"""
Organization Models for Multi-tenancy Support

Provides database models for multi-tenant architecture including:
- Organization management with isolation
- Tenant-specific resource quotas
- Billing and subscription tracking
- User-organization relationships
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Numeric, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import uuid

from .base import Base


class SubscriptionTier(str, Enum):
    """Subscription tier options"""
    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"




class Organization(Base):
    """Organization model for multi-tenancy"""
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Contact information
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(50), nullable=True)
    
    # Address information
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    
    # Subscription tier (no billing)
    subscription_tier = Column(SQLEnum(SubscriptionTier), default=SubscriptionTier.FREE, nullable=False)
    
    # Resource quotas
    max_containers = Column(Integer, default=5, nullable=False)
    max_cpu_cores = Column(Numeric(4, 2), default=2.0, nullable=False)
    max_memory_gb = Column(Numeric(6, 2), default=4.0, nullable=False)
    max_storage_gb = Column(Numeric(8, 2), default=20.0, nullable=False)
    max_users = Column(Integer, default=3, nullable=False)
    max_backups = Column(Integer, default=5, nullable=False)
    
    # Feature flags
    features_enabled = Column(JSON, default=lambda: {
        "monitoring": True,
        "backups": False,
        "analytics": False,
        "custom_domains": False,
        "api_access": True,
        "webhooks": False,
        "audit_logs": False,
        "sso": False,
        "priority_support": False
    })
    
    # Usage tracking
    current_containers = Column(Integer, default=0, nullable=False)
    current_cpu_usage = Column(Numeric(4, 2), default=0.0, nullable=False)
    current_memory_usage = Column(Numeric(6, 2), default=0.0, nullable=False)
    current_storage_usage = Column(Numeric(8, 2), default=0.0, nullable=False)
    current_users = Column(Integer, default=1, nullable=False)
    current_backups = Column(Integer, default=0, nullable=False)
    
    # Settings and preferences
    settings = Column(JSON, default=lambda: {
        "timezone": "UTC",
        "date_format": "YYYY-MM-DD",
        "currency": "USD",
        "notifications": {
            "email": True,
            "webhook": False,
            "sms": False
        },
        "security": {
            "require_2fa": False,
            "password_policy": "standard",
            "session_timeout": 24
        }
    })
    
    # Status and metadata
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # External IDs for integrations
    external_crm_id = Column(String(255), nullable=True)     # CRM system ID
    
    # Relationships
    users = relationship("OrganizationUser", back_populates="organization", cascade="all, delete-orphan")
    services = relationship("Service", back_populates="organization")
    invitations = relationship("OrganizationInvitation", back_populates="organization", cascade="all, delete-orphan")
    usage_records = relationship("UsageRecord", back_populates="organization", cascade="all, delete-orphan")
    
    # Security relationships (commented out to avoid circular imports)
    # security_rules = relationship("SecurityRule", back_populates="organization", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}', slug='{self.slug}')>"
    
    
    def can_create_container(self) -> bool:
        """Check if organization can create another container"""
        return self.current_containers < self.max_containers
    
    def can_add_user(self) -> bool:
        """Check if organization can add another user"""
        return self.current_users < self.max_users
    
    def has_feature(self, feature: str) -> bool:
        """Check if organization has access to a specific feature"""
        return self.features_enabled.get(feature, False)
    
    def get_quota_usage(self) -> Dict[str, float]:
        """Get quota usage percentages"""
        return {
            "containers": (self.current_containers / self.max_containers) * 100 if self.max_containers > 0 else 0,
            "cpu": (float(self.current_cpu_usage) / float(self.max_cpu_cores)) * 100 if self.max_cpu_cores > 0 else 0,
            "memory": (float(self.current_memory_usage) / float(self.max_memory_gb)) * 100 if self.max_memory_gb > 0 else 0,
            "storage": (float(self.current_storage_usage) / float(self.max_storage_gb)) * 100 if self.max_storage_gb > 0 else 0,
            "users": (self.current_users / self.max_users) * 100 if self.max_users > 0 else 0,
            "backups": (self.current_backups / self.max_backups) * 100 if self.max_backups > 0 else 0
        }


class OrganizationRole(str, Enum):
    """Organization user roles"""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class OrganizationUser(Base):
    """User-Organization relationship with roles"""
    __tablename__ = "organization_users"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(SQLEnum(OrganizationRole), default=OrganizationRole.MEMBER, nullable=False)
    
    # Permissions and access
    permissions = Column(JSON, default=lambda: {
        "containers": {"read": True, "write": False, "delete": False},
        "users": {"read": False, "write": False, "delete": False},
        "settings": {"read": False, "write": False},
        "analytics": {"read": False},
        "backups": {"read": False, "write": False}
    })
    
    # Status and metadata
    is_active = Column(Boolean, default=True, nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_active_at = Column(DateTime, nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    user = relationship("User")
    
    def __repr__(self):
        return f"<OrganizationUser(org_id={self.organization_id}, user_id={self.user_id}, role='{self.role}')>"
    
    def has_permission(self, resource: str, action: str) -> bool:
        """Check if user has specific permission"""
        return self.permissions.get(resource, {}).get(action, False)


class OrganizationInvitation(Base):
    """Organization invitations for new users"""
    __tablename__ = "organization_invitations"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    role = Column(SQLEnum(OrganizationRole), default=OrganizationRole.MEMBER, nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    
    # Invitation details
    invited_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=True)
    
    # Status and timestamps
    is_accepted = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="invitations")
    invited_by = relationship("User")
    
    def __repr__(self):
        return f"<OrganizationInvitation(id={self.id}, email='{self.email}', org_id={self.organization_id})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if invitation has expired"""
        return datetime.utcnow() > self.expires_at
    
    def generate_token(self) -> str:
        """Generate unique invitation token"""
        import secrets
        self.token = secrets.token_urlsafe(32)
        return self.token


