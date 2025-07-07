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
    UserCreate, UserUpdate, UserResponse, UserLogin, 
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


@router.post("/login", response_model=Token)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db_session)
):
    """Authenticate user and return access token."""
    # Find user by username or email
    user = db.query(User).filter(
        (User.username == form_data.username) | 
        (User.email == form_data.username)
    ).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
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
    
    # Update last login - use merge to handle detached objects
    user.last_login = datetime.utcnow()
    user = db.merge(user)
    db.commit()
    
    # Create access token
    access_token = create_access_token(
        user_id=user.id,
        username=user.username,
        role=user.role
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": int(jwt_manager.access_token_expires.total_seconds()),
        "user": user
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
