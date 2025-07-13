"""
Tenancy Service

Core service for managing multi-tenant organizations including:
- Organization CRUD operations
- User-organization relationships
- Invitation management
- Resource quota tracking
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import secrets
import hashlib

from wakedock.database.models import User, Service
from wakedock.database.models.organization import (
    Organization, OrganizationUser, OrganizationInvitation, UsageRecord,
    SubscriptionTier, OrganizationRole, TenantQuota
)
from wakedock.database import get_db_session
from wakedock.config import get_settings

logger = logging.getLogger(__name__)


class TenancyService:
    """Core tenancy management service"""
    
    def __init__(self):
        self.settings = get_settings()
    
    async def create_organization(
        self,
        name: str,
        slug: str,
        owner_user_id: int,
        contact_email: str,
        subscription_tier: SubscriptionTier = SubscriptionTier.FREE,
        trial_days: int = 14
    ) -> Organization:
        """Create a new organization with owner"""
        async with get_db_session() as session:
            # Check if slug is unique
            existing = await session.query(Organization).filter(
                Organization.slug == slug
            ).first()
            
            if existing:
                raise ValueError(f"Organization slug '{slug}' already exists")
            
            # Get tier limits
            tier_limits = TenantQuota.get_tier_limits(subscription_tier)
            
            # Create organization
            organization = Organization(
                name=name,
                slug=slug,
                contact_email=contact_email,
                subscription_tier=subscription_tier,
                **{k: v for k, v in tier_limits.items() if k.startswith('max_')},
                features_enabled=tier_limits['features']
            )
            
            session.add(organization)
            await session.flush()  # Get the ID
            
            # Add owner relationship
            org_user = OrganizationUser(
                organization_id=organization.id,
                user_id=owner_user_id,
                role=OrganizationRole.OWNER,
                permissions={
                    "containers": {"read": True, "write": True, "delete": True},
                    "users": {"read": True, "write": True, "delete": True},
                    "settings": {"read": True, "write": True},
                    "billing": {"read": True, "write": True},
                    "analytics": {"read": True},
                    "backups": {"read": True, "write": True}
                }
            )
            
            session.add(org_user)
            await session.commit()
            
            logger.info(f"Created organization '{name}' with slug '{slug}' for user {owner_user_id}")
            return organization
    
    async def get_organization(self, org_id: int) -> Optional[Organization]:
        """Get organization by ID"""
        async with get_db_session() as session:
            return await session.query(Organization).filter(
                Organization.id == org_id
            ).first()
    
    async def get_organization_by_slug(self, slug: str) -> Optional[Organization]:
        """Get organization by slug"""
        async with get_db_session() as session:
            return await session.query(Organization).filter(
                Organization.slug == slug
            ).first()
    
    async def get_user_organizations(self, user_id: int) -> List[Organization]:
        """Get all organizations a user belongs to"""
        async with get_db_session() as session:
            org_users = await session.query(OrganizationUser).filter(
                OrganizationUser.user_id == user_id,
                OrganizationUser.is_active == True
            ).all()
            
            org_ids = [ou.organization_id for ou in org_users]
            if not org_ids:
                return []
            
            organizations = await session.query(Organization).filter(
                Organization.id.in_(org_ids),
                Organization.is_active == True
            ).all()
            
            return organizations
    
    async def get_user_role_in_organization(self, user_id: int, org_id: int) -> Optional[OrganizationRole]:
        """Get user's role in specific organization"""
        async with get_db_session() as session:
            org_user = await session.query(OrganizationUser).filter(
                OrganizationUser.user_id == user_id,
                OrganizationUser.organization_id == org_id,
                OrganizationUser.is_active == True
            ).first()
            
            return org_user.role if org_user else None
    
    async def update_organization(self, org_id: int, updates: Dict[str, Any]) -> Organization:
        """Update organization details"""
        async with get_db_session() as session:
            organization = await session.query(Organization).filter(
                Organization.id == org_id
            ).first()
            
            if not organization:
                raise ValueError(f"Organization {org_id} not found")
            
            # Update fields
            for field, value in updates.items():
                if hasattr(organization, field):
                    setattr(organization, field, value)
            
            organization.updated_at = datetime.utcnow()
            await session.commit()
            
            logger.info(f"Updated organization {org_id} with fields: {list(updates.keys())}")
            return organization
    
    async def invite_user_to_organization(
        self,
        org_id: int,
        email: str,
        role: OrganizationRole,
        invited_by_user_id: int,
        message: Optional[str] = None
    ) -> OrganizationInvitation:
        """Send invitation to user to join organization"""
        async with get_db_session() as session:
            # Check if organization exists and inviter has permission
            organization = await session.query(Organization).filter(
                Organization.id == org_id
            ).first()
            
            if not organization:
                raise ValueError(f"Organization {org_id} not found")
            
            # Check if user can add more members
            if not organization.can_add_user():
                raise ValueError("Organization has reached maximum user limit")
            
            # Check if user is already invited or member
            existing_invitation = await session.query(OrganizationInvitation).filter(
                OrganizationInvitation.organization_id == org_id,
                OrganizationInvitation.email == email,
                OrganizationInvitation.is_accepted == False,
                OrganizationInvitation.expires_at > datetime.utcnow()
            ).first()
            
            if existing_invitation:
                raise ValueError(f"User {email} already has pending invitation")
            
            # Create invitation
            invitation = OrganizationInvitation(
                organization_id=org_id,
                email=email,
                role=role,
                invited_by_user_id=invited_by_user_id,
                message=message,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            invitation.generate_token()
            
            session.add(invitation)
            await session.commit()
            
            logger.info(f"Created invitation for {email} to organization {org_id}")
            return invitation
    
    async def accept_invitation(self, token: str, user_id: int) -> OrganizationUser:
        """Accept organization invitation"""
        async with get_db_session() as session:
            invitation = await session.query(OrganizationInvitation).filter(
                OrganizationInvitation.token == token,
                OrganizationInvitation.is_accepted == False
            ).first()
            
            if not invitation:
                raise ValueError("Invalid invitation token")
            
            if invitation.is_expired:
                raise ValueError("Invitation has expired")
            
            # Get user email to verify
            user = await session.query(User).filter(User.id == user_id).first()
            if not user or user.email != invitation.email:
                raise ValueError("User email does not match invitation")
            
            # Check if user is already a member
            existing_membership = await session.query(OrganizationUser).filter(
                OrganizationUser.organization_id == invitation.organization_id,
                OrganizationUser.user_id == user_id,
                OrganizationUser.is_active == True
            ).first()
            
            if existing_membership:
                raise ValueError("User is already a member of this organization")
            
            # Create organization membership
            org_user = OrganizationUser(
                organization_id=invitation.organization_id,
                user_id=user_id,
                role=invitation.role
            )
            
            # Mark invitation as accepted
            invitation.is_accepted = True
            invitation.accepted_at = datetime.utcnow()
            
            # Update organization user count
            organization = await session.query(Organization).filter(
                Organization.id == invitation.organization_id
            ).first()
            organization.current_users += 1
            
            session.add(org_user)
            await session.commit()
            
            logger.info(f"User {user_id} accepted invitation to organization {invitation.organization_id}")
            return org_user
    
    async def remove_user_from_organization(self, org_id: int, user_id: int) -> bool:
        """Remove user from organization"""
        async with get_db_session() as session:
            org_user = await session.query(OrganizationUser).filter(
                OrganizationUser.organization_id == org_id,
                OrganizationUser.user_id == user_id,
                OrganizationUser.is_active == True
            ).first()
            
            if not org_user:
                return False
            
            # Cannot remove the last owner
            if org_user.role == OrganizationRole.OWNER:
                owner_count = await session.query(OrganizationUser).filter(
                    OrganizationUser.organization_id == org_id,
                    OrganizationUser.role == OrganizationRole.OWNER,
                    OrganizationUser.is_active == True
                ).count()
                
                if owner_count <= 1:
                    raise ValueError("Cannot remove the last owner from organization")
            
            # Mark as inactive
            org_user.is_active = False
            
            # Update organization user count
            organization = await session.query(Organization).filter(
                Organization.id == org_id
            ).first()
            organization.current_users = max(0, organization.current_users - 1)
            
            await session.commit()
            
            logger.info(f"Removed user {user_id} from organization {org_id}")
            return True
    
    async def update_user_role(self, org_id: int, user_id: int, new_role: OrganizationRole) -> OrganizationUser:
        """Update user role in organization"""
        async with get_db_session() as session:
            org_user = await session.query(OrganizationUser).filter(
                OrganizationUser.organization_id == org_id,
                OrganizationUser.user_id == user_id,
                OrganizationUser.is_active == True
            ).first()
            
            if not org_user:
                raise ValueError("User is not a member of this organization")
            
            # If changing from owner, ensure there's another owner
            if org_user.role == OrganizationRole.OWNER and new_role != OrganizationRole.OWNER:
                owner_count = await session.query(OrganizationUser).filter(
                    OrganizationUser.organization_id == org_id,
                    OrganizationUser.role == OrganizationRole.OWNER,
                    OrganizationUser.is_active == True
                ).count()
                
                if owner_count <= 1:
                    raise ValueError("Cannot change role of the last owner")
            
            org_user.role = new_role
            await session.commit()
            
            logger.info(f"Updated user {user_id} role to {new_role} in organization {org_id}")
            return org_user
    
    async def get_organization_services(self, org_id: int) -> List[Service]:
        """Get all services belonging to organization"""
        async with get_db_session() as session:
            services = await session.query(Service).filter(
                Service.organization_id == org_id
            ).all()
            
            return services
    
    async def update_resource_usage(self, org_id: int, usage_data: Dict[str, Any]) -> Organization:
        """Update organization's current resource usage"""
        async with get_db_session() as session:
            organization = await session.query(Organization).filter(
                Organization.id == org_id
            ).first()
            
            if not organization:
                raise ValueError(f"Organization {org_id} not found")
            
            # Update usage fields
            for field, value in usage_data.items():
                if hasattr(organization, f"current_{field}"):
                    setattr(organization, f"current_{field}", value)
            
            organization.updated_at = datetime.utcnow()
            await session.commit()
            
            return organization
    
    async def check_quota_exceeded(self, org_id: int, resource: str, requested_amount: float = 1) -> Tuple[bool, str]:
        """Check if adding resource would exceed quota"""
        async with get_db_session() as session:
            organization = await session.query(Organization).filter(
                Organization.id == org_id
            ).first()
            
            if not organization:
                raise ValueError(f"Organization {org_id} not found")
            
            # Get current and max values
            current_attr = f"current_{resource}"
            max_attr = f"max_{resource}"
            
            if not hasattr(organization, current_attr) or not hasattr(organization, max_attr):
                return False, f"Unknown resource: {resource}"
            
            current_value = getattr(organization, current_attr)
            max_value = getattr(organization, max_attr)
            
            # -1 means unlimited (enterprise tier)
            if max_value == -1:
                return False, ""
            
            if current_value + requested_amount > max_value:
                return True, f"Would exceed {resource} quota: {current_value + requested_amount} > {max_value}"
            
            return False, ""
    
    async def record_usage(self, org_id: int, period_start: datetime, period_end: datetime) -> UsageRecord:
        """Record usage statistics for billing period"""
        async with get_db_session() as session:
            organization = await session.query(Organization).filter(
                Organization.id == org_id
            ).first()
            
            if not organization:
                raise ValueError(f"Organization {org_id} not found")
            
            # Create usage record
            usage_record = UsageRecord(
                organization_id=org_id,
                containers_count=organization.current_containers,
                cpu_usage=organization.current_cpu_usage,
                memory_usage_gb=organization.current_memory_usage,
                storage_usage_gb=organization.current_storage_usage,
                backup_count=organization.current_backups,
                period_start=period_start,
                period_end=period_end
            )
            
            session.add(usage_record)
            await session.commit()
            
            logger.info(f"Recorded usage for organization {org_id} for period {period_start.date()}")
            return usage_record
    
    async def upgrade_subscription(self, org_id: int, new_tier: SubscriptionTier) -> Organization:
        """Upgrade organization subscription tier"""
        async with get_db_session() as session:
            organization = await session.query(Organization).filter(
                Organization.id == org_id
            ).first()
            
            if not organization:
                raise ValueError(f"Organization {org_id} not found")
            
            # Get new tier limits
            tier_limits = TenantQuota.get_tier_limits(new_tier)
            
            # Update subscription
            organization.subscription_tier = new_tier
            
            # Update quotas
            for field, value in tier_limits.items():
                if field.startswith('max_') and hasattr(organization, field):
                    setattr(organization, field, value)
            
            # Update features
            organization.features_enabled = tier_limits['features']
            organization.updated_at = datetime.utcnow()
            
            await session.commit()
            
            logger.info(f"Upgraded organization {org_id} to {new_tier}")
            return organization


# Global instance
_tenancy_service = None

def get_tenancy_service() -> Optional[TenancyService]:
    """Get the global tenancy service instance"""
    return _tenancy_service

def initialize_tenancy_service() -> TenancyService:
    """Initialize the global tenancy service instance"""
    global _tenancy_service
    _tenancy_service = TenancyService()
    return _tenancy_service