class UsageRecord(Base):
    """Track organization resource usage over time"""
    __tablename__ = "usage_records"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Resource usage snapshots
    containers_count = Column(Integer, default=0, nullable=False)
    cpu_usage = Column(Numeric(6, 2), default=0.0, nullable=False)
    memory_usage_gb = Column(Numeric(8, 2), default=0.0, nullable=False)
    storage_usage_gb = Column(Numeric(10, 2), default=0.0, nullable=False)
    bandwidth_usage_gb = Column(Numeric(10, 2), default=0.0, nullable=False)
    api_requests = Column(Integer, default=0, nullable=False)
    backup_count = Column(Integer, default=0, nullable=False)
    
    # Usage period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="usage_records")
    
    def __repr__(self):
        return f"<UsageRecord(id={self.id}, org_id={self.organization_id}, period={self.period_start.date()})>"
    


class TenantQuota:
    """Utility class for quota management"""
    
    @staticmethod
    def get_tier_limits(tier: SubscriptionTier) -> Dict[str, Any]:
        """Get resource limits for subscription tier"""
        limits = {
            SubscriptionTier.FREE: {
                "max_containers": 2,
                "max_cpu_cores": 1.0,
                "max_memory_gb": 2.0,
                "max_storage_gb": 10.0,
                "max_users": 1,
                "max_backups": 2,
                "features": {
                    "monitoring": True,
                    "backups": False,
                    "analytics": False,
                    "custom_domains": False,
                    "api_access": True,
                    "webhooks": False,
                    "audit_logs": False,
                    "sso": False,
                    "priority_support": False
                }
            },
            SubscriptionTier.BASIC: {
                "max_containers": 10,
                "max_cpu_cores": 4.0,
                "max_memory_gb": 8.0,
                "max_storage_gb": 50.0,
                "max_users": 5,
                "max_backups": 10,
                "features": {
                    "monitoring": True,
                    "backups": True,
                    "analytics": True,
                    "custom_domains": False,
                    "api_access": True,
                    "webhooks": True,
                    "audit_logs": False,
                    "sso": False,
                    "priority_support": False
                }
            },
            SubscriptionTier.PROFESSIONAL: {
                "max_containers": 50,
                "max_cpu_cores": 16.0,
                "max_memory_gb": 32.0,
                "max_storage_gb": 200.0,
                "max_users": 25,
                "max_backups": 50,
                "features": {
                    "monitoring": True,
                    "backups": True,
                    "analytics": True,
                    "custom_domains": True,
                    "api_access": True,
                    "webhooks": True,
                    "audit_logs": True,
                    "sso": True,
                    "priority_support": True
                }
            },
            SubscriptionTier.ENTERPRISE: {
                "max_containers": -1,  # Unlimited
                "max_cpu_cores": -1,   # Unlimited
                "max_memory_gb": -1,   # Unlimited
                "max_storage_gb": -1,  # Unlimited
                "max_users": -1,       # Unlimited
                "max_backups": -1,     # Unlimited
                "features": {
                    "monitoring": True,
                    "backups": True,
                    "analytics": True,
                    "custom_domains": True,
                    "api_access": True,
                    "webhooks": True,
                    "audit_logs": True,
                    "sso": True,
                    "priority_support": True
                }
            }
        }
        return limits.get(tier, limits[SubscriptionTier.FREE])
    
    @staticmethod
    def calculate_trial_end(days: int = 14) -> datetime:
        """Calculate trial end date"""
        return datetime.utcnow() + timedelta(days=days)