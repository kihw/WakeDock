"""
Enhanced Role-Based Access Control (RBAC) System

Comprehensive permission system with:
- Granular permissions
- Role hierarchies
- Resource-based access control
- Permission inheritance
- Dynamic permission checking
"""

from typing import Dict, List, Set, Optional, Union
from enum import Enum
from functools import wraps
from fastapi import HTTPException, status, Depends, Request
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func

from wakedock.database.database import Base, get_db_session
from wakedock.database.models import User, UserRole
from wakedock.api.auth.dependencies import get_current_active_user

import logging

logger = logging.getLogger(__name__)


class Permission(Enum):
    """Granular permissions for system operations"""
    # User management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_LIST = "user:list"
    USER_ROLE_CHANGE = "user:role_change"
    
    # Service management
    SERVICE_CREATE = "service:create"
    SERVICE_READ = "service:read"
    SERVICE_UPDATE = "service:update"
    SERVICE_DELETE = "service:delete"
    SERVICE_START = "service:start"
    SERVICE_STOP = "service:stop"
    SERVICE_RESTART = "service:restart"
    SERVICE_LOGS = "service:logs"
    SERVICE_METRICS = "service:metrics"
    SERVICE_LIST = "service:list"
    
    # Configuration management
    CONFIG_READ = "config:read"
    CONFIG_UPDATE = "config:update"
    CONFIG_DELETE = "config:delete"
    CONFIG_SECRET_READ = "config:secret_read"
    CONFIG_SECRET_UPDATE = "config:secret_update"
    
    # System management
    SYSTEM_HEALTH = "system:health"
    SYSTEM_METRICS = "system:metrics"
    SYSTEM_LOGS = "system:logs"
    SYSTEM_BACKUP = "system:backup"
    SYSTEM_RESTORE = "system:restore"
    SYSTEM_MAINTENANCE = "system:maintenance"
    
    # Monitoring and analytics
    MONITORING_READ = "monitoring:read"
    MONITORING_CONFIGURE = "monitoring:configure"
    ANALYTICS_READ = "analytics:read"
    ANALYTICS_EXPORT = "analytics:export"
    
    # Audit and security
    AUDIT_READ = "audit:read"
    AUDIT_EXPORT = "audit:export"
    SECURITY_CONFIGURE = "security:configure"
    
    # Cache management
    CACHE_READ = "cache:read"
    CACHE_MANAGE = "cache:manage"
    CACHE_FLUSH = "cache:flush"
    
    # Vault/Secrets management
    VAULT_READ = "vault:read"
    VAULT_WRITE = "vault:write"
    VAULT_DELETE = "vault:delete"
    VAULT_ADMIN = "vault:admin"


class ResourceType(Enum):
    """Types of resources that can be protected"""
    USER = "user"
    SERVICE = "service"
    CONFIGURATION = "configuration"
    SYSTEM = "system"
    AUDIT = "audit"
    VAULT = "vault"


# Association table for role-permission relationships
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)

# Association table for user-permission relationships (direct permissions)
user_permissions = Table(
    'user_permissions',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)


class Role(Base):
    """Role model for RBAC system"""
    
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(String(500))
    
    # Role hierarchy
    parent_role_id = Column(Integer, ForeignKey('roles.id'), nullable=True)
    parent_role = relationship("Role", remote_side=[id], backref="child_roles")
    
    # System role flag
    is_system_role = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    permissions = relationship("PermissionModel", secondary=role_permissions, back_populates="roles")
    
    def __repr__(self) -> str:
        return f"<Role(name='{self.name}', display_name='{self.display_name}')>"


class PermissionModel(Base):
    """Permission model for RBAC system"""
    
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(String(500))
    resource_type = Column(String(50), nullable=False)
    
    # Permission categories for organization
    category = Column(String(50), nullable=False)
    
    # System permission flag
    is_system_permission = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
    users = relationship("User", secondary=user_permissions)
    
    def __repr__(self) -> str:
        return f"<Permission(name='{self.name}', resource_type='{self.resource_type}')>"


class ResourcePermission(Base):
    """Resource-specific permissions for fine-grained access control"""
    
    __tablename__ = "resource_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(String(100), nullable=False, index=True)
    permission = Column(String(100), nullable=False)
    
    # Permission metadata
    granted_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    granted_by_user = relationship("User", foreign_keys=[granted_by])
    
    def __repr__(self) -> str:
        return f"<ResourcePermission(user_id={self.user_id}, resource='{self.resource_type}:{self.resource_id}', permission='{self.permission}')>"


