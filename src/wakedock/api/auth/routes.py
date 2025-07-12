"""Authentication routes for WakeDock API."""

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
        print(f"[DEBUG] Raw body bytes: {body}")
        print(f"[DEBUG] Headers: {dict(request.headers)}")
        print(f"[DEBUG] Method: {request.method}")
        print(f"[DEBUG] URL: {request.url}")
        
        import json
        data = json.loads(body.decode('utf-8'))
        print(f"[DEBUG] Raw JSON received: {data}")
        print(f"[DEBUG] Keys in data: {list(data.keys())}")
        print(f"[DEBUG] Data types: {[(k, type(v)) for k, v in data.items()]}")
        
        # Test parsing with UserLogin model
        try:
            from .models import UserLogin
            parsed = UserLogin(**data)
            print(f"[DEBUG] UserLogin parsing SUCCESS: {parsed}")
            print(f"[DEBUG] UserLogin dict: {parsed.dict()}")
        except Exception as parse_error:
            print(f"[DEBUG] UserLogin parsing FAILED: {parse_error}")
            
        return {"debug": "ok", "received": data}
    except Exception as e:
        print(f"[DEBUG] Error parsing body: {e}")
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
        print(f"[LOGIN_DEBUG] Raw data received: {raw_data}")
        print(f"[LOGIN_DEBUG] Keys in data: {list(raw_data.keys())}")
        
        # Extract username/email and password from various possible formats
        username = None
        password = raw_data.get('password')
        
        # Try different field names for username
        if 'usernameOrEmail' in raw_data:
            username = raw_data['usernameOrEmail']
            print(f"[LOGIN_DEBUG] Found usernameOrEmail: {username}")
        elif 'username' in raw_data:
            username = raw_data['username']
            print(f"[LOGIN_DEBUG] Found username: {username}")
        elif 'email' in raw_data:
            username = raw_data['email']
            print(f"[LOGIN_DEBUG] Found email: {username}")
        
        if not username or not password:
            print(f"[LOGIN_DEBUG] Missing credentials - username: {bool(username)}, password: {bool(password)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Username/email and password are required"
            )
        
        print(f"[LOGIN_DEBUG] Processing login for user: {username}")
        
    except json.JSONDecodeError as e:
        print(f"[LOGIN_DEBUG] JSON decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid JSON format"
        )
    except Exception as e:
        print(f"[LOGIN_DEBUG] Error parsing request: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Request parsing error: {str(e)}"
        )
    
    print(f"[LOGIN_DEBUG] Received login request with username: {username}")
    print(f"[LOGIN_DEBUG] Raw headers: {dict(request.headers)}")
    print(f"[LOGIN_DEBUG] Content-Type: {request.headers.get('content-type')}")
    print(f"[LOGIN_DEBUG] User-Agent: {request.headers.get('user-agent')}")
    print(f"[LOGIN_DEBUG] Origin: {request.headers.get('origin')}")
    
    # Find user by username or email
    user = db.query(User).filter(
        (User.username == username) | 
        (User.email == username)
    ).first()
    
    if not user or not verify_password(password, user.hashed_password):
        print(f"[LOGIN_DEBUG] Auth failed - user found: {bool(user)}")
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
        print(f"[LOGIN_DEBUG] Failed to update last_login: {e}")
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
        
        print(f"[RAW_DEBUG] === REQUÊTE {method} VERS /login_raw_debug ===")
        print(f"[RAW_DEBUG] Headers: {headers}")
        print(f"[RAW_DEBUG] Body raw: {body}")
        
        if body:
            try:
                import json
                parsed_body = json.loads(body.decode('utf-8'))
                print(f"[RAW_DEBUG] Body parsed: {parsed_body}")
                print(f"[RAW_DEBUG] Keys in body: {list(parsed_body.keys())}")
            except Exception as parse_error:
                print(f"[RAW_DEBUG] Impossible de parser le body JSON: {parse_error}")
        
        return {
            "debug": "raw_intercepted",
            "method": method,
            "body_length": len(body) if body else 0,
            "headers": headers
        }
    except Exception as e:
        print(f"[RAW_DEBUG] Erreur dans le debug: {e}")
        return {"debug": "error", "message": str(e)}
