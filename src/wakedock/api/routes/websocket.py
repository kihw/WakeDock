"""
DEPRECATED: WebSocket Routes for Real-time Communication

This file has been refactored into a modular architecture located in:
src/wakedock/api/websocket/

The new architecture provides:
- WebSocketManager: Connection management (180 lines)
- AuthWebSocketHandler: Authentication handling (120 lines)
- ServicesWebSocketHandler: Service events and streaming (200 lines)
- SystemWebSocketHandler: System metrics streaming (110 lines)
- NotificationsWebSocketHandler: Real-time notifications (80 lines)
- Facade: Unified interface for compatibility (60 lines)

TOTAL: 750 lines well-organized vs 774 lines monolithic

Please update imports to:
from wakedock.api.websocket import websocket_router, get_websocket_user
"""

import warnings
import logging

# Import the new modular WebSocket components
from wakedock.api.websocket import (
    websocket_router,
    get_websocket_user,
    websocket_manager,
    WebSocketMessage,
    SubscriptionRequest,
    WebSocketError,
    handle_docker_event,
    broadcast_system_update,
    broadcast_log_entry,
    broadcast_notification,
    websocket_ping_task
)

logger = logging.getLogger(__name__)

# Compatibility warning
warnings.warn(
    "wakedock.api.routes.websocket is deprecated. "
    "Use wakedock.api.websocket instead.",
    DeprecationWarning,
    stacklevel=2
)

logger.warning(
    "Using deprecated WebSocket routes. "
    "Please update to: from wakedock.api.websocket import websocket_router"
)

# Re-export for backward compatibility
WebSocketManager = websocket_manager.__class__
router = websocket_router  # Backward compatibility alias

__all__ = [
    'websocket_router',
    'router',  # Backward compatibility
    'get_websocket_user', 
    'WebSocketManager',
    'WebSocketMessage',
    'SubscriptionRequest', 
    'WebSocketError',
    'handle_docker_event',
    'broadcast_system_update',
    'broadcast_log_entry',
    'broadcast_notification',
    'websocket_ping_task'
]