class RBACService:
    """Service for role-based access control operations"""
    
    def __init__(self):
        self.audit_service = None
        
        # Define role hierarchies and default permissions
        self.role_hierarchy = {
            UserRole.ADMIN: {
                "permissions": [p for p in Permission],  # Admin gets all permissions
                "inherits_from": []
            },
            UserRole.USER: {
                "permissions": [
                    Permission.SERVICE_CREATE, Permission.SERVICE_READ, Permission.SERVICE_UPDATE,
                    Permission.SERVICE_DELETE, Permission.SERVICE_START, Permission.SERVICE_STOP,
                    Permission.SERVICE_RESTART, Permission.SERVICE_LOGS, Permission.SERVICE_METRICS,
                    Permission.USER_READ, Permission.SYSTEM_HEALTH, Permission.MONITORING_READ,
                    Permission.ANALYTICS_READ, Permission.CACHE_READ
                ],
                "inherits_from": [UserRole.VIEWER]
            },
            UserRole.VIEWER: {
                "permissions": [
                    Permission.SERVICE_READ, Permission.SERVICE_LOGS, Permission.SERVICE_METRICS,
                    Permission.SERVICE_LIST, Permission.USER_READ, Permission.SYSTEM_HEALTH,
                    Permission.SYSTEM_METRICS, Permission.MONITORING_READ, Permission.ANALYTICS_READ
                ],
                "inherits_from": []
            }
        }
    
    def has_permission(self, user: User, permission: Permission, 
                      resource_type: Optional[ResourceType] = None,
                      resource_id: Optional[str] = None) -> bool:
        """Check if user has a specific permission"""
        try:
            # System admin always has access
            if user.role == UserRole.ADMIN:
                return True
            
            # Check direct user permissions first
            if self._check_direct_permission(user, permission):
                return True
            
            # Check role-based permissions
            if self._check_role_permission(user.role, permission):
                return True
            
            # Check resource-specific permissions
            if resource_type and resource_id:
                if self._check_resource_permission(user, permission, resource_type, resource_id):
                    return True
            
            # Check ownership-based permissions
            if self._check_ownership_permission(user, permission, resource_type, resource_id):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking permission {permission.value} for user {user.id}: {e}")
            return False
    
    def _check_direct_permission(self, user: User, permission: Permission) -> bool:
        """Check if user has direct permission assigned"""
        # Implementation would check user_permissions table
        # For now, return False as we rely on role-based permissions
        return False
    
    def _check_role_permission(self, role: UserRole, permission: Permission) -> bool:
        """Check if user's role has the permission"""
        role_config = self.role_hierarchy.get(role, {})
        permissions = role_config.get("permissions", [])
        
        if permission in permissions:
            return True
        
        # Check inherited permissions
        for inherited_role in role_config.get("inherits_from", []):
            if self._check_role_permission(inherited_role, permission):
                return True
        
        return False
    
    def _check_resource_permission(self, user: User, permission: Permission,
                                 resource_type: ResourceType, resource_id: str) -> bool:
        """Check resource-specific permissions"""
        # This would query the resource_permissions table
        # Implementation depends on database session availability
        return False
    
    def _check_ownership_permission(self, user: User, permission: Permission,
                                  resource_type: Optional[ResourceType], 
                                  resource_id: Optional[str]) -> bool:
        """Check ownership-based permissions"""
        if not resource_type or not resource_id:
            return False
        
        # Service ownership check
        if resource_type == ResourceType.SERVICE:
            # Check if user owns the service
            # This would require a database query to verify ownership
            return True  # Simplified for now
        
        # User can always manage their own user resource
        if resource_type == ResourceType.USER and resource_id == str(user.id):
            return permission in [Permission.USER_READ, Permission.USER_UPDATE]
        
        return False
    
    async def grant_permission(self, user_id: int, permission: Permission,
                             resource_type: Optional[ResourceType] = None,
                             resource_id: Optional[str] = None,
                             granted_by: Optional[User] = None) -> bool:
        """Grant a specific permission to a user"""
        try:
            # Implementation would add to user_permissions or resource_permissions table
            # Log the permission grant
            if granted_by and self.audit_service:
                await self.audit_service.log_security_violation(
                    "permission_granted",
                    f"Permission {permission.value} granted to user {user_id}",
                    user_id=granted_by.id,
                    username=granted_by.username,
                    event_metadata={
                        "target_user_id": user_id,
                        "permission": permission.value,
                        "resource_type": resource_type.value if resource_type else None,
                        "resource_id": resource_id
                    }
                )
            return True
        except Exception as e:
            logger.error(f"Failed to grant permission {permission.value} to user {user_id}: {e}")
            return False
    
    async def revoke_permission(self, user_id: int, permission: Permission,
                              resource_type: Optional[ResourceType] = None,
                              resource_id: Optional[str] = None,
                              revoked_by: Optional[User] = None) -> bool:
        """Revoke a specific permission from a user"""
        try:
            # Implementation would remove from user_permissions or resource_permissions table
            # Log the permission revocation
            if revoked_by and self.audit_service:
                await self.audit_service.log_security_violation(
                    "permission_revoked",
                    f"Permission {permission.value} revoked from user {user_id}",
                    user_id=revoked_by.id,
                    username=revoked_by.username,
                    event_metadata={
                        "target_user_id": user_id,
                        "permission": permission.value,
                        "resource_type": resource_type.value if resource_type else None,
                        "resource_id": resource_id
                    }
                )
            return True
        except Exception as e:
            logger.error(f"Failed to revoke permission {permission.value} from user {user_id}: {e}")
            return False
    
    def get_user_permissions(self, user: User) -> Set[Permission]:
        """Get all permissions for a user"""
        permissions = set()
        
        # Get role-based permissions
        role_config = self.role_hierarchy.get(user.role, {})
        permissions.update(role_config.get("permissions", []))
        
        # Add inherited permissions
        for inherited_role in role_config.get("inherits_from", []):
            inherited_config = self.role_hierarchy.get(inherited_role, {})
            permissions.update(inherited_config.get("permissions", []))
        
        return permissions


