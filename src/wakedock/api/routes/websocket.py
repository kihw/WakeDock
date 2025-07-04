"""
WebSocket Routes for Real-time Communication
Provides real-time updates for services, system metrics, logs, and notifications
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field

from wakedock.api.auth.dependencies import get_current_user_optional
from wakedock.api.auth.jwt import jwt_manager
from wakedock.database.models import User

logger = logging.getLogger(__name__)

async def get_websocket_user(websocket: WebSocket) -> Optional[User]:
    """
    Extract user from WebSocket connection via token parameter
    Checks for token in query parameters or headers
    """
    try:
        # Try to get token from query parameters first
        token = None
        if hasattr(websocket, 'query_params'):
            token = websocket.query_params.get('token')
        
        # If no token in query params, try headers
        if not token and hasattr(websocket, 'headers'):
            auth_header = websocket.headers.get('authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header[7:]
        
        if not token:
            logger.debug("No token found in WebSocket connection")
            return None
            
        # Verify token and get user
        token_data = await jwt_manager.verify_token(token)
        if not token_data:
            logger.debug("Invalid token in WebSocket connection")
            return None
            
        # Get user from database (we'll need to implement this part)
        # For now, create a simple user object from token data
        user = User(
            id=int(token_data.get('sub', 0)),
            username=token_data.get('username', 'unknown'),
            email=token_data.get('email', ''),
            role=token_data.get('role', 'user'),
            is_active=True,
            is_verified=True
        )
        
        return user
        
    except Exception as e:
        logger.error(f"Error authenticating WebSocket user: {e}")
        return None

# Pydantic models for WebSocket messages
class WebSocketMessage(BaseModel):
    type: str = Field(..., description="Message type")
    data: Any = Field(..., description="Message data")
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.utcnow().isoformat())
    sequence: Optional[int] = Field(default=None, description="Message sequence number")

class SubscriptionRequest(BaseModel):
    event_type: str = Field(..., description="Event type to subscribe to")

class WebSocketError(BaseModel):
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")

# WebSocket Manager for handling multiple connections
class WebSocketManager:
    def __init__(self):
        # Active WebSocket connections
        self.active_connections: List[WebSocket] = []
        
        # Subscriptions mapping: event_type -> set of websockets
        self.subscriptions: Dict[str, Set[WebSocket]] = {}
        
        # User mapping for websockets (for authentication)
        self.user_connections: Dict[WebSocket, User] = {}
        
        # Message sequence counter
        self.sequence_counter: int = 0
        
        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, user: Optional[User] = None) -> None:
        """Accept a new WebSocket connection"""
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            
            if user:
                self.user_connections[websocket] = user
                
            # Initialize metadata
            self.connection_metadata[websocket] = {
                'connected_at': datetime.utcnow(),
                'last_ping': datetime.utcnow(),
                'messages_sent': 0,
                'messages_received': 0,
                'user_id': user.id if user else None,
                'subscriptions': set()
            }
            
            logger.info(f"WebSocket connection established. User: {user.username if user else 'Anonymous'}")
            
            # Send welcome message
            await self.send_personal_message(websocket, {
                'type': 'connection_established',
                'data': {
                    'message': 'Connected to WakeDock WebSocket',
                    'server_time': datetime.utcnow().isoformat(),
                    'user': user.username if user else None
                }
            })
            
        except Exception as e:
            logger.error(f"Error establishing WebSocket connection: {e}")
            raise

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection"""
        try:
            # Remove from active connections
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
            
            # Remove from user mapping
            if websocket in self.user_connections:
                user = self.user_connections.pop(websocket)
                logger.info(f"WebSocket disconnected for user: {user.username}")
            
            # Remove from all subscriptions
            for event_type, subscribers in self.subscriptions.items():
                subscribers.discard(websocket)
            
            # Clean up metadata
            if websocket in self.connection_metadata:
                metadata = self.connection_metadata.pop(websocket)
                logger.debug(f"Connection metadata: {metadata}")
                
        except Exception as e:
            logger.error(f"Error during WebSocket disconnect: {e}")

    async def subscribe(self, websocket: WebSocket, event_type: str) -> bool:
        """Subscribe a WebSocket to specific event types"""
        try:
            if websocket not in self.active_connections:
                logger.warning("Attempted to subscribe inactive WebSocket")
                return False
                
            if event_type not in self.subscriptions:
                self.subscriptions[event_type] = set()
            
            self.subscriptions[event_type].add(websocket)
            
            # Update metadata
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]['subscriptions'].add(event_type)
            
            logger.debug(f"WebSocket subscribed to {event_type}")
            
            # Send confirmation
            await self.send_personal_message(websocket, {
                'type': 'subscription_confirmed',
                'data': {
                    'event_type': event_type,
                    'message': f'Subscribed to {event_type} events'
                }
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error subscribing to {event_type}: {e}")
            return False

    async def unsubscribe(self, websocket: WebSocket, event_type: str) -> bool:
        """Unsubscribe a WebSocket from specific event types"""
        try:
            if event_type in self.subscriptions:
                self.subscriptions[event_type].discard(websocket)
                
                # Update metadata
                if websocket in self.connection_metadata:
                    self.connection_metadata[websocket]['subscriptions'].discard(event_type)
                
                logger.debug(f"WebSocket unsubscribed from {event_type}")
                
                # Send confirmation
                await self.send_personal_message(websocket, {
                    'type': 'unsubscription_confirmed',
                    'data': {
                        'event_type': event_type,
                        'message': f'Unsubscribed from {event_type} events'
                    }
                })
                
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error unsubscribing from {event_type}: {e}")
            return False

    async def send_personal_message(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Send a message to a specific WebSocket connection"""
        try:
            if websocket in self.active_connections:
                # Add sequence number
                self.sequence_counter += 1
                message['sequence'] = self.sequence_counter
                
                # Ensure timestamp
                if 'timestamp' not in message:
                    message['timestamp'] = datetime.utcnow().isoformat()
                
                await websocket.send_text(json.dumps(message))
                
                # Update metadata
                if websocket in self.connection_metadata:
                    self.connection_metadata[websocket]['messages_sent'] += 1
                    
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            await self.disconnect(websocket)

    async def broadcast(self, message: Dict[str, Any], event_type: Optional[str] = None) -> int:
        """Broadcast a message to all subscribers of an event type"""
        sent_count = 0
        
        try:
            # Add sequence number and timestamp
            self.sequence_counter += 1
            message['sequence'] = self.sequence_counter
            
            if 'timestamp' not in message:
                message['timestamp'] = datetime.utcnow().isoformat()
            
            message_json = json.dumps(message)
            
            # Determine target connections
            if event_type and event_type in self.subscriptions:
                target_connections = self.subscriptions[event_type].copy()
            else:
                target_connections = set(self.active_connections)
            
            # Send to all target connections
            for websocket in target_connections:
                try:
                    if websocket in self.active_connections:
                        await websocket.send_text(message_json)
                        sent_count += 1
                        
                        # Update metadata
                        if websocket in self.connection_metadata:
                            self.connection_metadata[websocket]['messages_sent'] += 1
                            
                except Exception as e:
                    logger.error(f"Error sending broadcast message: {e}")
                    await self.disconnect(websocket)
            
            if sent_count > 0:
                logger.debug(f"Broadcast message sent to {sent_count} connections for event: {event_type}")
                
        except Exception as e:
            logger.error(f"Error broadcasting message: {e}")
        
        return sent_count

    async def ping_all(self) -> int:
        """Send ping to all active connections"""
        ping_message = {
            'type': 'ping',
            'data': {
                'server_time': datetime.utcnow().isoformat()
            }
        }
        
        return await self.broadcast(ping_message)

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about current connections"""
        stats = {
            'total_connections': len(self.active_connections),
            'subscriptions': {
                event_type: len(subscribers) 
                for event_type, subscribers in self.subscriptions.items()
            },
            'authenticated_connections': len(self.user_connections),
            'anonymous_connections': len(self.active_connections) - len(self.user_connections),
            'total_messages_sent': self.sequence_counter,
            'uptime_seconds': 0  # Will be calculated by caller
        }
        
        return stats

# Global WebSocket manager instance
websocket_manager = WebSocketManager()

# Router for WebSocket endpoints
router = APIRouter(prefix="/ws", tags=["WebSocket"])

@router.websocket("")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for real-time communication
    Handles connection, authentication, subscriptions, and message routing
    """
    # Try to authenticate user (optional for WebSocket)
    user = None
    try:
        user = await get_websocket_user(websocket)
    except Exception as e:
        logger.debug(f"WebSocket authentication failed: {e}")
    
    # Accept the connection
    await websocket_manager.connect(websocket, user)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await handle_websocket_message(websocket, message)
                
                # Update metadata
                if websocket in websocket_manager.connection_metadata:
                    websocket_manager.connection_metadata[websocket]['messages_received'] += 1
                    websocket_manager.connection_metadata[websocket]['last_ping'] = datetime.utcnow()
                
            except json.JSONDecodeError:
                await websocket_manager.send_personal_message(websocket, {
                    'type': 'error',
                    'data': {
                        'error': 'Invalid JSON format',
                        'code': 'INVALID_JSON'
                    }
                })
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await websocket_manager.send_personal_message(websocket, {
                    'type': 'error',
                    'data': {
                        'error': str(e),
                        'code': 'MESSAGE_HANDLING_ERROR'
                    }
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket_manager.disconnect(websocket)

async def handle_websocket_message(websocket: WebSocket, message: Dict[str, Any]) -> None:
    """Handle incoming WebSocket messages from clients"""
    try:
        message_type = message.get('type', '')
        data = message.get('data', {})
        
        if message_type == 'ping':
            # Respond to ping with pong
            await websocket_manager.send_personal_message(websocket, {
                'type': 'pong',
                'data': {
                    'server_time': datetime.utcnow().isoformat()
                }
            })
            
        elif message_type == 'subscribe':
            # Subscribe to event type
            event_type = data.get('event_type', '')
            if event_type:
                await websocket_manager.subscribe(websocket, event_type)
            else:
                await websocket_manager.send_personal_message(websocket, {
                    'type': 'error',
                    'data': {
                        'error': 'Missing event_type for subscription',
                        'code': 'MISSING_EVENT_TYPE'
                    }
                })
                
        elif message_type == 'unsubscribe':
            # Unsubscribe from event type
            event_type = data.get('event_type', '')
            if event_type:
                await websocket_manager.unsubscribe(websocket, event_type)
            else:
                await websocket_manager.send_personal_message(websocket, {
                    'type': 'error',
                    'data': {
                        'error': 'Missing event_type for unsubscription',
                        'code': 'MISSING_EVENT_TYPE'
                    }
                })
                
        elif message_type == 'get_stats':
            # Send connection statistics
            stats = websocket_manager.get_connection_stats()
            await websocket_manager.send_personal_message(websocket, {
                'type': 'stats',
                'data': stats
            })
            
        else:
            # Unknown message type
            await websocket_manager.send_personal_message(websocket, {
                'type': 'error',
                'data': {
                    'error': f'Unknown message type: {message_type}',
                    'code': 'UNKNOWN_MESSAGE_TYPE'
                }
            })
            
    except Exception as e:
        logger.error(f"Error in handle_websocket_message: {e}")
        await websocket_manager.send_personal_message(websocket, {
            'type': 'error',
            'data': {
                'error': 'Internal server error',
                'code': 'INTERNAL_ERROR'
            }
        })

# Utility functions for other modules to broadcast events
async def broadcast_service_update(service_data: Dict[str, Any]) -> int:
    """Broadcast service update to all subscribers"""
    message = {
        'type': 'service_update',
        'data': service_data
    }
    return await websocket_manager.broadcast(message, 'service_updates')

async def broadcast_system_update(system_data: Dict[str, Any]) -> int:
    """Broadcast system update to all subscribers"""
    message = {
        'type': 'system_update',
        'data': system_data
    }
    return await websocket_manager.broadcast(message, 'system_updates')

async def broadcast_log_entry(log_data: Dict[str, Any]) -> int:
    """Broadcast log entry to all subscribers"""
    message = {
        'type': 'log_entry',
        'data': log_data
    }
    return await websocket_manager.broadcast(message, 'log_entries')

async def broadcast_notification(notification_data: Dict[str, Any]) -> int:
    """Broadcast notification to all subscribers"""
    message = {
        'type': 'notification',
        'data': notification_data
    }
    return await websocket_manager.broadcast(message, 'notifications')

# Docker events integration
async def handle_docker_event(event_data: Dict[str, Any]) -> None:
    """Handle Docker events and broadcast to subscribers"""
    try:
        # Broadcast Docker event as service update
        await broadcast_service_update(event_data)
        logger.debug(f"Broadcasted Docker event: {event_data.get('action')} for {event_data.get('name')}")
    except Exception as e:
        logger.error(f"Error handling Docker event: {e}")

# Background task for periodic pings
async def websocket_ping_task():
    """Background task to ping all WebSocket connections periodically"""
    while True:
        try:
            if websocket_manager.active_connections:
                ping_count = await websocket_manager.ping_all()
                logger.debug(f"Sent ping to {ping_count} WebSocket connections")
            
            # Wait 30 seconds before next ping
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"Error in WebSocket ping task: {e}")
            await asyncio.sleep(30)

# Export manager for use in other modules
__all__ = [
    'router',
    'websocket_manager',
    'broadcast_service_update',
    'broadcast_system_update', 
    'broadcast_log_entry',
    'broadcast_notification',
    'websocket_ping_task',
    'handle_docker_event'
]