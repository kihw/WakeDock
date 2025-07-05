"""
Notifications WebSocket Handler

Notifications WebSocket en temps réel.
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

from .types import WebSocketMessage, NotificationMessage, EventType

logger = logging.getLogger(__name__)


class NotificationsWebSocketHandler:
    """Gestionnaire WebSocket pour les notifications"""
    
    def __init__(self, websocket_manager):
        """Initialiser le handler de notifications"""
        self.ws_manager = websocket_manager
    
    async def send_notification(
        self,
        user_id: Optional[int],
        title: str,
        message: str,
        level: str = "info",
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Envoyer une notification à un utilisateur ou globalement"""
        try:
            notification = NotificationMessage(
                id=f"notif_{datetime.utcnow().timestamp()}",
                title=title,
                message=message,
                level=level,
                user_id=user_id,
                data=data
            )
            
            ws_message = WebSocketMessage(
                type=EventType.NOTIFICATION.value,
                data=notification.dict()
            )
            
            if user_id:
                sent_count = await self.ws_manager.send_to_user(user_id, ws_message)
            else:
                sent_count = await self.ws_manager.broadcast_to_all(ws_message)
            
            logger.info(f"Sent notification '{title}' to {sent_count} connections")
            return sent_count > 0
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False
    
    async def send_alert(
        self,
        title: str,
        message: str,
        severity: str = "warning",
        target_users: Optional[List[int]] = None
    ) -> int:
        """Envoyer une alerte critique"""
        try:
            alert_data = {
                "id": f"alert_{datetime.utcnow().timestamp()}",
                "title": title,
                "message": message,
                "severity": severity,
                "timestamp": datetime.utcnow().isoformat(),
                "requires_acknowledgment": severity in ["critical", "high"]
            }
            
            ws_message = WebSocketMessage(
                type=EventType.ALERT.value,
                data=alert_data
            )
            
            total_sent = 0
            
            if target_users:
                for user_id in target_users:
                    sent_count = await self.ws_manager.send_to_user(user_id, ws_message)
                    total_sent += sent_count
            else:
                total_sent = await self.ws_manager.broadcast_to_all(ws_message)
            
            logger.warning(f"Sent {severity} alert '{title}' to {total_sent} connections")
            return total_sent
            
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
            return 0