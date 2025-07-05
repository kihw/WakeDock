"""
Log Streaming Handler
Streams Docker container logs in real-time via WebSocket
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Callable, Set, List
import docker
from docker.models.containers import Container

logger = logging.getLogger(__name__)

class LogStreamingHandler:
    """
    Handles Docker container log streaming and broadcasting
    """
    
    def __init__(self, docker_client: docker.DockerClient):
        self.docker_client = docker_client
        self.is_monitoring = False
        self.active_streams: Dict[str, asyncio.Task] = {}
        self.subscribers: Set[Callable] = set()
        self.container_subscriptions: Dict[str, Set[Callable]] = {}
        
    def subscribe(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribe to all log streams"""
        self.subscribers.add(callback)
        logger.debug(f"Added log streaming subscriber. Total: {len(self.subscribers)}")
        
    def subscribe_to_container(self, container_id: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribe to logs from a specific container"""
        if container_id not in self.container_subscriptions:
            self.container_subscriptions[container_id] = set()
        self.container_subscriptions[container_id].add(callback)
        logger.debug(f"Added subscriber for container {container_id}")
        
    def unsubscribe(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Unsubscribe from all log streams"""
        self.subscribers.discard(callback)
        # Also remove from container subscriptions
        for container_id in self.container_subscriptions:
            self.container_subscriptions[container_id].discard(callback)
        logger.debug(f"Removed log streaming subscriber. Total: {len(self.subscribers)}")
        
    def unsubscribe_from_container(self, container_id: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Unsubscribe from logs of a specific container"""
        if container_id in self.container_subscriptions:
            self.container_subscriptions[container_id].discard(callback)
            # Clean up empty sets
            if not self.container_subscriptions[container_id]:
                del self.container_subscriptions[container_id]
        logger.debug(f"Removed subscriber for container {container_id}")
    
    async def start_monitoring(self) -> None:
        """Start monitoring logs for all running containers"""
        if self.is_monitoring:
            logger.warning("Log streaming monitoring is already running")
            return
            
        self.is_monitoring = True
        logger.info("Started log streaming monitoring")
        
        # Start monitoring existing containers
        await self._start_existing_containers()
        
    async def stop_monitoring(self) -> None:
        """Stop monitoring all container logs"""
        self.is_monitoring = False
        
        # Stop all active streams
        for container_id, task in list(self.active_streams.items()):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            
        self.active_streams.clear()
        logger.info("Stopped log streaming monitoring")
        
    async def start_container_stream(self, container_id: str) -> bool:
        """Start log streaming for a specific container"""
        if container_id in self.active_streams:
            logger.debug(f"Log stream already active for container {container_id}")
            return True
            
        try:
            container = self.docker_client.containers.get(container_id)
            task = asyncio.create_task(self._stream_container_logs(container))
            self.active_streams[container_id] = task
            logger.info(f"Started log streaming for container {container.name} ({container_id[:12]})")
            return True
            
        except docker.errors.NotFound:
            logger.warning(f"Container {container_id} not found for log streaming")
            return False
        except Exception as e:
            logger.error(f"Failed to start log stream for container {container_id}: {e}")
            return False
            
    async def stop_container_stream(self, container_id: str) -> bool:
        """Stop log streaming for a specific container"""
        if container_id not in self.active_streams:
            logger.debug(f"No active log stream for container {container_id}")
            return True
            
        try:
            task = self.active_streams.pop(container_id)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            logger.info(f"Stopped log streaming for container {container_id[:12]}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping log stream for container {container_id}: {e}")
            return False
            
    async def _start_existing_containers(self) -> None:
        """Start log streaming for all running containers"""
        try:
            containers = self.docker_client.containers.list(filters={'status': 'running'})
            logger.info(f"Starting log streaming for {len(containers)} running containers")
            
            for container in containers:
                if self.is_monitoring:
                    await self.start_container_stream(container.id)
                    
        except Exception as e:
            logger.error(f"Error starting log streams for existing containers: {e}")
            
    async def _stream_container_logs(self, container: Container) -> None:
        """Stream logs from a specific container"""
        container_id = container.id
        container_name = container.name
        
        try:
            logger.debug(f"Starting log stream for {container_name} ({container_id[:12]})")
            
            # Get log stream (follow=True for real-time, tail=50 for recent history)
            log_stream = container.logs(
                stream=True,
                follow=True,
                stdout=True,
                stderr=True,
                timestamps=True,
                tail=50
            )
            
            # Process logs in executor to avoid blocking
            while self.is_monitoring and container_id in self.active_streams:
                try:
                    # Get next log line
                    log_line = await asyncio.get_event_loop().run_in_executor(
                        None, next, log_stream
                    )
                    
                    if log_line:
                        await self._process_log_line(container_id, container_name, log_line)
                        
                except StopIteration:
                    logger.debug(f"Log stream ended for container {container_name}")
                    break
                except Exception as e:
                    logger.error(f"Error reading log line from {container_name}: {e}")
                    await asyncio.sleep(1)  # Brief pause before retrying
                    
        except Exception as e:
            logger.error(f"Log streaming failed for container {container_name}: {e}")
        finally:
            # Clean up
            if container_id in self.active_streams:
                self.active_streams.pop(container_id, None)
            logger.debug(f"Log stream cleanup completed for {container_name}")
            
    async def _process_log_line(self, container_id: str, container_name: str, log_line: bytes) -> None:
        """Process a single log line and broadcast it"""
        try:
            # Decode log line
            log_text = log_line.decode('utf-8', errors='replace').strip()
            
            if not log_text:
                return
                
            # Parse timestamp if present (Docker format: 2023-12-01T10:30:45.123456789Z message)
            timestamp = datetime.utcnow().isoformat()
            message = log_text
            log_level = 'info'
            
            # Try to parse Docker timestamp format
            if 'T' in log_text and 'Z' in log_text:
                try:
                    timestamp_end = log_text.find('Z') + 1
                    if timestamp_end > 1:
                        timestamp_str = log_text[:timestamp_end]
                        message = log_text[timestamp_end:].strip()
                        
                        # Validate and use the timestamp
                        datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        timestamp = timestamp_str
                except (ValueError, IndexError):
                    # If parsing fails, use original text as message
                    pass
            
            # Detect log level from message content
            message_upper = message.upper()
            if any(level in message_upper for level in ['ERROR', 'FATAL', 'CRITICAL']):
                log_level = 'error'
            elif any(level in message_upper for level in ['WARN', 'WARNING']):
                log_level = 'warning'
            elif any(level in message_upper for level in ['DEBUG']):
                log_level = 'debug'
            elif any(level in message_upper for level in ['INFO']):
                log_level = 'info'
            
            # Create log entry
            log_entry = {
                'container_id': container_id,
                'container_name': container_name,
                'timestamp': timestamp,
                'message': message,
                'level': log_level,
                'source': 'docker',
                'received_at': datetime.utcnow().isoformat()
            }
            
            # Broadcast to subscribers
            await self._broadcast_log_entry(log_entry)
            
        except Exception as e:
            logger.error(f"Error processing log line from {container_name}: {e}")
            
    async def _broadcast_log_entry(self, log_entry: Dict[str, Any]) -> None:
        """Broadcast log entry to all subscribers"""
        container_id = log_entry['container_id']
        
        # Create WebSocket message
        log_message = {
            'type': 'log_entry',
            'data': log_entry
        }
        
        # Broadcast to general subscribers
        for callback in self.subscribers.copy():
            try:
                await self._safe_callback(callback, log_message)
            except Exception as e:
                logger.error(f"Error in log streaming callback: {e}")
                
        # Broadcast to container-specific subscribers
        if container_id in self.container_subscriptions:
            for callback in self.container_subscriptions[container_id].copy():
                try:
                    await self._safe_callback(callback, log_message)
                except Exception as e:
                    logger.error(f"Error in container-specific log callback: {e}")
                    
    async def _safe_callback(self, callback: Callable, data: Dict[str, Any]) -> None:
        """Safely execute callback"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(data)
            else:
                callback(data)
        except Exception as e:
            logger.error(f"Log streaming callback execution failed: {e}")
            
    async def get_recent_logs(self, container_id: str, lines: int = 100) -> List[Dict[str, Any]]:
        """Get recent logs from a container"""
        try:
            container = self.docker_client.containers.get(container_id)
            logs = container.logs(
                stdout=True,
                stderr=True,
                timestamps=True,
                tail=lines
            )
            
            log_entries = []
            for line in logs.decode('utf-8', errors='replace').split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                # Parse similar to _process_log_line but return list
                timestamp = datetime.utcnow().isoformat()
                message = line
                log_level = 'info'
                
                # Try to parse Docker timestamp format
                if 'T' in line and 'Z' in line:
                    try:
                        timestamp_end = line.find('Z') + 1
                        if timestamp_end > 1:
                            timestamp_str = line[:timestamp_end]
                            message = line[timestamp_end:].strip()
                            
                            # Validate and use the timestamp
                            datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            timestamp = timestamp_str
                    except (ValueError, IndexError):
                        pass
                
                # Detect log level
                message_upper = message.upper()
                if any(level in message_upper for level in ['ERROR', 'FATAL', 'CRITICAL']):
                    log_level = 'error'
                elif any(level in message_upper for level in ['WARN', 'WARNING']):
                    log_level = 'warning'
                elif any(level in message_upper for level in ['DEBUG']):
                    log_level = 'debug'
                elif any(level in message_upper for level in ['INFO']):
                    log_level = 'info'
                
                log_entries.append({
                    'container_id': container_id,
                    'container_name': container.name,
                    'timestamp': timestamp,
                    'message': message,
                    'level': log_level,
                    'source': 'docker'
                })
                
            return log_entries
            
        except docker.errors.NotFound:
            logger.warning(f"Container {container_id} not found for log retrieval")
            return []
        except Exception as e:
            logger.error(f"Error getting recent logs for container {container_id}: {e}")
            return []
            
    def get_active_streams(self) -> List[str]:
        """Get list of container IDs with active log streams"""
        return list(self.active_streams.keys())
        
    def get_stream_stats(self) -> Dict[str, Any]:
        """Get statistics about log streaming"""
        return {
            'active_streams': len(self.active_streams),
            'total_subscribers': len(self.subscribers),
            'container_subscriptions': {
                container_id: len(subscribers)
                for container_id, subscribers in self.container_subscriptions.items()
            },
            'is_monitoring': self.is_monitoring
        }

# Global instance (will be initialized by the main app)
log_streaming_handler: Optional[LogStreamingHandler] = None

def initialize_log_streaming(docker_client: docker.DockerClient) -> LogStreamingHandler:
    """Initialize the global log streaming handler"""
    global log_streaming_handler
    log_streaming_handler = LogStreamingHandler(docker_client)
    return log_streaming_handler

def get_log_streaming_handler() -> Optional[LogStreamingHandler]:
    """Get the global log streaming handler"""
    return log_streaming_handler