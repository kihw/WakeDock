"""
WebSocket Connection Manager

Gestionnaire centralisé des connexions WebSocket.
Extrait de la classe monolithique WebSocketManager.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect

from wakedock.database.models import User
from .types import (
    WebSocketMessage, ConnectionInfo, ConnectionStatus, 
    EventType, SubscriptionRequest, WebSocketError
)
from .batch_manager import batch_manager, WebSocketMessage as BatchWebSocketMessage, MessagePriority

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Gestionnaire centralisé des connexions WebSocket"""
    
    def __init__(self):
        """Initialiser le gestionnaire"""
        self.connections: Dict[str, WebSocket] = {}
        self.connection_info: Dict[str, ConnectionInfo] = {}
        self.connection_users: Dict[str, Optional[User]] = {}  # connection_id -> User
        self.user_connections: Dict[int, Set[str]] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # event_type -> connection_ids
        
        # Configuration
        self.max_connections_per_user = 10
        self.ping_interval = 30  # seconds
        self.connection_timeout = 300  # 5 minutes
        
        # Métriques
        self.total_connections = 0
        self.total_messages_sent = 0
        self.total_messages_received = 0
        
        # Task de nettoyage périodique
        self._cleanup_task = None
        
        # Initialize batch manager
        batch_manager.set_websocket_manager(self)
    
    async def connect(
        self, 
        websocket: WebSocket, 
        user: Optional[User] = None,
        connection_id: Optional[str] = None
    ) -> str:
        """Établir une nouvelle connexion WebSocket"""
        
        if connection_id is None:
            connection_id = str(uuid.uuid4())
        
        try:
            # Accepter la connexion
            await websocket.accept()
            
            # Vérifier les limites par utilisateur
            if user and not await self._check_user_connection_limit(user.id):
                await self._send_error(
                    websocket,
                    "CONNECTION_LIMIT_EXCEEDED",
                    f"Maximum {self.max_connections_per_user} connections per user"
                )
                await websocket.close()
                return ""
            
            # Enregistrer la connexion
            self.connections[connection_id] = websocket
            
            # Créer les informations de connexion
            conn_info = ConnectionInfo(
                connection_id=connection_id,
                user_id=user.id if user else None,
                username=user.username if user else None,
                connected_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                ip_address=self._get_client_ip(websocket),
                user_agent=self._get_user_agent(websocket)
            )
            
            self.connection_info[connection_id] = conn_info
            self.connection_users[connection_id] = user
            
            # Associer à l'utilisateur
            if user:
                if user.id not in self.user_connections:
                    self.user_connections[user.id] = set()
                self.user_connections[user.id].add(connection_id)
            
            # Métriques
            self.total_connections += 1
            
            # Envoyer message de bienvenue
            await self._send_welcome_message(websocket, connection_id, user)
            
            # Démarrer le ping si c'est la première connexion
            if len(self.connections) == 1:
                await self._start_ping_task()
            
            logger.info(f"WebSocket connected: {connection_id} (user: {user.id if user else 'anonymous'})")
            return connection_id
            
        except Exception as e:
            logger.error(f"Error connecting WebSocket: {e}")
            if connection_id in self.connections:
                del self.connections[connection_id]
            raise
    
    async def disconnect(self, connection_id: str) -> None:
        """Fermer une connexion WebSocket"""
        try:
            # Récupérer les infos de connexion
            conn_info = self.connection_info.get(connection_id)
            
            # Nettoyer les abonnements
            await self._cleanup_subscriptions(connection_id)
            
            # Retirer de la liste des connexions utilisateur
            if conn_info and conn_info.user_id:
                user_conns = self.user_connections.get(conn_info.user_id)
                if user_conns:
                    user_conns.discard(connection_id)
                    if not user_conns:
                        del self.user_connections[conn_info.user_id]
            
            # Supprimer la connexion
            if connection_id in self.connections:
                del self.connections[connection_id]
            
            if connection_id in self.connection_info:
                del self.connection_info[connection_id]
                
            if connection_id in self.connection_users:
                del self.connection_users[connection_id]
            
            logger.info(f"WebSocket disconnected: {connection_id}")
            
            # Arrêter le ping s'il n'y a plus de connexions
            if not self.connections and self._cleanup_task:
                self._cleanup_task.cancel()
                self._cleanup_task = None
                
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket {connection_id}: {e}")
    
    async def send_to_connection(
        self, 
        connection_id: str, 
        message: str | WebSocketMessage,
        priority: MessagePriority = MessagePriority.NORMAL,
        use_batching: bool = True
    ) -> bool:
        """Envoyer un message à une connexion spécifique"""
        try:
            websocket = self.connections.get(connection_id)
            if not websocket:
                return False
            
            # Handle string messages (from batch manager)
            if isinstance(message, str):
                await websocket.send_text(message)
                self.total_messages_sent += 1
                return True
            
            # Mettre à jour l'activité
            conn_info = self.connection_info.get(connection_id)
            if conn_info:
                conn_info.last_activity = datetime.utcnow()
            
            # Convert to batch message format
            batch_message = BatchWebSocketMessage(
                type=message.type,
                data=message.data,
                priority=priority
            )
            
            # Use batching for non-critical messages
            if use_batching and priority != MessagePriority.CRITICAL:
                await batch_manager.queue_message(connection_id, batch_message)
            else:
                # Send immediately for critical messages
                await batch_manager.send_immediate(connection_id, batch_message)
            
            return True
            
        except WebSocketDisconnect:
            logger.info(f"WebSocket {connection_id} disconnected during send")
            await self.disconnect(connection_id)
            return False
        except Exception as e:
            logger.error(f"Error sending message to {connection_id}: {e}")
            return False
    
    async def send_to_user(
        self, 
        user_id: int, 
        message: WebSocketMessage
    ) -> int:
        """Envoyer un message à toutes les connexions d'un utilisateur"""
        sent_count = 0
        user_connections = self.user_connections.get(user_id, set())
        
        for connection_id in list(user_connections):  # Copy to avoid modification during iteration
            if await self.send_to_connection(connection_id, message):
                sent_count += 1
        
        return sent_count
    
    async def broadcast_to_all(self, message: WebSocketMessage) -> int:
        """Diffuser un message à toutes les connexions"""
        sent_count = 0
        
        for connection_id in list(self.connections.keys()):
            if await self.send_to_connection(connection_id, message):
                sent_count += 1
        
        logger.debug(f"Broadcasted message to {sent_count} connections")
        return sent_count
    
    async def broadcast_to_subscribers(
        self, 
        event_type: str, 
        message: WebSocketMessage,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> int:
        """Diffuser à tous les abonnés d'un type d'événement"""
        sent_count = 0
        subscribers = self.subscriptions.get(event_type, set())
        
        for connection_id in list(subscribers):
            if await self.send_to_connection(connection_id, message, priority=priority):
                sent_count += 1
        
        logger.debug(f"Sent {event_type} message to {sent_count} subscribers")
        return sent_count
    
    async def send_high_priority(
        self, 
        connection_id: str, 
        message: WebSocketMessage
    ) -> bool:
        """Send a high priority message (bypasses normal batching)"""
        return await self.send_to_connection(
            connection_id, 
            message, 
            priority=MessagePriority.HIGH,
            use_batching=False
        )
    
    async def send_critical(
        self, 
        connection_id: str, 
        message: WebSocketMessage
    ) -> bool:
        """Send a critical message (immediate, no batching)"""
        return await self.send_to_connection(
            connection_id, 
            message, 
            priority=MessagePriority.CRITICAL,
            use_batching=False
        )
    
    async def flush_all_batches(self) -> None:
        """Flush all pending batched messages"""
        await batch_manager.flush_all_connections()
    
    def get_batching_stats(self) -> Dict[str, Any]:
        """Get batching statistics"""
        return batch_manager.get_stats()
    
    def get_connection_user(self, connection_id: str) -> Optional[User]:
        """Récupérer l'utilisateur associé à une connexion"""
        return self.connection_users.get(connection_id)
    
    async def subscribe(
        self, 
        connection_id: str, 
        event_type: str
    ) -> bool:
        """Abonner une connexion à un type d'événement"""
        try:
            # Vérifier que la connexion existe
            if connection_id not in self.connections:
                return False
            
            # Ajouter l'abonnement
            if event_type not in self.subscriptions:
                self.subscriptions[event_type] = set()
            
            self.subscriptions[event_type].add(connection_id)
            
            # Mettre à jour les infos de connexion
            conn_info = self.connection_info.get(connection_id)
            if conn_info:
                conn_info.subscriptions.add(event_type)
            
            logger.debug(f"Connection {connection_id} subscribed to {event_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error subscribing {connection_id} to {event_type}: {e}")
            return False
    
    async def unsubscribe(
        self, 
        connection_id: str, 
        event_type: str
    ) -> bool:
        """Désabonner une connexion d'un type d'événement"""
        try:
            # Retirer de la liste d'abonnement
            if event_type in self.subscriptions:
                self.subscriptions[event_type].discard(connection_id)
                
                # Nettoyer si plus d'abonnés
                if not self.subscriptions[event_type]:
                    del self.subscriptions[event_type]
            
            # Mettre à jour les infos de connexion
            conn_info = self.connection_info.get(connection_id)
            if conn_info:
                conn_info.subscriptions.discard(event_type)
            
            logger.debug(f"Connection {connection_id} unsubscribed from {event_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error unsubscribing {connection_id} from {event_type}: {e}")
            return False
    
    async def handle_message(
        self, 
        connection_id: str, 
        message: str
    ) -> None:
        """Traiter un message reçu d'une connexion"""
        try:
            self.total_messages_received += 1
            
            # Parser le message JSON
            data = json.loads(message)
            
            # Mettre à jour l'activité
            conn_info = self.connection_info.get(connection_id)
            if conn_info:
                conn_info.last_activity = datetime.utcnow()
            
            # Traiter selon le type de message
            message_type = data.get("type")
            
            if message_type == EventType.SUBSCRIBE.value:
                await self._handle_subscribe(connection_id, data)
            elif message_type == EventType.UNSUBSCRIBE.value:
                await self._handle_unsubscribe(connection_id, data)
            elif message_type == EventType.PING.value:
                await self._handle_ping(connection_id)
            else:
                # Message non reconnu
                await self._send_error(
                    self.connections[connection_id],
                    "UNKNOWN_MESSAGE_TYPE",
                    f"Unknown message type: {message_type}"
                )
                
        except json.JSONDecodeError:
            await self._send_error(
                self.connections[connection_id],
                "INVALID_JSON",
                "Invalid JSON message"
            )
        except Exception as e:
            logger.error(f"Error handling message from {connection_id}: {e}")
            await self._send_error(
                self.connections[connection_id],
                "MESSAGE_PROCESSING_ERROR",
                str(e)
            )
    
    # === Méthodes privées ===
    
    async def _check_user_connection_limit(self, user_id: int) -> bool:
        """Vérifier la limite de connexions par utilisateur"""
        user_conns = self.user_connections.get(user_id, set())
        return len(user_conns) < self.max_connections_per_user
    
    def _get_client_ip(self, websocket: WebSocket) -> Optional[str]:
        """Extraire l'IP du client"""
        try:
            # Essayer d'obtenir l'IP depuis les headers
            forwarded_for = websocket.headers.get("x-forwarded-for")
            if forwarded_for:
                return forwarded_for.split(",")[0].strip()
            
            real_ip = websocket.headers.get("x-real-ip")
            if real_ip:
                return real_ip
            
            # Fallback vers l'IP de connexion directe
            if hasattr(websocket, 'client') and websocket.client:
                return websocket.client.host
                
        except Exception as e:
            logger.error(f"Error getting client IP: {e}")
        
        return None
    
    def _get_user_agent(self, websocket: WebSocket) -> Optional[str]:
        """Extraire le User-Agent"""
        try:
            return websocket.headers.get("user-agent")
        except:
            return None
    
    async def _send_welcome_message(
        self, 
        websocket: WebSocket, 
        connection_id: str,
        user: Optional[User]
    ) -> None:
        """Envoyer le message de bienvenue"""
        welcome_msg = WebSocketMessage(
            type="connection:established",
            data={
                "connection_id": connection_id,
                "user": user.username if user else "anonymous",
                "server_time": datetime.utcnow().isoformat(),
                "available_events": [event.value for event in EventType]
            }
        )
        
        await websocket.send_text(welcome_msg.json())
    
    async def _send_error(
        self, 
        websocket: WebSocket, 
        code: str, 
        message: str
    ) -> None:
        """Envoyer un message d'erreur"""
        error_msg = WebSocketMessage(
            type=EventType.ERROR.value,
            data=WebSocketError(
                error=message,
                code=code
            ).dict()
        )
        
        try:
            await websocket.send_text(error_msg.json())
        except:
            pass  # Ignore si la connexion est fermée
    
    async def _handle_subscribe(self, connection_id: str, data: Dict) -> None:
        """Traiter une demande d'abonnement"""
        event_type = data.get("data", {}).get("event_type")
        if event_type:
            success = await self.subscribe(connection_id, event_type)
            
            response = WebSocketMessage(
                type="subscription:response",
                data={
                    "event_type": event_type,
                    "subscribed": success
                }
            )
            
            await self.send_to_connection(connection_id, response)
    
    async def _handle_unsubscribe(self, connection_id: str, data: Dict) -> None:
        """Traiter une demande de désabonnement"""
        event_type = data.get("data", {}).get("event_type")
        if event_type:
            success = await self.unsubscribe(connection_id, event_type)
            
            response = WebSocketMessage(
                type="unsubscription:response",
                data={
                    "event_type": event_type,
                    "unsubscribed": success
                }
            )
            
            await self.send_to_connection(connection_id, response)
    
    async def _handle_ping(self, connection_id: str) -> None:
        """Traiter un ping"""
        pong_msg = WebSocketMessage(
            type=EventType.PONG.value,
            data={"timestamp": datetime.utcnow().isoformat()}
        )
        
        await self.send_to_connection(connection_id, pong_msg)
    
    async def _cleanup_subscriptions(self, connection_id: str) -> None:
        """Nettoyer les abonnements d'une connexion"""
        conn_info = self.connection_info.get(connection_id)
        if conn_info:
            for event_type in list(conn_info.subscriptions):
                await self.unsubscribe(connection_id, event_type)
    
    async def _start_ping_task(self) -> None:
        """Démarrer la tâche de ping périodique"""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
    
    async def _periodic_cleanup(self) -> None:
        """Nettoyage périodique des connexions inactives"""
        while True:
            try:
                await asyncio.sleep(self.ping_interval)
                
                if not self.connections:
                    break
                
                # Ping toutes les connexions actives
                current_time = datetime.utcnow()
                
                for connection_id in list(self.connections.keys()):
                    conn_info = self.connection_info.get(connection_id)
                    
                    if conn_info:
                        # Vérifier le timeout
                        inactive_time = (current_time - conn_info.last_activity).total_seconds()
                        
                        if inactive_time > self.connection_timeout:
                            logger.info(f"Connection {connection_id} timed out")
                            await self.disconnect(connection_id)
                        else:
                            # Envoyer un ping
                            ping_msg = WebSocketMessage(
                                type=EventType.PING.value,
                                data={"timestamp": current_time.isoformat()}
                            )
                            
                            await self.send_to_connection(connection_id, ping_msg)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    # === Méthodes de monitoring ===
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Récupérer les statistiques de connexion"""
        return {
            "active_connections": len(self.connections),
            "total_connections": self.total_connections,
            "messages_sent": self.total_messages_sent,
            "messages_received": self.total_messages_received,
            "subscriptions": {
                event_type: len(subscribers)
                for event_type, subscribers in self.subscriptions.items()
            },
            "users_connected": len(self.user_connections)
        }
    
    def get_user_connections(self, user_id: int) -> List[str]:
        """Récupérer les connexions d'un utilisateur"""
        return list(self.user_connections.get(user_id, set()))
    
    def is_user_connected(self, user_id: int) -> bool:
        """Vérifier si un utilisateur est connecté"""
        return user_id in self.user_connections and bool(self.user_connections[user_id])
    
    async def ping_all_connections(self) -> int:
        """Ping toutes les connexions actives"""
        ping_count = 0
        current_time = datetime.utcnow()
        
        ping_msg = WebSocketMessage(
            type=EventType.PING.value,
            data={"timestamp": current_time.isoformat()}
        )
        
        for connection_id in list(self.connections.keys()):
            if await self.send_to_connection(connection_id, ping_msg):
                ping_count += 1
        
        logger.debug(f"Pinged {ping_count} connections")
        return ping_count