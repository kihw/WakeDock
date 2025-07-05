"""
System WebSocket Handler

Streaming métriques système en temps réel.
"""

import asyncio
import logging
import psutil
from typing import Dict, Any
from datetime import datetime

from .types import WebSocketMessage, SystemMetrics, EventType

logger = logging.getLogger(__name__)


class SystemWebSocketHandler:
    """Gestionnaire WebSocket pour les métriques système"""
    
    def __init__(self, websocket_manager):
        """Initialiser le handler système"""
        self.ws_manager = websocket_manager
        self.system_streams: Dict[str, asyncio.Task] = {}  # connection_id -> task
        self.docker_event_streams: Dict[str, asyncio.Task] = {}
    
    async def start_system_metrics_stream(self, connection_id: str, interval: int = 5) -> bool:
        """Démarrer le streaming des métriques système"""
        try:
            # Arrêter le stream existant
            await self.stop_system_metrics_stream(connection_id)
            
            # Créer nouvelle tâche
            stream_task = asyncio.create_task(
                self._stream_system_metrics(connection_id, interval)
            )
            
            self.system_streams[connection_id] = stream_task
            
            logger.info(f"Started system metrics stream for connection {connection_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting system metrics stream: {e}")
            return False
    
    async def stop_system_metrics_stream(self, connection_id: str) -> bool:
        """Arrêter le streaming des métriques système"""
        try:
            if connection_id in self.system_streams:
                task = self.system_streams[connection_id]
                if not task.done():
                    task.cancel()
                del self.system_streams[connection_id]
                return True
            return False
        except Exception as e:
            logger.error(f"Error stopping system metrics stream: {e}")
            return False
    
    async def start_docker_events_stream(self, connection_id: str) -> bool:
        """Démarrer le streaming des événements Docker"""
        try:
            await self.stop_docker_events_stream(connection_id)
            
            stream_task = asyncio.create_task(
                self._stream_docker_events(connection_id)
            )
            
            self.docker_event_streams[connection_id] = stream_task
            
            logger.info(f"Started Docker events stream for connection {connection_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting Docker events stream: {e}")
            return False
    
    async def stop_docker_events_stream(self, connection_id: str) -> bool:
        """Arrêter le streaming des événements Docker"""
        try:
            if connection_id in self.docker_event_streams:
                task = self.docker_event_streams[connection_id]
                if not task.done():
                    task.cancel()
                del self.docker_event_streams[connection_id]
                return True
            return False
        except Exception as e:
            logger.error(f"Error stopping Docker events stream: {e}")
            return False
    
    async def _stream_system_metrics(self, connection_id: str, interval: int) -> None:
        """Stream continu des métriques système"""
        try:
            while True:
                # Collecter métriques système
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                network = psutil.net_io_counters()
                
                # TODO: Récupérer le nombre de conteneurs actifs depuis Docker
                active_containers = 0
                
                metrics = SystemMetrics(
                    cpu_usage=cpu_percent,
                    memory_usage=memory.percent,
                    disk_usage=(disk.used / disk.total) * 100,
                    network_io={
                        "bytes_sent": network.bytes_sent,
                        "bytes_recv": network.bytes_recv,
                        "packets_sent": network.packets_sent,
                        "packets_recv": network.packets_recv
                    },
                    active_containers=active_containers
                )
                
                message = WebSocketMessage(
                    type=EventType.SYSTEM_METRICS.value,
                    data=metrics.dict()
                )
                
                success = await self.ws_manager.send_to_connection(connection_id, message)
                if not success:
                    break
                
                await asyncio.sleep(interval)
                
        except asyncio.CancelledError:
            logger.debug(f"System metrics stream cancelled for {connection_id}")
        except Exception as e:
            logger.error(f"Error in system metrics stream: {e}")
    
    async def _stream_docker_events(self, connection_id: str) -> None:
        """Stream continu des événements Docker"""
        try:
            # TODO: Intégrer avec Docker API pour événements temps réel
            # Simulation pour l'instant
            import random
            
            event_types = ["container:start", "container:stop", "image:pull"]
            
            while True:
                # Simuler un événement Docker
                event_data = {
                    "type": random.choice(event_types),
                    "container_id": f"container_{random.randint(1, 10)}",
                    "image": "nginx:latest",
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "success"
                }
                
                message = WebSocketMessage(
                    type="docker:event",
                    data=event_data
                )
                
                success = await self.ws_manager.send_to_connection(connection_id, message)
                if not success:
                    break
                
                await asyncio.sleep(random.randint(5, 15))  # Événement aléatoire
                
        except asyncio.CancelledError:
            logger.debug(f"Docker events stream cancelled for {connection_id}")
        except Exception as e:
            logger.error(f"Error in Docker events stream: {e}")
    
    async def broadcast_system_status_change(self, status: str, details: Dict[str, Any]) -> None:
        """Diffuser un changement de statut système"""
        try:
            message = WebSocketMessage(
                type=EventType.SYSTEM_STATUS.value,
                data={
                    "status": status,
                    "details": details,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            sent_count = await self.ws_manager.broadcast_to_subscribers(
                EventType.SYSTEM_STATUS.value,
                message
            )
            
            logger.info(f"Broadcasted system status change to {sent_count} subscribers")
            
        except Exception as e:
            logger.error(f"Error broadcasting system status change: {e}")
    
    async def cleanup_connection_streams(self, connection_id: str) -> None:
        """Nettoyer tous les streams d'une connexion"""
        try:
            await self.stop_system_metrics_stream(connection_id)
            await self.stop_docker_events_stream(connection_id)
            
            logger.info(f"Cleaned up system streams for connection {connection_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up system streams: {e}")