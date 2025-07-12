"""
Services WebSocket Handler

Real-time updates pour les services Docker.
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

from wakedock.database.models import Service, ServiceStatus
from .types import WebSocketMessage, ServiceEvent, LogEntry, EventType

logger = logging.getLogger(__name__)


class ServicesWebSocketHandler:
    """Gestionnaire WebSocket pour les événements de services"""
    
    def __init__(self, websocket_manager, orchestrator=None):
        """Initialiser le handler de services"""
        self.ws_manager = websocket_manager
        self.orchestrator = orchestrator
        self.log_streams: Dict[str, asyncio.Task] = {}  # service_id -> task
        self.metrics_streams: Dict[str, asyncio.Task] = {}  # service_id -> task
    
    async def handle_service_events(self, connection_id: str) -> None:
        """Gérer les événements de services pour une connexion"""
        try:
            # S'abonner aux événements de services
            await self.ws_manager.subscribe(connection_id, EventType.SERVICE_CREATED.value)
            await self.ws_manager.subscribe(connection_id, EventType.SERVICE_UPDATED.value)
            await self.ws_manager.subscribe(connection_id, EventType.SERVICE_DELETED.value)
            await self.ws_manager.subscribe(connection_id, EventType.SERVICE_STARTED.value)
            await self.ws_manager.subscribe(connection_id, EventType.SERVICE_STOPPED.value)
            
            logger.info(f"Connection {connection_id} subscribed to service events")
            
        except Exception as e:
            logger.error(f"Error handling service events for {connection_id}: {e}")
    
    async def broadcast_service_created(self, service: Service) -> None:
        """Diffuser l'événement de création de service"""
        try:
            service_event = ServiceEvent(
                service_id=str(service.id),
                service_name=service.name,
                event_type="created",
                data={
                    "service": {
                        "id": str(service.id),
                        "name": service.name,
                        "status": service.status.value if hasattr(service.status, 'value') else str(service.status),
                        "image": getattr(service, 'image', 'unknown'),
                        "created_at": service.created_at.isoformat() if hasattr(service, 'created_at') else datetime.utcnow().isoformat()
                    }
                }
            )
            
            message = WebSocketMessage(
                type=EventType.SERVICE_CREATED.value,
                data=service_event.dict()
            )
            
            sent_count = await self.ws_manager.broadcast_to_subscribers(
                EventType.SERVICE_CREATED.value, 
                message
            )
            
            logger.info(f"Broadcasted service created event for {service.name} to {sent_count} subscribers")
            
        except Exception as e:
            logger.error(f"Error broadcasting service created event: {e}")
    
    async def broadcast_service_updated(self, service: Service, changes: Dict[str, Any]) -> None:
        """Diffuser l'événement de mise à jour de service"""
        try:
            service_event = ServiceEvent(
                service_id=str(service.id),
                service_name=service.name,
                event_type="updated",
                data={
                    "service": {
                        "id": str(service.id),
                        "name": service.name,
                        "status": service.status.value if hasattr(service.status, 'value') else str(service.status),
                        "updated_at": datetime.utcnow().isoformat()
                    },
                    "changes": changes
                }
            )
            
            message = WebSocketMessage(
                type=EventType.SERVICE_UPDATED.value,
                data=service_event.dict()
            )
            
            sent_count = await self.ws_manager.broadcast_to_subscribers(
                EventType.SERVICE_UPDATED.value,
                message
            )
            
            logger.info(f"Broadcasted service updated event for {service.name} to {sent_count} subscribers")
            
        except Exception as e:
            logger.error(f"Error broadcasting service updated event: {e}")
    
    async def broadcast_service_deleted(self, service_id: str, service_name: str) -> None:
        """Diffuser l'événement de suppression de service"""
        try:
            service_event = ServiceEvent(
                service_id=service_id,
                service_name=service_name,
                event_type="deleted",
                data={
                    "service_id": service_id,
                    "service_name": service_name,
                    "deleted_at": datetime.utcnow().isoformat()
                }
            )
            
            message = WebSocketMessage(
                type=EventType.SERVICE_DELETED.value,
                data=service_event.dict()
            )
            
            sent_count = await self.ws_manager.broadcast_to_subscribers(
                EventType.SERVICE_DELETED.value,
                message
            )
            
            # Arrêter les streams pour ce service
            await self._stop_service_streams(service_id)
            
            logger.info(f"Broadcasted service deleted event for {service_name} to {sent_count} subscribers")
            
        except Exception as e:
            logger.error(f"Error broadcasting service deleted event: {e}")
    
    async def broadcast_service_status_change(
        self, 
        service: Service, 
        old_status: ServiceStatus,
        new_status: ServiceStatus
    ) -> None:
        """Diffuser le changement de statut d'un service"""
        try:
            event_type_map = {
                ServiceStatus.RUNNING: EventType.SERVICE_STARTED.value,
                ServiceStatus.STOPPED: EventType.SERVICE_STOPPED.value
            }
            
            event_type = event_type_map.get(new_status, EventType.SERVICE_UPDATED.value)
            
            service_event = ServiceEvent(
                service_id=str(service.id),
                service_name=service.name,
                event_type="status_changed",
                data={
                    "service": {
                        "id": str(service.id),
                        "name": service.name,
                        "status": new_status.value if hasattr(new_status, 'value') else str(new_status)
                    },
                    "old_status": old_status.value if hasattr(old_status, 'value') else str(old_status),
                    "new_status": new_status.value if hasattr(new_status, 'value') else str(new_status),
                    "changed_at": datetime.utcnow().isoformat()
                }
            )
            
            message = WebSocketMessage(
                type=event_type,
                data=service_event.dict()
            )
            
            sent_count = await self.ws_manager.broadcast_to_subscribers(event_type, message)
            
            logger.info(f"Broadcasted status change for {service.name} "
                       f"({old_status} -> {new_status}) to {sent_count} subscribers")
            
        except Exception as e:
            logger.error(f"Error broadcasting service status change: {e}")
    
    async def start_log_stream(self, connection_id: str, service_id: str, lines: int = 100) -> bool:
        """Démarrer le streaming des logs d'un service"""
        try:
            # Arrêter le stream existant s'il y en a un
            await self.stop_log_stream(connection_id, service_id)
            
            # Créer une nouvelle tâche de streaming
            stream_task = asyncio.create_task(
                self._stream_service_logs(connection_id, service_id, lines)
            )
            
            stream_key = f"{connection_id}:{service_id}"
            self.log_streams[stream_key] = stream_task
            
            logger.info(f"Started log stream for service {service_id} to connection {connection_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting log stream for service {service_id}: {e}")
            return False
    
    async def stop_log_stream(self, connection_id: str, service_id: str) -> bool:
        """Arrêter le streaming des logs d'un service"""
        try:
            stream_key = f"{connection_id}:{service_id}"
            
            if stream_key in self.log_streams:
                task = self.log_streams[stream_key]
                if not task.done():
                    task.cancel()
                
                del self.log_streams[stream_key]
                
                logger.info(f"Stopped log stream for service {service_id} to connection {connection_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error stopping log stream for service {service_id}: {e}")
            return False
    
    async def start_metrics_stream(self, connection_id: str, service_id: str, interval: int = 5) -> bool:
        """Démarrer le streaming des métriques d'un service"""
        try:
            # Arrêter le stream existant s'il y en a un
            await self.stop_metrics_stream(connection_id, service_id)
            
            # Créer une nouvelle tâche de streaming
            stream_task = asyncio.create_task(
                self._stream_service_metrics(connection_id, service_id, interval)
            )
            
            stream_key = f"{connection_id}:{service_id}"
            self.metrics_streams[stream_key] = stream_task
            
            logger.info(f"Started metrics stream for service {service_id} to connection {connection_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting metrics stream for service {service_id}: {e}")
            return False
    
    async def stop_metrics_stream(self, connection_id: str, service_id: str) -> bool:
        """Arrêter le streaming des métriques d'un service"""
        try:
            stream_key = f"{connection_id}:{service_id}"
            
            if stream_key in self.metrics_streams:
                task = self.metrics_streams[stream_key]
                if not task.done():
                    task.cancel()
                
                del self.metrics_streams[stream_key]
                
                logger.info(f"Stopped metrics stream for service {service_id} to connection {connection_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error stopping metrics stream for service {service_id}: {e}")
            return False
    
    async def _stream_service_logs(self, connection_id: str, service_id: str, lines: int) -> None:
        """Stream des logs de service en continu"""
        try:
            if not self.orchestrator:
                logger.error("No orchestrator available for log streaming")
                return
            
            # Get the service to find the container ID
            service = await self.orchestrator.get_service(service_id)
            if not service:
                logger.error(f"Service {service_id} not found")
                return
            
            container_id = service.get("container_id")
            if not container_id:
                logger.error(f"Service {service_id} has no container")
                return
            
            # Send initial logs
            try:
                initial_logs = await self.orchestrator.get_container_logs(container_id, tail=lines)
                if initial_logs:
                    # Split logs into lines and send each as a separate message
                    for log_line in initial_logs.split('\n'):
                        if log_line.strip():
                            # Parse timestamp and log level from Docker log format
                            timestamp_str, level, message = self._parse_docker_log_line(log_line)
                            
                            log_entry = LogEntry(
                                service_id=service_id,
                                level=level,
                                message=message,
                                timestamp=timestamp_str,
                                source="container"
                            )
                            
                            message = WebSocketMessage(
                                type=EventType.SERVICE_LOGS.value,
                                data={
                                    "service_id": service_id,
                                    "log": log_entry.dict()
                                }
                            )
                            
                            success = await self.ws_manager.send_to_connection(connection_id, message)
                            if not success:
                                return  # Connection closed
                        
                            # Small delay to avoid overwhelming the client
                            await asyncio.sleep(0.01)
            except Exception as e:
                logger.error(f"Error sending initial logs: {e}")
            
            # Stream new logs continuously
            last_timestamp = None
            while True:
                try:
                    # Get logs since last timestamp
                    new_logs = await self.orchestrator.get_container_logs(
                        container_id, 
                        tail=10,  # Get only recent logs
                        since=last_timestamp
                    )
                    
                    if new_logs:
                        log_lines = new_logs.split('\n')
                        for log_line in log_lines:
                            if log_line.strip():
                                timestamp_str, level, message = self._parse_docker_log_line(log_line)
                                
                                log_entry = LogEntry(
                                    service_id=service_id,
                                    level=level,
                                    message=message,
                                    timestamp=timestamp_str,
                                    source="container"
                                )
                                
                                message = WebSocketMessage(
                                    type=EventType.SERVICE_LOGS.value,
                                    data={
                                        "service_id": service_id,
                                        "log": log_entry.dict()
                                    }
                                )
                                
                                success = await self.ws_manager.send_to_connection(connection_id, message)
                                if not success:
                                    return  # Connection closed
                                
                                # Update last timestamp
                                last_timestamp = timestamp_str
                    
                    # Wait before checking for new logs
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error in continuous log streaming: {e}")
                    await asyncio.sleep(5)  # Wait longer on error
                
        except asyncio.CancelledError:
            logger.debug(f"Log stream cancelled for service {service_id}")
        except Exception as e:
            logger.error(f"Error in log stream for service {service_id}: {e}")
    
    def _parse_docker_log_line(self, log_line: str) -> tuple:
        """Parse a Docker log line to extract timestamp, level, and message"""
        try:
            # Docker log format: timestamp level message
            # Example: "2023-07-12T10:30:00.000000000Z INFO This is a log message"
            
            if not log_line.strip():
                return datetime.utcnow(), "info", ""
            
            # Try to extract timestamp
            parts = log_line.split(' ', 2)
            if len(parts) >= 3:
                timestamp_str = parts[0]
                level_str = parts[1].lower()
                message = parts[2]
                
                # Parse timestamp
                try:
                    if 'T' in timestamp_str and 'Z' in timestamp_str:
                        # ISO format with Z
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        # Fallback to current time
                        timestamp = datetime.utcnow()
                except:
                    timestamp = datetime.utcnow()
                
                # Determine log level
                if level_str in ['error', 'err', 'fatal', 'crit']:
                    level = "error"
                elif level_str in ['warn', 'warning']:
                    level = "warning"
                elif level_str in ['debug', 'trace']:
                    level = "debug"
                else:
                    level = "info"
                
                return timestamp, level, message
            else:
                # Simple format without timestamp
                return datetime.utcnow(), "info", log_line
                
        except Exception as e:
            logger.debug(f"Error parsing log line: {e}")
            return datetime.utcnow(), "info", log_line
    
    async def _stream_service_metrics(self, connection_id: str, service_id: str, interval: int) -> None:
        """Stream des métriques de service en continu"""
        try:
            if not self.orchestrator:
                logger.error("No orchestrator available for metrics streaming")
                return
            
            # Get the service to find the container ID
            service = await self.orchestrator.get_service(service_id)
            if not service:
                logger.error(f"Service {service_id} not found")
                return
            
            container_id = service.get("container_id")
            if not container_id:
                logger.error(f"Service {service_id} has no container")
                return
            
            while True:
                try:
                    # Get real metrics from Docker API
                    stats = await self.orchestrator.get_container_stats(container_id)
                    
                    if stats:
                        # Use real Docker stats
                        metrics_data = {
                            "service_id": service_id,
                            "container_id": container_id,
                            "timestamp": stats.get("timestamp", datetime.utcnow().isoformat()),
                            "cpu_usage": stats.get("cpu_usage", 0),
                            "memory_usage": stats.get("memory_usage", 0),
                            "memory_limit": stats.get("memory_limit", 0),
                            "memory_percent": stats.get("memory_percent", 0),
                            "network_io": {
                                "rx_bytes": stats.get("network_rx", 0),
                                "tx_bytes": stats.get("network_tx", 0)
                            },
                            "disk_io": {
                                "read_bytes": stats.get("block_read", 0),
                                "write_bytes": stats.get("block_write", 0)
                            }
                        }
                    else:
                        # Fallback to basic service stats
                        service_stats = await self.orchestrator.get_service_stats(service_id)
                        if service_stats:
                            metrics_data = {
                                "service_id": service_id,
                                "container_id": container_id,
                                "timestamp": service_stats.get("timestamp", datetime.utcnow().isoformat()),
                                "cpu_usage": service_stats.get("cpu_percent", 0),
                                "memory_usage": service_stats.get("memory_usage", 0),
                                "memory_limit": service_stats.get("memory_limit", 0),
                                "memory_percent": service_stats.get("memory_percent", 0),
                                "network_io": {
                                    "rx_bytes": service_stats.get("network_rx", 0),
                                    "tx_bytes": service_stats.get("network_tx", 0)
                                },
                                "disk_io": {
                                    "read_bytes": 0,
                                    "write_bytes": 0
                                }
                            }
                        else:
                            # Service is not running, send empty metrics
                            metrics_data = {
                                "service_id": service_id,
                                "container_id": container_id,
                                "timestamp": datetime.utcnow().isoformat(),
                                "cpu_usage": 0,
                                "memory_usage": 0,
                                "memory_limit": 0,
                                "memory_percent": 0,
                                "network_io": {
                                    "rx_bytes": 0,
                                    "tx_bytes": 0
                                },
                                "disk_io": {
                                    "read_bytes": 0,
                                    "write_bytes": 0
                                },
                                "status": "stopped"
                            }
                    
                    message = WebSocketMessage(
                        type=EventType.SERVICE_METRICS.value,
                        data=metrics_data
                    )
                    
                    success = await self.ws_manager.send_to_connection(connection_id, message)
                    if not success:
                        break  # Connection closed
                    
                    await asyncio.sleep(interval)
                    
                except Exception as e:
                    logger.error(f"Error getting metrics for service {service_id}: {e}")
                    await asyncio.sleep(interval)  # Continue trying
                
        except asyncio.CancelledError:
            logger.debug(f"Metrics stream cancelled for service {service_id}")
        except Exception as e:
            logger.error(f"Error in metrics stream for service {service_id}: {e}")
    
    async def _stop_service_streams(self, service_id: str) -> None:
        """Arrêter tous les streams pour un service"""
        try:
            # Arrêter les streams de logs
            log_keys_to_remove = [
                key for key in self.log_streams.keys() 
                if key.endswith(f":{service_id}")
            ]
            
            for key in log_keys_to_remove:
                task = self.log_streams[key]
                if not task.done():
                    task.cancel()
                del self.log_streams[key]
            
            # Arrêter les streams de métriques
            metrics_keys_to_remove = [
                key for key in self.metrics_streams.keys()
                if key.endswith(f":{service_id}")
            ]
            
            for key in metrics_keys_to_remove:
                task = self.metrics_streams[key]
                if not task.done():
                    task.cancel()
                del self.metrics_streams[key]
            
            logger.info(f"Stopped all streams for service {service_id}")
            
        except Exception as e:
            logger.error(f"Error stopping streams for service {service_id}: {e}")
    
    async def cleanup_connection_streams(self, connection_id: str) -> None:
        """Nettoyer tous les streams d'une connexion"""
        try:
            # Nettoyer les streams de logs
            log_keys_to_remove = [
                key for key in self.log_streams.keys()
                if key.startswith(f"{connection_id}:")
            ]
            
            for key in log_keys_to_remove:
                task = self.log_streams[key]
                if not task.done():
                    task.cancel()
                del self.log_streams[key]
            
            # Nettoyer les streams de métriques
            metrics_keys_to_remove = [
                key for key in self.metrics_streams.keys()
                if key.startswith(f"{connection_id}:")
            ]
            
            for key in metrics_keys_to_remove:
                task = self.metrics_streams[key]
                if not task.done():
                    task.cancel()
                del self.metrics_streams[key]
            
            logger.info(f"Cleaned up all streams for connection {connection_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up streams for connection {connection_id}: {e}")
    
    async def get_service_stream_stats(self) -> Dict[str, Any]:
        """Récupérer les statistiques des streams"""
        try:
            active_log_streams = len([task for task in self.log_streams.values() if not task.done()])
            active_metrics_streams = len([task for task in self.metrics_streams.values() if not task.done()])
            
            return {
                "active_log_streams": active_log_streams,
                "active_metrics_streams": active_metrics_streams,
                "total_log_streams": len(self.log_streams),
                "total_metrics_streams": len(self.metrics_streams)
            }
            
        except Exception as e:
            logger.error(f"Error getting stream stats: {e}")
            return {
                "active_log_streams": 0,
                "active_metrics_streams": 0,
                "total_log_streams": 0,
                "total_metrics_streams": 0,
                "error": str(e)
            }
    
    async def handle_docker_event(self, event: dict) -> None:
        """Gestionnaire d'événements Docker"""
        try:
            event_type = event.get('Type', 'unknown')
            event_action = event.get('Action', 'unknown')
            
            # Diffuser l'événement à tous les clients connectés
            message = WebSocketMessage(
                type=EventType.DOCKER_EVENT.value,
                data={
                    "event_type": event_type,
                    "action": event_action,
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": event
                }
            )
            
            sent_count = await self.ws_manager.broadcast_to_subscribers(
                EventType.DOCKER_EVENT.value,
                message
            )
            
            logger.info(f"Broadcasted Docker event {event_type}:{event_action} to {sent_count} clients")
            
        except Exception as e:
            logger.error(f"Error handling Docker event: {e}")