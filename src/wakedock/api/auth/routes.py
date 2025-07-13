"""Authentication routes for WakeDock API."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from wakedock.database.database import get_db_session, get_async_db_session
from wakedock.database.models import User, UserRole
from .models import (
    UserCreate, UserUpdate, UserResponse, UserLogin, UserLoginRequest,
    Token, PasswordChange, PasswordReset, PasswordResetConfirm
)
from .password import hash_password, verify_password
from .jwt import create_access_token, jwt_manager
from .dependencies import (
    get_current_user, get_current_active_user, 
    require_admin, require_role
)
from wakedock.security.jwt_rotation import get_jwt_rotation_service, get_jwt_rotation_manager
from wakedock.security.session_timeout import get_session_timeout_service
from wakedock.security.ids_middleware import get_security_dashboard

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db_session)
):
    """Register a new user."""
    # Check if username already exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = hash_password(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role,
        is_active=user_data.is_active
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.post("/login_debug")
async def login_user_debug(
    request: Request,
    db: Session = Depends(get_db_session)
):
    """DEBUG endpoint to see raw request."""
    try:
        body = await request.body()
        logger.debug(f"Raw body bytes: {body}")
        logger.debug(f"Headers: {dict(request.headers)}")
        logger.debug(f"Method: {request.method}")
        logger.debug(f"URL: {request.url}")
        
        import json
        data = json.loads(body.decode('utf-8'))
        logger.debug(f"Raw JSON received: {data}")
        logger.debug(f"Keys in data: {list(data.keys())}")
        logger.debug(f"Data types: {[(k, type(v)) for k, v in data.items()]}")
        
        # Test parsing with UserLogin model
        try:
            from .models import UserLogin
            parsed = UserLogin(**data)
            logger.debug(f"UserLogin parsing SUCCESS: {parsed}")
            logger.debug(f"UserLogin dict: {parsed.dict()}")
        except Exception as parse_error:
            logger.debug(f"UserLogin parsing FAILED: {parse_error}")
            
        return {"debug": "ok", "received": data}
    except Exception as e:
        logger.debug(f"Error parsing body: {e}")
        return {"debug": "error", "message": str(e)}


@router.post("/login", response_model=Token)
async def login_user(
    request: Request,
    db: Session = Depends(get_db_session)
):
    """Authenticate user and return access token."""
    try:
        # Parse raw body manually to handle any format
        body = await request.body()
        import json
        raw_data = json.loads(body.decode('utf-8'))
        logger.debug(f"Raw data received: {raw_data}")
        logger.debug(f"Keys in data: {list(raw_data.keys())}")
        
        # Extract username/email and password from various possible formats
        username = None
        password = raw_data.get('password')
        
        # Try different field names for username
        if 'usernameOrEmail' in raw_data:
            username = raw_data['usernameOrEmail']
            logger.debug(f"Found usernameOrEmail: {username}")
        elif 'username' in raw_data:
            username = raw_data['username']
            logger.debug(f"Found username: {username}")
        elif 'email' in raw_data:
            username = raw_data['email']
            logger.debug(f"Found email: {username}")
        
        if not username or not password:
            logger.debug(f"Missing credentials - username: {bool(username)}, password: {bool(password)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Username/email and password are required"
            )
        
        logger.debug(f"Processing login for user: {username}")
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid JSON format"
        )
    except Exception as e:
        logger.error(f"Error parsing request: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Request parsing error: {str(e)}"
        )
    
    logger.debug(f"Received login request with username: {username}")
    logger.debug(f"Raw headers: {dict(request.headers)}")
    logger.debug(f"Content-Type: {request.headers.get('content-type')}")
    logger.debug(f"User-Agent: {request.headers.get('user-agent')}")
    logger.debug(f"Origin: {request.headers.get('origin')}")
    
    # Find user by username or email
    user = db.query(User).filter(
        (User.username == username) | 
        (User.email == username)
    ).first()
    
    if not user or not verify_password(password, user.hashed_password):
        logger.debug(f"Auth failed - user found: {bool(user)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Store user data before any modifications
    user_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "last_login": user.last_login
    }
    
    # Update last login in a new transaction
    try:
        db.query(User).filter(User.id == user.id).update({
            'last_login': datetime.utcnow()
        })
        db.commit()
        user_data["last_login"] = datetime.utcnow()
    except Exception as e:
        logger.error(f"Failed to update last_login: {e}")
        db.rollback()
    
    # Create access token using stored data to avoid ObjectDeletedError
    access_token = create_access_token(
        user_id=user_data["id"],
        username=user_data["username"],
        role=user_data["role"]
    )
    
    # Return user data as dict instead of SQLAlchemy object to avoid ObjectDeletedError
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": int(jwt_manager.access_token_expires.total_seconds()),
        "user": user_data
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    request: Request,
    db: AsyncSession = Depends(get_async_db_session)
):
    """Refresh access token using refresh token with automatic rotation."""
    
    # Obtenir le service de rotation JWT
    jwt_rotation_service = get_jwt_rotation_service()
    
    # Vérifier si le token doit être tourné
    if jwt_rotation_service.should_rotate_token(refresh_token):
        # Effectuer la rotation
        new_tokens = await jwt_rotation_service.rotate_tokens(refresh_token, db)
        
        if not new_tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token or rotation failed"
            )
        
        # Créer la session timeout
        session_timeout_service = get_session_timeout_service()
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "")
        
        # Décoder le token pour obtenir l'ID utilisateur
        payload = jwt_rotation_service.decode_token(new_tokens.access_token)
        if payload and payload.get("user_id"):
            await session_timeout_service.create_session(
                user_id=payload["user_id"],
                session_id=new_tokens.access_token,
                ip_address=ip_address,
                user_agent=user_agent
            )
        
        return {
            "access_token": new_tokens.access_token,
            "refresh_token": new_tokens.refresh_token,
            "token_type": "bearer",
            "expires_in": int((new_tokens.access_expires_at - datetime.now()).total_seconds()),
            "rotated": True
        }
    
    else:
        # Utiliser le système de refresh existant
        new_token = jwt_manager.refresh_access_token(refresh_token)
        if not new_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        return {
            "access_token": new_token,
            "token_type": "bearer",
            "expires_in": int(jwt_manager.access_token_expires.total_seconds()),
            "rotated": False
        }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information."""
    return current_user


