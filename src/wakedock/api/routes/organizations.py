"""
Organization Management API Routes

Provides REST endpoints for multi-tenant organization management:
- Organization CRUD operations
- User invitation and role management
- Quota and billing information
- Resource management
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from wakedock.tenancy import (
    get_tenancy_service, get_quota_manager
)
from wakedock.tenancy.middleware import (
    get_current_organization, get_current_user_role, 
    require_permission, require_organization
)
from wakedock.database.models.organization import (
    Organization, OrganizationRole, SubscriptionTier
)
from wakedock.api.auth.dependencies import get_current_user, require_role
from wakedock.database.models import UserRole
from pydantic import BaseModel, EmailStr

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for API requests/responses
class OrganizationCreate(BaseModel):
    name: str
    slug: str
    contact_email: EmailStr
    description: Optional[str] = None
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class UserInvitation(BaseModel):
    email: EmailStr
    role: OrganizationRole
    message: Optional[str] = None


class UserRoleUpdate(BaseModel):
    role: OrganizationRole


class InvitationAccept(BaseModel):
    token: str


@router.post("/", response_model=dict)
async def create_organization(
    org_data: OrganizationCreate,
    current_user = Depends(get_current_user),
    tenancy_service = Depends(get_tenancy_service)
):
    """Create a new organization"""
    if not tenancy_service:
        raise HTTPException(status_code=503, detail="Tenancy service not available")
    
    try:
        organization = await tenancy_service.create_organization(
            name=org_data.name,
            slug=org_data.slug,
            owner_user_id=current_user.id,
            contact_email=org_data.contact_email,
            subscription_tier=org_data.subscription_tier
        )
        
        return {
            "id": organization.id,
            "name": organization.name,
            "slug": organization.slug,
            "subscription_tier": organization.subscription_tier.value,
            "created_at": organization.created_at.isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create organization: {e}")
        raise HTTPException(status_code=500, detail="Failed to create organization")


@router.get("/", response_model=List[dict])
async def list_user_organizations(
    current_user = Depends(get_current_user),
    tenancy_service = Depends(get_tenancy_service)
):
    """List organizations the current user belongs to"""
    if not tenancy_service:
        raise HTTPException(status_code=503, detail="Tenancy service not available")
    
    try:
        organizations = await tenancy_service.get_user_organizations(current_user.id)
        
        result = []
        for org in organizations:
            user_role = await tenancy_service.get_user_role_in_organization(
                current_user.id, org.id
            )
            
            result.append({
                "id": org.id,
                "name": org.name,
                "slug": org.slug,
                "description": org.description,
                "subscription_tier": org.subscription_tier.value,
                "user_role": user_role.value if user_role else None,
                "quota_usage": org.get_quota_usage(),
                "created_at": org.created_at.isoformat()
            })
        
        return result
    
    except Exception as e:
        logger.error(f"Failed to list organizations: {e}")
        raise HTTPException(status_code=500, detail="Failed to list organizations")


@router.get("/{org_id}", response_model=dict)
@require_organization
async def get_organization(
    org_id: int,
    current_org = Depends(get_current_organization),
    current_role = Depends(get_current_user_role)
):
    """Get organization details"""
    
    return {
        "id": current_org.id,
        "name": current_org.name,
        "slug": current_org.slug,
        "description": current_org.description,
        "contact_email": current_org.contact_email,
        "contact_phone": current_org.contact_phone,
        "subscription_tier": current_org.subscription_tier.value,
        "user_role": current_role.value,
        "features_enabled": current_org.features_enabled,
        "quota_usage": current_org.get_quota_usage(),
        "resource_limits": {
            "max_containers": current_org.max_containers,
            "max_cpu_cores": float(current_org.max_cpu_cores),
            "max_memory_gb": float(current_org.max_memory_gb),
            "max_storage_gb": float(current_org.max_storage_gb),
            "max_users": current_org.max_users,
            "max_backups": current_org.max_backups
        },
        "current_usage": {
            "containers": current_org.current_containers,
            "cpu_cores": float(current_org.current_cpu_usage),
            "memory_gb": float(current_org.current_memory_usage),
            "storage_gb": float(current_org.current_storage_usage),
            "users": current_org.current_users,
            "backups": current_org.current_backups
        },
        "created_at": current_org.created_at.isoformat(),
        "updated_at": current_org.updated_at.isoformat()
    }


@router.put("/{org_id}", response_model=dict)
@require_organization
@require_permission("settings", "write")
async def update_organization(
    org_id: int,
    org_update: OrganizationUpdate,
    current_org = Depends(get_current_organization),
    tenancy_service = Depends(get_tenancy_service)
):
    """Update organization details"""
    if not tenancy_service:
        raise HTTPException(status_code=503, detail="Tenancy service not available")
    
    try:
        # Convert to dict and remove None values
        update_data = {k: v for k, v in org_update.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        updated_org = await tenancy_service.update_organization(org_id, update_data)
        
        return {
            "id": updated_org.id,
            "name": updated_org.name,
            "slug": updated_org.slug,
            "description": updated_org.description,
            "updated_at": updated_org.updated_at.isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update organization: {e}")
        raise HTTPException(status_code=500, detail="Failed to update organization")


@router.post("/{org_id}/invitations", response_model=dict)
@require_organization
@require_permission("users", "write")
async def invite_user(
    org_id: int,
    invitation: UserInvitation,
    current_user = Depends(get_current_user),
    tenancy_service = Depends(get_tenancy_service)
):
    """Invite user to organization"""
    if not tenancy_service:
        raise HTTPException(status_code=503, detail="Tenancy service not available")
    
    try:
        invitation_obj = await tenancy_service.invite_user_to_organization(
            org_id=org_id,
            email=invitation.email,
            role=invitation.role,
            invited_by_user_id=current_user.id,
            message=invitation.message
        )
        
        return {
            "invitation_id": invitation_obj.id,
            "email": invitation_obj.email,
            "role": invitation_obj.role.value,
            "token": invitation_obj.token,
            "expires_at": invitation_obj.expires_at.isoformat(),
            "created_at": invitation_obj.created_at.isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to invite user: {e}")
        raise HTTPException(status_code=500, detail="Failed to invite user")


@router.post("/invitations/accept", response_model=dict)
async def accept_invitation(
    invitation: InvitationAccept,
    current_user = Depends(get_current_user),
    tenancy_service = Depends(get_tenancy_service)
):
    """Accept organization invitation"""
    if not tenancy_service:
        raise HTTPException(status_code=503, detail="Tenancy service not available")
    
    try:
        org_user = await tenancy_service.accept_invitation(
            token=invitation.token,
            user_id=current_user.id
        )
        
        return {
            "organization_id": org_user.organization_id,
            "role": org_user.role.value,
            "joined_at": org_user.joined_at.isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to accept invitation: {e}")
        raise HTTPException(status_code=500, detail="Failed to accept invitation")


@router.get("/{org_id}/users", response_model=List[dict])
@require_organization
@require_permission("users", "read")
async def list_organization_users(
    org_id: int,
    current_org = Depends(get_current_organization)
):
    """List organization users"""
    users_data = []
    
    for org_user in current_org.users:
        if org_user.is_active:
            users_data.append({
                "user_id": org_user.user_id,
                "username": org_user.user.username if org_user.user else None,
                "email": org_user.user.email if org_user.user else None,
                "full_name": org_user.user.full_name if org_user.user else None,
                "role": org_user.role.value,
                "permissions": org_user.permissions,
                "joined_at": org_user.joined_at.isoformat(),
                "last_active_at": org_user.last_active_at.isoformat() if org_user.last_active_at else None
            })
    
    return users_data


@router.put("/{org_id}/users/{user_id}/role", response_model=dict)
@require_organization
@require_permission("users", "write")
async def update_user_role(
    org_id: int,
    user_id: int,
    role_update: UserRoleUpdate,
    tenancy_service = Depends(get_tenancy_service)
):
    """Update user role in organization"""
    if not tenancy_service:
        raise HTTPException(status_code=503, detail="Tenancy service not available")
    
    try:
        org_user = await tenancy_service.update_user_role(
            org_id=org_id,
            user_id=user_id,
            new_role=role_update.role
        )
        
        return {
            "user_id": org_user.user_id,
            "role": org_user.role.value,
            "updated_at": datetime.utcnow().isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update user role: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user role")


@router.delete("/{org_id}/users/{user_id}", response_model=dict)
@require_organization
@require_permission("users", "delete")
async def remove_user(
    org_id: int,
    user_id: int,
    tenancy_service = Depends(get_tenancy_service)
):
    """Remove user from organization"""
    if not tenancy_service:
        raise HTTPException(status_code=503, detail="Tenancy service not available")
    
    try:
        success = await tenancy_service.remove_user_from_organization(
            org_id=org_id,
            user_id=user_id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="User not found in organization")
        
        return {"message": "User removed successfully"}
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to remove user: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove user")


@router.get("/{org_id}/quota", response_model=dict)
@require_organization
async def get_quota_status(
    org_id: int,
    quota_manager = Depends(get_quota_manager)
):
    """Get organization quota status"""
    if not quota_manager:
        raise HTTPException(status_code=503, detail="Quota manager not available")
    
    try:
        quota_status = await quota_manager.get_organization_quota_status(org_id)
        
        return {
            "organization_id": org_id,
            "quotas": {
                resource: {
                    "current": status.current,
                    "limit": status.limit,
                    "percentage": status.percentage,
                    "is_exceeded": status.is_exceeded,
                    "is_warning": status.is_warning
                }
                for resource, status in quota_status.items()
            },
            "last_updated": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to get quota status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get quota status")


@router.get("/{org_id}/quota/alerts", response_model=List[dict])
@require_organization
async def get_quota_alerts(
    org_id: int,
    limit: int = Query(50, le=100),
    quota_manager = Depends(get_quota_manager)
):
    """Get recent quota alerts"""
    if not quota_manager:
        raise HTTPException(status_code=503, detail="Quota manager not available")
    
    try:
        alerts = await quota_manager.get_recent_alerts(org_id=org_id, limit=limit)
        
        return [
            {
                "resource": alert.resource,
                "current": alert.current,
                "limit": alert.limit,
                "percentage": alert.percentage,
                "severity": alert.severity,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat()
            }
            for alert in alerts
        ]
    
    except Exception as e:
        logger.error(f"Failed to get quota alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get quota alerts")


# Billing endpoints removed - no billing system needed