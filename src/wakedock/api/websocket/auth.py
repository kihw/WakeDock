"""
Authentication WebSocket Handler

Gestion des événements d'authentification via WebSocket.
"""

import logging
from typing import Optional
from fastapi import WebSocket

from wakedock.api.auth.jwt import jwt_manager
from wakedock.database.models import User
from .types import WebSocketMessage, AuthEvent, EventType

logger = logging.getLogger(__name__)


class AuthWebSocketHandler:
    """Gestionnaire WebSocket pour l'authentification"""
    
    def __init__(self, websocket_manager):
        """Initialiser le handler d'authentification"""
        self.ws_manager = websocket_manager
    
    async def get_websocket_user(self, websocket: WebSocket) -> Optional[User]:
        """
        Extraire et valider l'utilisateur depuis la connexion WebSocket.
        Vérifie token dans query parameters et headers.
        """
        try:
            # Essayer de récupérer le token depuis les query parameters
            token = None
            if hasattr(websocket, 'query_params'):
                token = websocket.query_params.get('token')
            
            # Si pas de token dans query params, essayer les headers
            if not token and hasattr(websocket, 'headers'):
                auth_header = websocket.headers.get('authorization')
                if auth_header and auth_header.startswith('Bearer '):
                    token = auth_header[7:]
            
            if not token:
                logger.debug("No authentication token found in WebSocket connection")
                return None
            
            # Vérifier et décoder le token
            token_data = await jwt_manager.verify_token(token)
            if not token_data:
                logger.debug("Invalid authentication token in WebSocket connection")
                return None
            
            # Créer l'objet utilisateur depuis les données du token
            # TODO: Récupérer depuis la base de données pour des données complètes
            user = User(
                id=int(token_data.get('sub', 0)),
                username=token_data.get('username', 'unknown'),
                email=token_data.get('email', ''),
                role=token_data.get('role', 'user'),
                roles=[token_data.get('role', 'user')],
                permissions=token_data.get('permissions', []),
                is_active=True,
                is_verified=True,
                created_at=token_data.get('created_at', ''),
                updated_at=token_data.get('updated_at', ''),
                last_login=token_data.get('last_login')
            )
            
            logger.debug(f"Authenticated WebSocket user: {user.username} (ID: {user.id})")
            return user
            
        except Exception as e:
            logger.error(f"Error authenticating WebSocket user: {e}")
            return None
    
    async def handle_login_event(
        self, 
        user: User, 
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Traiter un événement de connexion"""
        try:
            auth_event = AuthEvent(
                user_id=user.id,
                username=user.username,
                event_type="login",
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Message pour l'utilisateur connecté
            user_message = WebSocketMessage(
                type=EventType.AUTH_LOGIN.value,
                data={
                    "message": "Authentication successful",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "role": user.role
                    },
                    "timestamp": auth_event.timestamp.isoformat()
                }
            )
            
            # Envoyer à toutes les connexions de l'utilisateur
            await self.ws_manager.send_to_user(user.id, user_message)
            
            # Message de notification pour les admins (optionnel)
            if hasattr(user, 'role') and user.role != 'admin':
                admin_message = WebSocketMessage(
                    type="admin:user_login",
                    data=auth_event.dict()
                )
                
                # TODO: Envoyer aux utilisateurs admin uniquement
                # await self.ws_manager.broadcast_to_role("admin", admin_message)
            
            logger.info(f"Processed login event for user {user.username}")
            
        except Exception as e:
            logger.error(f"Error handling login event for user {user.id}: {e}")
    
    async def handle_logout_event(
        self, 
        user: User,
        connection_id: Optional[str] = None
    ) -> None:
        """Traiter un événement de déconnexion"""
        try:
            auth_event = AuthEvent(
                user_id=user.id,
                username=user.username,
                event_type="logout"
            )
            
            # Message de déconnexion
            logout_message = WebSocketMessage(
                type=EventType.AUTH_LOGOUT.value,
                data={
                    "message": "User logged out",
                    "user_id": user.id,
                    "username": user.username,
                    "timestamp": auth_event.timestamp.isoformat()
                }
            )
            
            if connection_id:
                # Envoyer à la connexion spécifique
                await self.ws_manager.send_to_connection(connection_id, logout_message)
            else:
                # Envoyer à toutes les connexions de l'utilisateur
                await self.ws_manager.send_to_user(user.id, logout_message)
            
            logger.info(f"Processed logout event for user {user.username}")
            
        except Exception as e:
            logger.error(f"Error handling logout event for user {user.id}: {e}")
    
    async def handle_session_expired_event(
        self, 
        user: User,
        reason: str = "Token expired"
    ) -> None:
        """Traiter un événement d'expiration de session"""
        try:
            expired_message = WebSocketMessage(
                type=EventType.AUTH_SESSION_EXPIRED.value,
                data={
                    "message": "Session expired",
                    "reason": reason,
                    "user_id": user.id,
                    "action_required": "Please log in again"
                }
            )
            
            # Envoyer à toutes les connexions de l'utilisateur
            sent_count = await self.ws_manager.send_to_user(user.id, expired_message)
            
            # Déconnecter toutes les connexions de l'utilisateur
            user_connections = self.ws_manager.get_user_connections(user.id)
            for connection_id in user_connections:
                await self.ws_manager.disconnect(connection_id)
            
            logger.info(f"Processed session expired event for user {user.username}, "
                       f"notified {sent_count} connections")
            
        except Exception as e:
            logger.error(f"Error handling session expired event for user {user.id}: {e}")
    
    async def validate_user_permissions(
        self, 
        user: User, 
        required_permission: str
    ) -> bool:
        """Valider les permissions d'un utilisateur pour WebSocket"""
        try:
            # Vérifier si l'utilisateur est actif
            if not user.is_active:
                return False
            
            # Vérifier si l'utilisateur est vérifié
            if not user.is_verified:
                return False
            
            # Les admins ont toutes les permissions
            if user.role == 'admin':
                return True
            
            # Vérifier la permission spécifique
            if hasattr(user, 'permissions') and user.permissions:
                return required_permission in user.permissions
            
            # Vérifier les rôles par défaut
            default_permissions = {
                'user': [
                    'websocket:connect',
                    'services:read',
                    'system:read'
                ],
                'viewer': [
                    'websocket:connect',
                    'services:read'
                ]
            }
            
            role_permissions = default_permissions.get(user.role, [])
            return required_permission in role_permissions
            
        except Exception as e:
            logger.error(f"Error validating permissions for user {user.id}: {e}")
            return False
    
    async def get_user_connection_info(self, user_id: int) -> dict:
        """Récupérer les informations de connexion d'un utilisateur"""
        try:
            user_connections = self.ws_manager.get_user_connections(user_id)
            
            connection_details = []
            for connection_id in user_connections:
                conn_info = self.ws_manager.connection_info.get(connection_id)
                if conn_info:
                    connection_details.append({
                        "connection_id": connection_id,
                        "connected_at": conn_info.connected_at.isoformat(),
                        "last_activity": conn_info.last_activity.isoformat(),
                        "subscriptions": list(conn_info.subscriptions),
                        "ip_address": conn_info.ip_address,
                        "user_agent": conn_info.user_agent
                    })
            
            return {
                "user_id": user_id,
                "active_connections": len(user_connections),
                "connections": connection_details,
                "is_connected": len(user_connections) > 0
            }
            
        except Exception as e:
            logger.error(f"Error getting connection info for user {user_id}: {e}")
            return {
                "user_id": user_id,
                "active_connections": 0,
                "connections": [],
                "is_connected": False,
                "error": str(e)
            }
    
    async def force_disconnect_user(
        self, 
        user_id: int, 
        reason: str = "Administrative action"
    ) -> int:
        """Forcer la déconnexion de toutes les connexions d'un utilisateur"""
        try:
            # Message de déconnexion forcée
            disconnect_message = WebSocketMessage(
                type="connection:force_disconnect",
                data={
                    "message": "Connection terminated by administrator",
                    "reason": reason
                }
            )
            
            # Envoyer le message à toutes les connexions
            sent_count = await self.ws_manager.send_to_user(user_id, disconnect_message)
            
            # Déconnecter toutes les connexions
            user_connections = self.ws_manager.get_user_connections(user_id)
            for connection_id in list(user_connections):
                await self.ws_manager.disconnect(connection_id)
            
            logger.info(f"Force disconnected user {user_id}: {len(user_connections)} connections")
            return len(user_connections)
            
        except Exception as e:
            logger.error(f"Error force disconnecting user {user_id}: {e}")
            return 0
    
    async def send_auth_notification(
        self, 
        user_id: int, 
        title: str, 
        message: str,
        level: str = "info"
    ) -> bool:
        """Envoyer une notification d'authentification à un utilisateur"""
        try:
            notification = WebSocketMessage(
                type="auth:notification",
                data={
                    "title": title,
                    "message": message,
                    "level": level,
                    "category": "authentication"
                }
            )
            
            sent_count = await self.ws_manager.send_to_user(user_id, notification)
            return sent_count > 0
            
        except Exception as e:
            logger.error(f"Error sending auth notification to user {user_id}: {e}")
            return False