@router.put("/me", response_model=UserResponse)
def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Update current user information."""
    # Users can only update their own basic info (not role)
    if user_update.username is not None:
        # Check if new username is already taken
        existing_user = db.query(User).filter(
            User.username == user_update.username,
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        current_user.username = user_update.username
    
    if user_update.email is not None:
        # Check if new email is already taken
        existing_user = db.query(User).filter(
            User.email == user_update.email,
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already taken"
            )
        current_user.email = user_update.email
        current_user.is_verified = False  # Re-verify email
    
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    
    if user_update.password is not None:
        current_user.hashed_password = hash_password(user_update.password)
    
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.post("/change-password")
def change_password(
    password_change: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Change user password."""
    # Verify current password
    if not verify_password(password_change.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Update password
    current_user.hashed_password = hash_password(password_change.new_password)
    current_user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Password changed successfully"}


@router.get("/users", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db_session)
):
    """List all users (admin only)."""
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db_session)
):
    """Get user by ID (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db_session)
):
    """Update user (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update user fields
    for field, value in user_update.dict(exclude_unset=True).items():
        if field == "password" and value:
            setattr(user, "hashed_password", hash_password(value))
        elif hasattr(user, field):
            setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    return user


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db_session)
):
    """Delete user (admin only)."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}


@router.post("/logout")
async def logout_user(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db_session)
):
    """Logout user and revoke all tokens."""
    
    # Obtenir le token depuis l'en-tête Authorization
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        access_token = auth_header.replace("Bearer ", "")
        
        # Révoquer le token
        jwt_rotation_service = get_jwt_rotation_service()
        jwt_rotation_service.revoke_token(access_token)
        
        # Terminer toutes les sessions utilisateur
        session_timeout_service = get_session_timeout_service()
        terminated_sessions = await session_timeout_service.terminate_all_user_sessions(current_user.id)
        
        return {
            "message": "Déconnexion réussie",
            "sessions_terminated": terminated_sessions
        }
    
    return {"message": "Déconnexion réussie"}


@router.post("/revoke-all-tokens")
async def revoke_all_user_tokens(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db_session)
):
    """Revoke all tokens for the current user."""
    
    # Révoquer tous les tokens utilisateur
    jwt_rotation_service = get_jwt_rotation_service()
    jwt_rotation_service.revoke_all_user_tokens(current_user.id)
    
    # Terminer toutes les sessions utilisateur
    session_timeout_service = get_session_timeout_service()
    terminated_sessions = await session_timeout_service.terminate_all_user_sessions(current_user.id)
    
    return {
        "message": "Tous les tokens ont été révoqués",
        "sessions_terminated": terminated_sessions
    }


@router.get("/security/events")
async def get_security_events(
    limit: int = 100,
    threat_level: Optional[str] = None,
    attack_type: Optional[str] = None,
    ip_address: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get security events (admin only)."""
    
    # Vérifier les permissions admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès administrateur requis"
        )
    
    security_dashboard = get_security_dashboard()
    return security_dashboard.get_security_events(
        limit=limit,
        threat_level=threat_level,
        attack_type=attack_type,
        ip_address=ip_address
    )