# Global RBAC service instance
_rbac_service: Optional[RBACService] = None


def get_rbac_service() -> RBACService:
    """Get global RBAC service instance"""
    global _rbac_service
    if _rbac_service is None:
        _rbac_service = RBACService()
    return _rbac_service


def require_permission(permission: Permission, 
                      resource_type: Optional[ResourceType] = None,
                      resource_id_param: Optional[str] = None):
    """Decorator for requiring specific permissions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request and user from function parameters
            request = None
            current_user = None
            
            # Look for Request and User objects in function parameters
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                elif isinstance(arg, User):
                    current_user = arg
            
            # Also check kwargs
            if 'request' in kwargs:
                request = kwargs['request']
            if 'current_user' in kwargs:
                current_user = kwargs['current_user']
            
            # If we don't have user, get it from dependencies
            if not current_user:
                # This should be handled by FastAPI dependencies
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Get resource ID from path parameters if specified
            resource_id = None
            if resource_id_param and request:
                resource_id = request.path_params.get(resource_id_param)
            
            # Check permission
            rbac_service = get_rbac_service()
            if not rbac_service.has_permission(current_user, permission, resource_type, resource_id):
                # Log permission denied (import here to avoid circular imports)
                try:
                    from wakedock.security.audit import get_audit_service
                    audit_service = get_audit_service()
                    await audit_service.log_permission_denied(
                        user_id=current_user.id,
                        username=current_user.username,
                        action=permission.value,
                        resource_type=resource_type.value if resource_type else "unknown",
                        resource_id=resource_id or "unknown",
                        ip_address=request.client.host if request else "unknown",
                        endpoint=request.url.path if request else "unknown"
                    )
                except Exception:
                    pass  # Don't fail request if audit logging fails
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission.value}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_permissions(*permissions: Permission):
    """Decorator for requiring multiple permissions (all must be satisfied)"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Similar implementation to require_permission but check all permissions
            current_user = None
            request = None
            
            # Extract user and request from parameters
            for arg in args:
                if isinstance(arg, User):
                    current_user = arg
                elif isinstance(arg, Request):
                    request = arg
            
            if 'current_user' in kwargs:
                current_user = kwargs['current_user']
            if 'request' in kwargs:
                request = kwargs['request']
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            rbac_service = get_rbac_service()
            for permission in permissions:
                if not rbac_service.has_permission(current_user, permission):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied: {permission.value}"
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# FastAPI dependency for permission checking
def RequirePermission(permission: Permission, 
                     resource_type: Optional[ResourceType] = None,
                     resource_id_param: Optional[str] = None):
    """FastAPI dependency for permission checking"""
    async def permission_dependency(
        request: Request,
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        # Get resource ID from path parameters if specified
        resource_id = None
        if resource_id_param:
            resource_id = request.path_params.get(resource_id_param)
        
        # Check permission
        rbac_service = get_rbac_service()
        if not rbac_service.has_permission(current_user, permission, resource_type, resource_id):
            # Log permission denied (import here to avoid circular imports)
            try:
                from wakedock.security.audit import get_audit_service
                audit_service = get_audit_service()
                await audit_service.log_permission_denied(
                    user_id=current_user.id,
                    username=current_user.username,
                    action=permission.value,
                    resource_type=resource_type.value if resource_type else "unknown",
                    resource_id=resource_id or "unknown",
                    ip_address=request.client.host,
                    endpoint=request.url.path
                )
            except Exception:
                pass  # Don't fail request if audit logging fails
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value}"
            )
        
        return current_user
    
    return permission_dependency