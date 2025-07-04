"""
Docker Events Handler
Monitors Docker events and broadcasts updates via WebSocket
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Callable, Set
import docker
from docker.models.containers import Container

logger = logging.getLogger(__name__)

class DockerEventsHandler:
    """
    Handles Docker events and converts them to WebSocket messages
    """
    
    def __init__(self, docker_client: docker.DockerClient):
        self.docker_client = docker_client
        self.is_monitoring = False
        self.event_task: Optional[asyncio.Task] = None
        self.subscribers: Set[Callable] = set()
        
    def subscribe(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribe to Docker events"""
        self.subscribers.add(callback)
        logger.debug(f"Added Docker events subscriber. Total: {len(self.subscribers)}")
        
    def unsubscribe(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Unsubscribe from Docker events"""
        self.subscribers.discard(callback)
        logger.debug(f"Removed Docker events subscriber. Total: {len(self.subscribers)}")
    
    async def start_monitoring(self) -> None:
        """Start monitoring Docker events"""
        if self.is_monitoring:
            logger.warning("Docker events monitoring is already running")
            return
            
        self.is_monitoring = True
        self.event_task = asyncio.create_task(self._monitor_events())
        logger.info("Started Docker events monitoring")
        
    async def stop_monitoring(self) -> None:
        """Stop monitoring Docker events"""
        self.is_monitoring = False
        
        if self.event_task:
            self.event_task.cancel()
            try:
                await self.event_task
            except asyncio.CancelledError:
                pass
            self.event_task = None
            
        logger.info("Stopped Docker events monitoring")
        
    async def _monitor_events(self) -> None:
        """Monitor Docker events in a background task"""
        try:
            # Get events stream
            events = self.docker_client.events(decode=True)
            
            logger.info("Docker events stream established")
            
            while self.is_monitoring:
                try:
                    # Get next event (this is blocking, so we run it in executor)
                    event = await asyncio.get_event_loop().run_in_executor(
                        None, next, events
                    )
                    
                    # Process the event
                    await self._process_event(event)
                    
                except StopIteration:
                    logger.warning("Docker events stream ended")
                    break
                except Exception as e:
                    logger.error(f"Error processing Docker event: {e}")
                    await asyncio.sleep(1)  # Brief pause before continuing
                    
        except Exception as e:
            logger.error(f"Docker events monitoring failed: {e}")
        finally:
            self.is_monitoring = False
            
    async def _process_event(self, event: Dict[str, Any]) -> None:
        """Process a Docker event and broadcast it"""
        try:
            # Filter for container events we care about
            if event.get('Type') != 'container':
                return
                
            action = event.get('Action', '')
            container_id = event.get('Actor', {}).get('ID', '')
            container_name = event.get('Actor', {}).get('Attributes', {}).get('name', '')
            
            # Only process relevant actions
            relevant_actions = {
                'start', 'stop', 'restart', 'kill', 'die', 'pause', 'unpause',
                'create', 'destroy', 'update', 'health_status'
            }
            
            if action not in relevant_actions:
                return
                
            logger.debug(f"Processing Docker event: {action} for container {container_name}")
            
            # Get container details
            container_data = await self._get_container_data(container_id, container_name)
            
            # Create service update message
            service_update = {
                'id': container_id,
                'name': container_name,
                'action': action,
                'status': container_data.get('status', 'unknown'),
                'health_status': container_data.get('health_status'),
                'resource_usage': container_data.get('resource_usage'),
                'timestamp': datetime.utcnow().isoformat(),
                'event_data': {
                    'action': action,
                    'time': event.get('time', 0),
                    'timeNano': event.get('timeNano', 0)
                }
            }
            
            # Broadcast to all subscribers
            for callback in self.subscribers.copy():  # Copy to avoid modification during iteration
                try:
                    await self._safe_callback(callback, service_update)
                except Exception as e:
                    logger.error(f"Error in Docker events callback: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing Docker event: {e}")
            
    async def _safe_callback(self, callback: Callable, data: Dict[str, Any]) -> None:
        """Safely execute callback"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(data)
            else:
                callback(data)
        except Exception as e:
            logger.error(f"Callback execution failed: {e}")
            
    async def _get_container_data(self, container_id: str, container_name: str) -> Dict[str, Any]:
        """Get detailed container information"""
        try:
            # Get container object
            container = self.docker_client.containers.get(container_id)
            
            # Basic container info
            container_info = {
                'id': container_id,
                'name': container_name,
                'status': container.status,
                'image': container.image.tags[0] if container.image.tags else 'unknown',
                'created': container.attrs.get('Created', ''),
                'started_at': container.attrs.get('State', {}).get('StartedAt', ''),
            }
            
            # Health status
            health = container.attrs.get('State', {}).get('Health', {})
            if health:
                container_info['health_status'] = health.get('Status', 'unknown').lower()
            
            # Get resource usage stats
            try:
                stats = container.stats(stream=False)
                resource_usage = self._calculate_resource_usage(stats)
                container_info['resource_usage'] = resource_usage
            except Exception as e:
                logger.debug(f"Could not get stats for container {container_name}: {e}")
                container_info['resource_usage'] = {
                    'cpu_usage': 0.0,
                    'memory_usage': 0.0,
                    'network_io': {'rx': 0, 'tx': 0}
                }
            
            # Port mappings
            ports = []
            port_bindings = container.attrs.get('NetworkSettings', {}).get('Ports', {})
            for container_port, host_bindings in port_bindings.items():
                if host_bindings:
                    for binding in host_bindings:
                        ports.append({
                            'host': int(binding.get('HostPort', 0)),
                            'container': int(container_port.split('/')[0]),
                            'protocol': container_port.split('/')[1] if '/' in container_port else 'tcp'
                        })
            container_info['ports'] = ports
            
            # Environment variables (filtered for security)
            env_vars = {}
            for env in container.attrs.get('Config', {}).get('Env', []):
                if '=' in env:
                    key, value = env.split('=', 1)
                    # Filter out sensitive variables
                    if not any(sensitive in key.upper() for sensitive in ['PASSWORD', 'SECRET', 'KEY', 'TOKEN']):
                        env_vars[key] = value
            container_info['environment'] = env_vars
            
            # Labels
            container_info['labels'] = container.attrs.get('Config', {}).get('Labels', {}) or {}
            
            return container_info
            
        except docker.errors.NotFound:
            logger.debug(f"Container {container_id} not found (probably removed)")
            return {
                'id': container_id,
                'name': container_name,
                'status': 'removed',
                'health_status': None,
                'resource_usage': None
            }
        except Exception as e:
            logger.error(f"Error getting container data for {container_id}: {e}")
            return {
                'id': container_id,
                'name': container_name,
                'status': 'error',
                'health_status': None,
                'resource_usage': None,
                'error': str(e)
            }
            
    def _calculate_resource_usage(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate resource usage from Docker stats"""
        try:
            # CPU usage calculation
            cpu_usage = 0.0
            cpu_stats = stats.get('cpu_stats', {})
            precpu_stats = stats.get('precpu_stats', {})
            
            if cpu_stats and precpu_stats:
                cpu_delta = cpu_stats.get('cpu_usage', {}).get('total_usage', 0) - \
                           precpu_stats.get('cpu_usage', {}).get('total_usage', 0)
                system_delta = cpu_stats.get('system_cpu_usage', 0) - \
                              precpu_stats.get('system_cpu_usage', 0)
                
                if system_delta > 0 and cpu_delta >= 0:
                    cpu_count = cpu_stats.get('cpu_usage', {}).get('percpu_usage', [])
                    if cpu_count:
                        cpu_usage = (cpu_delta / system_delta) * len(cpu_count) * 100.0
            
            # Memory usage calculation
            memory_usage = 0.0
            memory_stats = stats.get('memory_stats', {})
            if memory_stats:
                usage = memory_stats.get('usage', 0)
                limit = memory_stats.get('limit', 0)
                if limit > 0:
                    memory_usage = (usage / limit) * 100.0
            
            # Network I/O
            network_io = {'rx': 0, 'tx': 0}
            networks = stats.get('networks', {})
            for interface_stats in networks.values():
                network_io['rx'] += interface_stats.get('rx_bytes', 0)
                network_io['tx'] += interface_stats.get('tx_bytes', 0)
            
            return {
                'cpu_usage': round(cpu_usage, 2),
                'memory_usage': round(memory_usage, 2),
                'network_io': network_io
            }
            
        except Exception as e:
            logger.error(f"Error calculating resource usage: {e}")
            return {
                'cpu_usage': 0.0,
                'memory_usage': 0.0,
                'network_io': {'rx': 0, 'tx': 0}
            }
    
    async def get_all_containers_status(self) -> Dict[str, Any]:
        """Get status of all containers"""
        try:
            containers = self.docker_client.containers.list(all=True)
            container_data = []
            
            for container in containers:
                data = await self._get_container_data(container.id, container.name)
                container_data.append(data)
            
            return {
                'containers': container_data,
                'total': len(container_data),
                'running': len([c for c in container_data if c.get('status') == 'running']),
                'stopped': len([c for c in container_data if c.get('status') in ['exited', 'stopped']]),
                'error': len([c for c in container_data if c.get('status') == 'error']),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting containers status: {e}")
            return {
                'containers': [],
                'total': 0,
                'running': 0,
                'stopped': 0,
                'error': 0,
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }

# Global instance (will be initialized by the main app)
docker_events_handler: Optional[DockerEventsHandler] = None

def initialize_docker_events(docker_client: docker.DockerClient) -> DockerEventsHandler:
    """Initialize the global Docker events handler"""
    global docker_events_handler
    docker_events_handler = DockerEventsHandler(docker_client)
    return docker_events_handler

def get_docker_events_handler() -> Optional[DockerEventsHandler]:
    """Get the global Docker events handler"""
    return docker_events_handler