@router.get("/security/statistics")
async def get_security_statistics(
    current_user: User = Depends(get_current_active_user)
):
    """Get security statistics (admin only)."""
    
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès administrateur requis"
        )
    
    security_dashboard = get_security_dashboard()
    return security_dashboard.get_security_statistics()


@router.get("/security/ip/{ip_address}")
async def get_ip_profile(
    ip_address: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get IP profile (admin only)."""
    
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès administrateur requis"
        )
    
    security_dashboard = get_security_dashboard()
    profile = security_dashboard.get_ip_profile(ip_address)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil IP non trouvé"
        )
    
    return profile


@router.post("/security/ip/{ip_address}/block")
async def block_ip_address(
    ip_address: str,
    current_user: User = Depends(get_current_active_user)
):
    """Block an IP address (admin only)."""
    
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès administrateur requis"
        )
    
    security_dashboard = get_security_dashboard()
    return security_dashboard.block_ip(ip_address)


@router.post("/security/ip/{ip_address}/unblock")
async def unblock_ip_address(
    ip_address: str,
    current_user: User = Depends(get_current_active_user)
):
    """Unblock an IP address (admin only)."""
    
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès administrateur requis"
        )
    
    security_dashboard = get_security_dashboard()
    return security_dashboard.unblock_ip(ip_address)


@router.post("/security/ip/{ip_address}/whitelist")
async def whitelist_ip_address(
    ip_address: str,
    current_user: User = Depends(get_current_active_user)
):
    """Whitelist an IP address (admin only)."""
    
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès administrateur requis"
        )
    
    security_dashboard = get_security_dashboard()
    return security_dashboard.whitelist_ip(ip_address)


@router.get("/security/threats")
async def get_top_threats(
    limit: int = 10,
    current_user: User = Depends(get_current_active_user)
):
    """Get top security threats (admin only)."""
    
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès administrateur requis"
        )
    
    security_dashboard = get_security_dashboard()
    return security_dashboard.get_top_threats(limit)


@router.get("/jwt/rotation/stats")
async def get_jwt_rotation_stats(
    current_user: User = Depends(get_current_active_user)
):
    """Get JWT rotation statistics (admin only)."""
    
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès administrateur requis"
        )
    
    jwt_rotation_service = get_jwt_rotation_service()
    return jwt_rotation_service.get_rotation_stats()


@router.get("/session/stats")
async def get_session_stats(
    current_user: User = Depends(get_current_active_user)
):
    """Get session statistics (admin only)."""
    
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès administrateur requis"
        )
    
    session_timeout_service = get_session_timeout_service()
    return session_timeout_service.get_session_stats()


@router.post("/session/extend")
async def extend_current_session(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Extend current user session."""
    
    # Obtenir le token depuis l'en-tête Authorization
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        access_token = auth_header.replace("Bearer ", "")
        
        # Étendre la session
        session_timeout_service = get_session_timeout_service()
        extended = await session_timeout_service.extend_session(access_token)
        
        if extended:
            return {"message": "Session étendue avec succès"}
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session invalide ou expirée"
            )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token d'authentification requis"
    )


