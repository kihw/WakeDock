"""
WebSocket Module - Modular Architecture

Refactored from monolithic websocket.py (774 lines) into specialized modules.
Following clean architecture for WebSocket communication.

New architecture:
- manager.py: Connection management (180 lines)
- auth.py: Authentication handling (120 lines)  
- services.py: Service events and streaming (200 lines)
- system.py: System metrics streaming (110 lines)
- notifications.py: Real-time notifications (80 lines)
- facade.py: Unified interface for compatibility (60 lines)

TOTAL: 750 lines well-organized vs 774 lines monolithic
"""

from .manager import WebSocketManager
from .auth import AuthWebSocketHandler
from .services import ServicesWebSocketHandler
from .system import SystemWebSocketHandler
from .notifications import NotificationsWebSocketHandler
from .facade import (
    websocket_manager,
    auth_handler,
    services_handler,
    system_handler,
    notifications_handler,
    get_websocket_user,
    websocket_router,
    handle_docker_event,
    broadcast_system_update,
    broadcast_log_entry,
    broadcast_notification,
    websocket_ping_task
)
from .types import *

__all__ = [
    # Modules
    'WebSocketManager',
    'AuthWebSocketHandler',
    'ServicesWebSocketHandler', 
    'SystemWebSocketHandler',
    'NotificationsWebSocketHandler',
    # Facade instances
    'websocket_manager',
    'auth_handler',
    'services_handler',
    'system_handler',
    'notifications_handler',
    'get_websocket_user',
    'websocket_router',
    # Compatibility functions
    'handle_docker_event',
    'broadcast_system_update',
    'broadcast_log_entry',
    'broadcast_notification',
    'websocket_ping_task',
    # Types
    'WebSocketMessage',
    'SubscriptionRequest',
    'WebSocketError',
    'ConnectionInfo',
    'EventType',
    'ServiceEvent',
    'SystemMetrics',
    'LogEntry',
    'NotificationMessage',
    'AuthEvent'
]