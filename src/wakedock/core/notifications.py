"""
Notification System
Manages and broadcasts notifications via WebSocket
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, Set, List
from enum import Enum
from dataclasses import dataclass, asdict
import uuid

logger = logging.getLogger(__name__)

class NotificationLevel(str, Enum):
    """Notification severity levels"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class NotificationCategory(str, Enum):
    """Notification categories"""
    SYSTEM = "system"
    DOCKER = "docker"
    SERVICE = "service"
    SECURITY = "security"
    MONITORING = "monitoring"
    USER = "user"

@dataclass
class Notification:
    """Notification data structure"""
    id: str
    title: str
    message: str
    level: NotificationLevel
    category: NotificationCategory
    timestamp: str
    source: str = "wakedock"
    data: Dict[str, Any] = None
    persistent: bool = False
    auto_dismiss: bool = True
    dismiss_after: int = 5000  # milliseconds
    actions: List[Dict[str, str]] = None
    read: bool = False
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}
        if self.actions is None:
            self.actions = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary"""
        return asdict(self)

class NotificationManager:
    """
    Manages notifications and broadcasting
    """
    
    def __init__(self, max_notifications: int = 1000):
        self.max_notifications = max_notifications
        self.notifications: Dict[str, Notification] = {}
        self.subscribers: Set[Callable] = set()
        self.user_subscribers: Dict[str, Set[Callable]] = {}
        self.notification_rules: Dict[str, Dict[str, Any]] = {}
        
    def subscribe(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribe to all notifications"""
        self.subscribers.add(callback)
        logger.debug(f"Added notification subscriber. Total: {len(self.subscribers)}")
        
    def subscribe_user(self, user_id: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribe to notifications for a specific user"""
        if user_id not in self.user_subscribers:
            self.user_subscribers[user_id] = set()
        self.user_subscribers[user_id].add(callback)
        logger.debug(f"Added notification subscriber for user {user_id}")
        
    def unsubscribe(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Unsubscribe from all notifications"""
        self.subscribers.discard(callback)
        # Also remove from user subscriptions
        for user_id in self.user_subscribers:
            self.user_subscribers[user_id].discard(callback)
        logger.debug(f"Removed notification subscriber. Total: {len(self.subscribers)}")
        
    def unsubscribe_user(self, user_id: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Unsubscribe from notifications for a specific user"""
        if user_id in self.user_subscribers:
            self.user_subscribers[user_id].discard(callback)
            # Clean up empty sets
            if not self.user_subscribers[user_id]:
                del self.user_subscribers[user_id]
        logger.debug(f"Removed notification subscriber for user {user_id}")
    
    async def create_notification(
        self,
        title: str,
        message: str,
        level: NotificationLevel = NotificationLevel.INFO,
        category: NotificationCategory = NotificationCategory.SYSTEM,
        source: str = "wakedock",
        data: Dict[str, Any] = None,
        persistent: bool = False,
        auto_dismiss: bool = True,
        dismiss_after: int = 5000,
        actions: List[Dict[str, str]] = None,
        user_id: Optional[str] = None
    ) -> str:
        """Create and broadcast a new notification"""
        
        notification_id = str(uuid.uuid4())
        
        notification = Notification(
            id=notification_id,
            title=title,
            message=message,
            level=level,
            category=category,
            timestamp=datetime.utcnow().isoformat(),
            source=source,
            data=data or {},
            persistent=persistent,
            auto_dismiss=auto_dismiss,
            dismiss_after=dismiss_after,
            actions=actions or []
        )
        
        # Store notification
        self.notifications[notification_id] = notification
        
        # Cleanup old notifications if we exceed max
        if len(self.notifications) > self.max_notifications:
            await self._cleanup_old_notifications()
        
        # Broadcast notification
        await self._broadcast_notification(notification, user_id)
        
        logger.info(f"Created {level.value} notification: {title}")
        return notification_id
    
    async def mark_as_read(self, notification_id: str, user_id: Optional[str] = None) -> bool:
        """Mark a notification as read"""
        if notification_id not in self.notifications:
            return False
            
        self.notifications[notification_id].read = True
        
        # Broadcast update
        update_message = {
            'type': 'notification_update',
            'data': {
                'id': notification_id,
                'action': 'mark_read',
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        if user_id:
            await self._broadcast_to_user(update_message, user_id)
        else:
            await self._broadcast_to_all(update_message)
            
        return True
    
    async def dismiss_notification(self, notification_id: str, user_id: Optional[str] = None) -> bool:
        """Dismiss a notification"""
        if notification_id not in self.notifications:
            return False
            
        notification = self.notifications.pop(notification_id)
        
        # Broadcast dismissal
        dismiss_message = {
            'type': 'notification_dismissed',
            'data': {
                'id': notification_id,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        if user_id:
            await self._broadcast_to_user(dismiss_message, user_id)
        else:
            await self._broadcast_to_all(dismiss_message)
            
        logger.debug(f"Dismissed notification: {notification.title}")
        return True
    
    async def clear_all_notifications(self, user_id: Optional[str] = None) -> int:
        """Clear all notifications"""
        count = len(self.notifications)
        self.notifications.clear()
        
        # Broadcast clear all
        clear_message = {
            'type': 'notifications_cleared',
            'data': {
                'count': count,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        if user_id:
            await self._broadcast_to_user(clear_message, user_id)
        else:
            await self._broadcast_to_all(clear_message)
            
        logger.info(f"Cleared {count} notifications")
        return count
    
    def get_notifications(
        self,
        limit: int = 50,
        offset: int = 0,
        level: Optional[NotificationLevel] = None,
        category: Optional[NotificationCategory] = None,
        unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Get notifications with filtering"""
        
        notifications = list(self.notifications.values())
        
        # Apply filters
        if level:
            notifications = [n for n in notifications if n.level == level]
        if category:
            notifications = [n for n in notifications if n.category == category]
        if unread_only:
            notifications = [n for n in notifications if not n.read]
        
        # Sort by timestamp (newest first)
        notifications.sort(key=lambda n: n.timestamp, reverse=True)
        
        # Apply pagination
        notifications = notifications[offset:offset + limit]
        
        return [n.to_dict() for n in notifications]
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification statistics"""
        total = len(self.notifications)
        unread = len([n for n in self.notifications.values() if not n.read])
        
        by_level = {}
        by_category = {}
        
        for notification in self.notifications.values():
            # Count by level
            level = notification.level.value
            by_level[level] = by_level.get(level, 0) + 1
            
            # Count by category
            category = notification.category.value
            by_category[category] = by_category.get(category, 0) + 1
        
        return {
            'total': total,
            'unread': unread,
            'read': total - unread,
            'by_level': by_level,
            'by_category': by_category,
            'subscribers': len(self.subscribers),
            'user_subscribers': len(self.user_subscribers)
        }
    
    async def _broadcast_notification(self, notification: Notification, user_id: Optional[str] = None) -> None:
        """Broadcast notification to subscribers"""
        message = {
            'type': 'notification',
            'data': notification.to_dict()
        }
        
        if user_id:
            await self._broadcast_to_user(message, user_id)
        else:
            await self._broadcast_to_all(message)
    
    async def _broadcast_to_all(self, message: Dict[str, Any]) -> None:
        """Broadcast message to all subscribers"""
        for callback in self.subscribers.copy():
            try:
                await self._safe_callback(callback, message)
            except Exception as e:
                logger.error(f"Error in notification callback: {e}")
    
    async def _broadcast_to_user(self, message: Dict[str, Any], user_id: str) -> None:
        """Broadcast message to specific user subscribers"""
        if user_id in self.user_subscribers:
            for callback in self.user_subscribers[user_id].copy():
                try:
                    await self._safe_callback(callback, message)
                except Exception as e:
                    logger.error(f"Error in user notification callback: {e}")
    
    async def _safe_callback(self, callback: Callable, data: Dict[str, Any]) -> None:
        """Safely execute callback"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(data)
            else:
                callback(data)
        except Exception as e:
            logger.error(f"Notification callback execution failed: {e}")
    
    async def _cleanup_old_notifications(self) -> None:
        """Remove old notifications to maintain max limit"""
        notifications = list(self.notifications.values())
        
        # Sort by timestamp (oldest first)
        notifications.sort(key=lambda n: n.timestamp)
        
        # Remove oldest non-persistent notifications
        to_remove = []
        for notification in notifications:
            if not notification.persistent and len(to_remove) < (len(notifications) - self.max_notifications + 100):
                to_remove.append(notification.id)
        
        for notification_id in to_remove:
            self.notifications.pop(notification_id, None)
        
        if to_remove:
            logger.debug(f"Cleaned up {len(to_remove)} old notifications")

# Predefined notification helpers
class NotificationHelpers:
    """Helper methods for common notifications"""
    
    @staticmethod
    async def docker_container_started(manager: NotificationManager, container_name: str, container_id: str):
        """Send notification when container starts"""
        await manager.create_notification(
            title="Container Started",
            message=f"Container '{container_name}' has started successfully",
            level=NotificationLevel.SUCCESS,
            category=NotificationCategory.DOCKER,
            data={"container_name": container_name, "container_id": container_id}
        )
    
    @staticmethod
    async def docker_container_stopped(manager: NotificationManager, container_name: str, container_id: str):
        """Send notification when container stops"""
        await manager.create_notification(
            title="Container Stopped", 
            message=f"Container '{container_name}' has stopped",
            level=NotificationLevel.WARNING,
            category=NotificationCategory.DOCKER,
            data={"container_name": container_name, "container_id": container_id}
        )
    
    @staticmethod
    async def docker_container_error(manager: NotificationManager, container_name: str, container_id: str, error: str):
        """Send notification when container has error"""
        await manager.create_notification(
            title="Container Error",
            message=f"Container '{container_name}' encountered an error: {error}",
            level=NotificationLevel.ERROR,
            category=NotificationCategory.DOCKER,
            data={"container_name": container_name, "container_id": container_id, "error": error},
            persistent=True
        )
    
    @staticmethod
    async def system_resource_warning(manager: NotificationManager, resource: str, usage: float, threshold: float):
        """Send notification for high resource usage"""
        await manager.create_notification(
            title="High Resource Usage",
            message=f"{resource} usage is {usage:.1f}% (threshold: {threshold:.1f}%)",
            level=NotificationLevel.WARNING,
            category=NotificationCategory.MONITORING,
            data={"resource": resource, "usage": usage, "threshold": threshold}
        )
    
    @staticmethod
    async def system_resource_critical(manager: NotificationManager, resource: str, usage: float, threshold: float):
        """Send notification for critical resource usage"""
        await manager.create_notification(
            title="Critical Resource Usage",
            message=f"{resource} usage is critically high: {usage:.1f}% (threshold: {threshold:.1f}%)",
            level=NotificationLevel.CRITICAL,
            category=NotificationCategory.MONITORING,
            data={"resource": resource, "usage": usage, "threshold": threshold},
            persistent=True
        )
    
    @staticmethod
    async def service_health_check_failed(manager: NotificationManager, service_name: str, endpoint: str):
        """Send notification when service health check fails"""
        await manager.create_notification(
            title="Service Health Check Failed",
            message=f"Health check failed for service '{service_name}' at {endpoint}",
            level=NotificationLevel.ERROR,
            category=NotificationCategory.SERVICE,
            data={"service_name": service_name, "endpoint": endpoint}
        )
    
    @staticmethod
    async def security_alert(manager: NotificationManager, alert_type: str, details: str):
        """Send security alert notification"""
        await manager.create_notification(
            title="Security Alert",
            message=f"{alert_type}: {details}",
            level=NotificationLevel.CRITICAL,
            category=NotificationCategory.SECURITY,
            data={"alert_type": alert_type, "details": details},
            persistent=True,
            auto_dismiss=False
        )

# Global instance (will be initialized by the main app)
notification_manager: Optional[NotificationManager] = None

def initialize_notifications(max_notifications: int = 1000) -> NotificationManager:
    """Initialize the global notification manager"""
    global notification_manager
    notification_manager = NotificationManager(max_notifications)
    return notification_manager

def get_notification_manager() -> Optional[NotificationManager]:
    """Get the global notification manager"""
    return notification_manager