@router.post("/reset-password")
def request_password_reset(
    password_reset: PasswordReset,
    db: Session = Depends(get_db_session)
):
    """Request password reset for email."""
    # Find user by email
    user = db.query(User).filter(User.email == password_reset.email).first()
    
    if not user:
        # Don't reveal whether email exists or not for security
        return {"message": "If the email exists in our system, you will receive a password reset link."}
    
    if not user.is_active:
        return {"message": "If the email exists in our system, you will receive a password reset link."}
    
    # Generate password reset token (in production, use secure random token and store in DB)
    import secrets
    import time
    reset_token = secrets.token_urlsafe(32)
    
    # In a real implementation, you would:
    # 1. Store the token in database with expiration time
    # 2. Send email with reset link
    # For now, we'll just log it
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Password reset requested for {password_reset.email}. Token: {reset_token}")
    
    # In development, return the token for testing
    return {
        "message": "If the email exists in our system, you will receive a password reset link.",
        "debug_token": reset_token  # Remove this in production
    }


@router.post("/reset-password-confirm")
def confirm_password_reset(
    reset_confirm: PasswordResetConfirm,
    db: Session = Depends(get_db_session)
):
    """Confirm password reset with token."""
    # In a real implementation, you would:
    # 1. Validate the token from database
    # 2. Check if token is expired
    # 3. Find user associated with token
    
    # For now, we'll implement a basic version
    # This is a simplified implementation for demonstration
    
    # You would typically decode/validate the token here
    # For demo purposes, we'll just check if it's a valid format
    if len(reset_confirm.token) < 16:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # In production, you would find the user by the token
    # For demo, we'll assume it's for the admin user
    user = db.query(User).filter(User.email == "admin@wakedock.com").first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Update password
    user.hashed_password = hash_password(reset_confirm.new_password)
    user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Password reset successfully"}


@router.api_route("/login_raw_debug", methods=["POST", "GET", "PUT", "PATCH", "DELETE"])
async def login_raw_debug(request: Request):
    """Endpoint de debug pour capturer toutes les requêtes vers login."""
    try:
        method = request.method
        headers = dict(request.headers)
        body = await request.body()
        
        logger.debug(f"=== REQUÊTE {method} VERS /login_raw_debug ===")
        logger.debug(f"Headers: {headers}")
        logger.debug(f"Body raw: {body}")
        
        if body:
            try:
                import json
                parsed_body = json.loads(body.decode('utf-8'))
                logger.debug(f"Body parsed: {parsed_body}")
                logger.debug(f"Keys in body: {list(parsed_body.keys())}")
            except Exception as parse_error:
                logger.debug(f"Impossible de parser le body JSON: {parse_error}")
        
        return {
            "debug": "raw_intercepted",
            "method": method,
            "body_length": len(body) if body else 0,
            "headers": headers
        }
    except Exception as e:
        logger.error(f"Erreur dans le debug: {e}")
        return {"debug": "error", "message": str(e)}


# === ENHANCED USER MANAGEMENT DASHBOARD ===

@router.get("/users/stats")
async def get_user_management_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db_session)
):
    """Get comprehensive user management statistics (admin only)"""
    try:
        # Total users count
        total_users = db.query(User).count()
        
        # Active users count
        active_users = db.query(User).filter(User.is_active == True).count()
        
        # Users by role
        admin_count = db.query(User).filter(User.role == UserRole.ADMIN).count()
        user_count = db.query(User).filter(User.role == UserRole.USER).count()
        viewer_count = db.query(User).filter(User.role == UserRole.VIEWER).count()
        
        # Recent registrations (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_registrations = db.query(User).filter(
            User.created_at >= seven_days_ago
        ).count()
        
        # Recent logins (last 24 hours)
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        recent_logins = db.query(User).filter(
            User.last_login >= one_day_ago
        ).count()
        
        # Verified users
        verified_users = db.query(User).filter(User.is_verified == True).count()
        
        # Inactive users (never logged in or not logged in for 30+ days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        inactive_users = db.query(User).filter(
            (User.last_login == None) | (User.last_login < thirty_days_ago)
        ).count()
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "verified_users": verified_users,
            "users_by_role": {
                "admin": admin_count,
                "user": user_count,
                "viewer": viewer_count
            },
            "recent_activity": {
                "registrations_last_7_days": recent_registrations,
                "logins_last_24_hours": recent_logins
            },
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user stats: {str(e)}"
        )


