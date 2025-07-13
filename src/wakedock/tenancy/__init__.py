"""
Multi-tenancy Support Module

Provides comprehensive multi-tenant functionality including:
- Organization management and isolation
- Resource quota enforcement
- Tenant-aware services and APIs
- Billing and subscription tracking
"""

from .service import TenancyService, get_tenancy_service, initialize_tenancy_service
from .middleware import TenantMiddleware

__all__ = [
    "TenancyService",
    "get_tenancy_service", 
    "initialize_tenancy_service",
    "TenantMiddleware"
]

# Import functions to avoid circular dependencies
def get_quota_manager():
    from .quota import get_quota_manager
    return get_quota_manager()

def initialize_quota_manager():
    from .quota import initialize_quota_manager
    return initialize_quota_manager()