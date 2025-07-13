"""
Tenant Middleware

Middleware for handling multi-tenant requests including:
- Tenant identification and validation
- Request scoping to organization
- Quota enforcement
- Access control
"""

import logging
from typing import Optional, Callable, Any
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from wakedock.tenancy.service import get_tenancy_service
from wakedock.database.models.organization import Organization, OrganizationRole
from wakedock.api.auth.dependencies import get_current_user

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware for multi-tenant request handling"""
    
    def __init__(self, app, exempt_paths: Optional[list] = None):
        super().__init__(app)
        self.exempt_paths = exempt_paths or [
            "/api/v1/health",
            "/api/v1/auth",
            "/api/config",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
        self.tenancy_service = get_tenancy_service()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with tenant context"""
        
        # Skip tenant processing for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)
        
        # Skip if no tenancy service available
        if not self.tenancy_service:
            return await call_next(request)
        
        try:
            # Extract tenant context
            tenant_context = await self._extract_tenant_context(request)
            
            if tenant_context:
                # Add tenant info to request state
                request.state.organization = tenant_context["organization"]
                request.state.user_role = tenant_context["role"]
                request.state.permissions = tenant_context["permissions"]
                
                # Check quota limits for write operations
                if request.method in ["POST", "PUT", "PATCH"]:
                    await self._check_quota_limits(request, tenant_context["organization"])
            
            # Process request
            response = await call_next(request)
            
            # Add tenant headers to response
            if tenant_context:
                response.headers["X-Organization-ID"] = str(tenant_context["organization"].id)
                response.headers["X-Organization-Slug"] = tenant_context["organization"].slug
                response.headers["X-User-Role"] = tenant_context["role"].value
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Tenant middleware error: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal tenant processing error"}
            )
    
    async def _extract_tenant_context(self, request: Request) -> Optional[dict]:
        """Extract tenant context from request"""
        
        # Get current user from request headers/tokens
        # This is a simplified version - in practice you'd extract from JWT token
        # For now, skip user authentication in middleware
        try:
            # Skip tenant extraction if no user context
            return None
        except Exception:
            return None
        
        # Check for organization context in different ways
        organization = None
        org_slug = None
        org_id = None
        
        # Method 1: X-Organization header
        org_header = request.headers.get("X-Organization")
        if org_header:
            if org_header.isdigit():
                org_id = int(org_header)
            else:
                org_slug = org_header
        
        # Method 2: Query parameter
        if not org_header:
            org_slug = request.query_params.get("org")
            if not org_slug:
                org_id_param = request.query_params.get("org_id")
                if org_id_param and org_id_param.isdigit():
                    org_id = int(org_id_param)
        
        # Method 3: Path parameter (for organization-specific endpoints)
        if not org_header and not org_slug and not org_id:
            path_parts = request.url.path.strip("/").split("/")
            if len(path_parts) >= 4 and path_parts[2] == "organizations":
                org_identifier = path_parts[3]
                if org_identifier.isdigit():
                    org_id = int(org_identifier)
                else:
                    org_slug = org_identifier
        
        # Get organization
        if org_id:
            organization = await self.tenancy_service.get_organization(org_id)
        elif org_slug:
            organization = await self.tenancy_service.get_organization_by_slug(org_slug)
        else:
            # Default to user's first organization
            user_orgs = await self.tenancy_service.get_user_organizations(user.id)
            if user_orgs:
                organization = user_orgs[0]
        
        if not organization:
            return None
        
        # Get user's role in organization
        user_role = await self.tenancy_service.get_user_role_in_organization(
            user.id, organization.id
        )
        
        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have access to this organization"
            )
        
        # Get permissions based on role
        permissions = self._get_role_permissions(user_role)
        
        return {
            "organization": organization,
            "role": user_role,
            "permissions": permissions,
            "user": user
        }
    
    def _get_role_permissions(self, role: OrganizationRole) -> dict:
        """Get permissions based on user role"""
        base_permissions = {
            "containers": {"read": False, "write": False, "delete": False},
            "users": {"read": False, "write": False, "delete": False},
            "settings": {"read": False, "write": False},
            "billing": {"read": False, "write": False},
            "analytics": {"read": False},
            "backups": {"read": False, "write": False}
        }
        
        if role == OrganizationRole.OWNER:
            # Owners have all permissions
            for resource in base_permissions:
                for action in base_permissions[resource]:
                    base_permissions[resource][action] = True
        
        elif role == OrganizationRole.ADMIN:
            # Admins have most permissions except billing
            base_permissions.update({
                "containers": {"read": True, "write": True, "delete": True},
                "users": {"read": True, "write": True, "delete": True},
                "settings": {"read": True, "write": True},
                "billing": {"read": True, "write": False},
                "analytics": {"read": True},
                "backups": {"read": True, "write": True}
            })
        
        elif role == OrganizationRole.MEMBER:
            # Members can manage containers and read analytics
            base_permissions.update({
                "containers": {"read": True, "write": True, "delete": False},
                "users": {"read": True, "write": False, "delete": False},
                "settings": {"read": False, "write": False},
                "billing": {"read": False, "write": False},
                "analytics": {"read": True},
                "backups": {"read": True, "write": False}
            })
        
        elif role == OrganizationRole.VIEWER:
            # Viewers can only read
            base_permissions.update({
                "containers": {"read": True, "write": False, "delete": False},
                "users": {"read": True, "write": False, "delete": False},
                "settings": {"read": False, "write": False},
                "billing": {"read": False, "write": False},
                "analytics": {"read": True},
                "backups": {"read": True, "write": False}
            })
        
        return base_permissions
    
    async def _check_quota_limits(self, request: Request, organization: Organization):
        """Check if request would exceed quota limits"""
        
        # Skip quota checks for certain operations
        if request.url.path.endswith("/stop") or request.url.path.endswith("/delete"):
            return
        
        # Check container creation quota
        if "/services" in request.url.path and request.method == "POST":
            exceeded, message = await self.tenancy_service.check_quota_exceeded(
                organization.id, "containers", 1
            )
            if exceeded:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Container quota exceeded: {message}"
                )
        
        # Check backup creation quota
        if "/backup" in request.url.path and request.method == "POST":
            exceeded, message = await self.tenancy_service.check_quota_exceeded(
                organization.id, "backups", 1
            )
            if exceeded:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Backup quota exceeded: {message}"
                )
        
        # Check feature access
        feature_map = {
            "/analytics": "analytics",
            "/backup": "backups",
            "/audit": "audit_logs"
        }
        
        for path, feature in feature_map.items():
            if path in request.url.path and not organization.has_feature(feature):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Feature '{feature}' not available in current subscription tier"
                )


def get_current_organization(request: Request) -> Optional[Organization]:
    """Get current organization from request state"""
    return getattr(request.state, "organization", None)


def get_current_user_role(request: Request) -> Optional[OrganizationRole]:
    """Get current user's role in organization from request state"""
    return getattr(request.state, "user_role", None)


def get_current_permissions(request: Request) -> dict:
    """Get current user's permissions from request state"""
    return getattr(request.state, "permissions", {})


def require_permission(resource: str, action: str):
    """Decorator to require specific permission"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Find request in args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request not found for permission check"
                )
            
            permissions = get_current_permissions(request)
            if not permissions.get(resource, {}).get(action, False):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions: {resource}.{action} required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_organization(func):
    """Decorator to require organization context"""
    async def wrapper(*args, **kwargs):
        # Find request in args/kwargs
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        if not request:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Request not found for organization check"
            )
        
        organization = get_current_organization(request)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization context required"
            )
        
        return await func(*args, **kwargs)
    return wrapper