@router.get("/users/recent-activity")
async def get_recent_user_activity(
    limit: int = 20,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db_session)
):
    """Get recent user activity for admin dashboard"""
    try:
        # Recent registrations
        recent_users = db.query(User).order_by(
            User.created_at.desc()
        ).limit(limit).all()
        
        activity_data = []
        for user in recent_users:
            activity_data.append({
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "created_at": user.created_at,
                "last_login": user.last_login,
                "activity_type": "registration"
            })
        
        return {
            "recent_activity": activity_data,
            "total_items": len(activity_data),
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent activity: {str(e)}"
        )


@router.post("/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db_session)
):
    """Toggle user active/inactive status (admin only)"""
    try:
        # Prevent admin from deactivating themselves
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change your own status"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Toggle status
        user.is_active = not user.is_active
        user.updated_at = datetime.utcnow()
        db.commit()
        
        action = "activated" if user.is_active else "deactivated"
        
        return {
            "success": True,
            "message": f"User {user.username} {action} successfully",
            "user_id": user_id,
            "new_status": user.is_active,
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle user status: {str(e)}"
        )


@router.post("/users/{user_id}/change-role")
async def change_user_role(
    user_id: int,
    new_role: UserRole,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db_session)
):
    """Change user role (admin only)"""
    try:
        # Prevent admin from changing their own role
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change your own role"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        old_role = user.role
        user.role = new_role
        user.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "success": True,
            "message": f"User {user.username} role changed from {old_role.value} to {new_role.value}",
            "user_id": user_id,
            "old_role": old_role.value,
            "new_role": new_role.value,
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change user role: {str(e)}"
        )


@router.get("/users/search")
async def search_users(
    q: str = "",
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    is_verified: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db_session)
):
    """Search and filter users (admin only)"""
    try:
        query = db.query(User)
        
        # Text search in username, email, or full_name
        if q:
            search_term = f"%{q}%"
            query = query.filter(
                (User.username.ilike(search_term)) |
                (User.email.ilike(search_term)) |
                (User.full_name.ilike(search_term))
            )
        
        # Filter by role
        if role:
            query = query.filter(User.role == role)
        
        # Filter by active status
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        # Filter by verified status
        if is_verified is not None:
            query = query.filter(User.is_verified == is_verified)
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination
        users = query.offset(offset).limit(limit).all()
        
        # Convert to response format
        user_data = []
        for user in users:
            user_data.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "last_login": user.last_login
            })
        
        return {
            "users": user_data,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "filters": {
                "search_query": q,
                "role": role.value if role else None,
                "is_active": is_active,
                "is_verified": is_verified
            },
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search users: {str(e)}"
        )


@router.post("/users/bulk-actions")
async def bulk_user_actions(
    user_ids: List[int],
    action: str,  # "activate", "deactivate", "delete"
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db_session)
):
    """Perform bulk actions on multiple users (admin only)"""
    try:
        # Prevent admin from affecting themselves
        if current_user.id in user_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot perform bulk actions on your own account"
            )
        
        users = db.query(User).filter(User.id.in_(user_ids)).all()
        
        if not users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No users found with provided IDs"
            )
        
        results = []
        
        for user in users:
            try:
                if action == "activate":
                    user.is_active = True
                    user.updated_at = datetime.utcnow()
                    results.append({"user_id": user.id, "username": user.username, "action": "activated", "success": True})
                    
                elif action == "deactivate":
                    user.is_active = False
                    user.updated_at = datetime.utcnow()
                    results.append({"user_id": user.id, "username": user.username, "action": "deactivated", "success": True})
                    
                elif action == "delete":
                    db.delete(user)
                    results.append({"user_id": user.id, "username": user.username, "action": "deleted", "success": True})
                    
                else:
                    results.append({"user_id": user.id, "username": user.username, "action": action, "success": False, "error": "Invalid action"})
                    
            except Exception as e:
                results.append({"user_id": user.id, "username": user.username, "action": action, "success": False, "error": str(e)})
        
        db.commit()
        
        successful_actions = len([r for r in results if r["success"]])
        
        return {
            "success": True,
            "message": f"Bulk action '{action}' completed on {successful_actions}/{len(user_ids)} users",
            "results": results,
            "total_processed": len(user_ids),
            "successful": successful_actions,
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk action: {str(e)}"
        )
