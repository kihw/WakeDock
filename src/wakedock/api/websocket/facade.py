"""
WebSocket Facade

Façade unifiée pour maintenir la compatibilité avec l'ancien code WebSocket
tout en utilisant la nouvelle architecture modulaire.
"""

import logging
from typing import Optional, Dict, Any
from fastapi import WebSocket, APIRouter, WebSocketDisconnect

from wakedock.database.models import User
from .manager import WebSocketManager
from .auth import AuthWebSocketHandler
from .services import ServicesWebSocketHandler
from .system import SystemWebSocketHandler
from .notifications import NotificationsWebSocketHandler

logger = logging.getLogger(__name__)

# Instance globale du gestionnaire WebSocket
websocket_manager = WebSocketManager()

# Handlers spécialisés
auth_handler = AuthWebSocketHandler(websocket_manager)
services_handler = ServicesWebSocketHandler(websocket_manager)
system_handler = SystemWebSocketHandler(websocket_manager)
notifications_handler = NotificationsWebSocketHandler(websocket_manager)


async def get_websocket_user(websocket: WebSocket) -> Optional[User]:
    """Compatibilité - extraction utilisateur WebSocket"""
    return await auth_handler.get_websocket_user(websocket)


# Router WebSocket pour compatibilité
websocket_router = APIRouter()


@websocket_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket principal - compatibilité"""
    connection_id = None
    try:
        logger.info("New WebSocket connection attempt")
        
        # Authentifier l'utilisateur (optionnel)
        user = await get_websocket_user(websocket)
        if user:
            logger.info(f"WebSocket user authenticated: {user.username}")
        else:
            logger.info("WebSocket connection without authentication")
        
        # Établir la connexion (includes accept)
        connection_id = await websocket_manager.connect(websocket, user)
        
        if not connection_id:
            logger.error("Failed to establish WebSocket connection")
            return
        
        logger.info(f"WebSocket connection established with ID: {connection_id}")
        
        # Configurer les abonnements par défaut
        if user:
            await services_handler.handle_service_events(connection_id)
            await websocket_manager.subscribe(connection_id, "system:metrics")
            await websocket_manager.subscribe(connection_id, "notification")
        
        # Envoyer un message de bienvenue
        await websocket.send_text('{"type": "welcome", "data": {"message": "WebSocket connected successfully"}}')
        
        # Boucle de traitement des messages
        while True:
            try:
                data = await websocket.receive_text()
                await websocket_manager.handle_message(connection_id, data)
            except WebSocketDisconnect as e:
                # Normal disconnection - don't log as error
                if e.code == 1001:  # Going away (browser tab closing)
                    logger.info(f"WebSocket client disconnected normally (going away): {connection_id}")
                elif e.code == 1000:  # Normal closure
                    logger.info(f"WebSocket client disconnected normally: {connection_id}")
                else:
                    logger.warning(f"WebSocket disconnected with code {e.code}: {connection_id}")
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        if connection_id:
            await websocket_manager.disconnect(connection_id)
            # Nettoyer les streams
            await services_handler.cleanup_connection_streams(connection_id)
            await system_handler.cleanup_connection_streams(connection_id)
            logger.info(f"WebSocket connection {connection_id} cleaned up")


@websocket_router.websocket("/ws-test")
async def websocket_test_endpoint(websocket: WebSocket):
    """Endpoint WebSocket de test simple"""
    try:
        await websocket.accept()
        logger.info("WebSocket test connection accepted")
        
        # Envoyer un message de test
        await websocket.send_text('{"type": "test", "data": {"message": "WebSocket test connection successful"}}')
        
        # Boucle simple pour maintenir la connexion
        while True:
            try:
                data = await websocket.receive_text()
                # Echo du message reçu
                await websocket.send_text(f'{{"type": "echo", "data": {data}}}')
            except WebSocketDisconnect:
                logger.info("WebSocket test connection closed")
                break
            except Exception as e:
                logger.error(f"Error in WebSocket test: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket test connection error: {e}")


# Fonctions de compatibilité pour main.py
async def handle_docker_event(event: dict):
    """Gestionnaire d'événements Docker - compatibilité"""
    try:
        await services_handler.handle_docker_event(event)
    except Exception as e:
        logger.error(f"Error handling Docker event: {e}")


async def broadcast_system_update(data: dict):
    """Diffusion mise à jour système - compatibilité"""
    try:
        await system_handler.broadcast_system_status_change(
            status=data.get('status', 'unknown'),
            details=data
        )
    except Exception as e:
        logger.error(f"Error broadcasting system update: {e}")


async def broadcast_log_entry(log_entry: dict):
    """Diffusion entrée log - compatibilité"""
    try:
        ws_message = {
            'type': 'log:entry',
            'data': log_entry
        }
        await websocket_manager.broadcast_to_all(ws_message)
    except Exception as e:
        logger.error(f"Error broadcasting log entry: {e}")


async def broadcast_notification(notification: dict):
    """Diffusion notification - compatibilité"""
    try:
        await notifications_handler.send_notification(
            user_id=notification.get('user_id'),
            title=notification.get('title', 'Notification'),
            message=notification.get('message', ''),
            level=notification.get('level', 'info'),
            data=notification.get('data')
        )
    except Exception as e:
        logger.error(f"Error broadcasting notification: {e}")


async def websocket_ping_task():
    """Tâche de ping WebSocket pour maintenir les connexions actives"""
    try:
        import asyncio
        while True:
            await asyncio.sleep(30)  # Ping toutes les 30 secondes
            await websocket_manager.ping_all_connections()
    except Exception as e:
        logger.error(f"Error in WebSocket ping task: {e}")


# Exports pour compatibilité
__all__ = [
    'websocket_manager',
    'auth_handler',
    'services_handler', 
    'system_handler',
    'notifications_handler',
    'get_websocket_user',
    'websocket_router',
    'handle_docker_event',
    'broadcast_system_update',
    'broadcast_log_entry',
    'broadcast_notification',
    'websocket_ping_task'
]