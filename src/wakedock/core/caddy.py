"""
DEPRECATED: Caddy integration for WakeDock dynamic reverse proxy management.

This file has been refactored into a modular architecture located in:
src/wakedock/infrastructure/caddy/

The new architecture provides:
- CaddyConfigManager: Configuration management (220 lines)
- CaddyApiClient: API communication (180 lines)
- RoutesManager: Dynamic routes management (280 lines)
- CaddyHealthMonitor: Health monitoring and metrics (240 lines)
- CaddyManager: Unified facade (maintains compatibility, 120 lines)

TOTAL: 1040 lines well-organized vs 879 lines monolithic

Please update imports to:
from wakedock.infrastructure.caddy import CaddyManager
"""

import warnings
import logging

# Import the new modular CaddyManager
from wakedock.infrastructure.caddy import CaddyManager as NewCaddyManager

logger = logging.getLogger(__name__)


class CaddyManager(NewCaddyManager):
    """Compatibility wrapper for the old CaddyManager class"""
    
    def __init__(self):
        warnings.warn(
            "wakedock.core.caddy.CaddyManager is deprecated. "
            "Use wakedock.infrastructure.caddy.CaddyManager instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__()
        logger.warning(
            "Using deprecated CaddyManager import. "
            "Please update to: from wakedock.infrastructure.caddy import CaddyManager"
        )


# Legacy export for backward compatibility
__all__ = ['CaddyManager']