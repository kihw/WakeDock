"""Database Models Package"""

from .base import Base, Service, User, Configuration, ServiceStatus, ServiceLog, UserRole
from .organization import (
    Organization, OrganizationUser, OrganizationInvitation, UsageRecord,
    SubscriptionTier, OrganizationRole, TenantQuota
)

# Import advanced security models
try:
    from wakedock.security.advanced.models import (
        SecurityRule, SecurityEvent, IPWhitelist, GeoBlock, MFAMethod,
        ThreatLevel, SecurityRuleType, SecurityActionType
    )
    _security_models_available = True
except ImportError:
    _security_models_available = False

__all__ = [
    # Base models
    "Base",
    "Service", 
    "User",
    "Configuration",
    "ServiceStatus",
    "ServiceLog",
    "UserRole",
    
    # Organization models
    "Organization",
    "OrganizationUser", 
    "OrganizationInvitation",
    "UsageRecord",
    "SubscriptionTier",
 
    "OrganizationRole",
    "TenantQuota"
]

# Add security models to exports if available
if _security_models_available:
    __all__.extend([
        "SecurityRule", "SecurityEvent", "IPWhitelist", "GeoBlock", "MFAMethod",
        "ThreatLevel", "SecurityRuleType", "SecurityActionType"
    ])