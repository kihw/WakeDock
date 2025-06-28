"""
Docker utility functions for WakeDock
"""

import asyncio
import logging
import docker
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import json

from wakedock.exceptions import DockerConnectionError, ServiceNotFoundError

logger = logging.getLogger(__name__)


class DockerUtils:
    """Utility class for Docker operations"""
    
    def __init__(self, client: Optional[docker.DockerClient] = None):
        """Initialize Docker utilities
        
        Args:
            client: Optional Docker client. If None, will create a new one.
        """
        self.client = client or docker.from_env()
    
    def parse_container_ports(self, container_ports: Dict) -> List[Dict[str, Any]]:
        """Parse container port configuration
        
        Args:
            container_ports: Port configuration from container attributes
            
        Returns:
            List of port mappings with container_port and host_port
        """
        ports = []
        if not container_ports:
            return ports
        
        for container_port, host_configs in container_ports.items():
            if host_configs:
                for host_config in host_configs:
                    port_info = {
                        'container_port': int(container_port.split('/')[0]),
                        'protocol': container_port.split('/')[1] if '/' in container_port else 'tcp',
                        'host_port': int(host_config.get('HostPort', 0)) if host_config.get('HostPort') else None,
                        'host_ip': host_config.get('HostIp', '0.0.0.0')
                    }
                    ports.append(port_info)
            else:
                # Port exposed but not mapped to host
                port_info = {
                    'container_port': int(container_port.split('/')[0]),
                    'protocol': container_port.split('/')[1] if '/' in container_port else 'tcp',
                    'host_port': None,
                    'host_ip': None
                }
                ports.append(port_info)
        
        return ports
    
    def parse_container_environment(self, env_list: List[str]) -> Dict[str, str]:
        """Parse container environment variables
        
        Args:
            env_list: List of environment variables in KEY=VALUE format
            
        Returns:
            Dictionary of environment variables
        """
        env_dict = {}
        if not env_list:
            return env_dict
        
        for env_var in env_list:
            if '=' in env_var:
                key, value = env_var.split('=', 1)
                env_dict[key] = value
            else:
                env_dict[env_var] = ''
        
        return env_dict
    
    def parse_container_volumes(self, mounts: List[Dict]) -> List[Dict[str, Any]]:
        """Parse container volume mounts
        
        Args:
            mounts: List of mount configurations from container attributes
            
        Returns:
            List of volume mount information
        """
        volumes = []
        if not mounts:
            return volumes
        
        for mount in mounts:
            volume_info = {
                'type': mount.get('Type', 'bind'),
                'source': mount.get('Source', ''),
                'destination': mount.get('Destination', ''),
                'mode': mount.get('Mode', 'rw'),
                'rw': mount.get('RW', True),
                'propagation': mount.get('Propagation', '')
            }
            volumes.append(volume_info)
        
        return volumes
    
    def parse_container_networks(self, networks: Dict) -> List[Dict[str, Any]]:
        """Parse container network configuration
        
        Args:
            networks: Network configuration from container attributes
            
        Returns:
            List of network information
        """
        network_list = []
        if not networks:
            return network_list
        
        for network_name, network_config in networks.items():
            network_info = {
                'name': network_name,
                'ip_address': network_config.get('IPAddress', ''),
                'gateway': network_config.get('Gateway', ''),
                'mac_address': network_config.get('MacAddress', ''),
                'network_id': network_config.get('NetworkID', '')
            }
            network_list.append(network_info)
        
        return network_list
    
    def calculate_container_uptime(self, started_at: str) -> Optional[int]:
        """Calculate container uptime in seconds
        
        Args:
            started_at: Container start time in ISO format
            
        Returns:
            Uptime in seconds, or None if container is not running
        """
        if not started_at or started_at == '0001-01-01T00:00:00Z':
            return None
        
        try:
            # Parse the datetime string
            start_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            current_time = datetime.now(start_time.tzinfo)
            uptime = (current_time - start_time).total_seconds()
            return int(uptime)
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to calculate uptime from {started_at}: {e}")
            return None
    
    def format_container_size(self, size_bytes: int) -> str:
        """Format container size in human-readable format
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string
        """
        if size_bytes == 0:
            return "0 B"
        
        size_units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        size = float(size_bytes)
        
        while size >= 1024 and unit_index < len(size_units) - 1:
            size /= 1024
            unit_index += 1
        
        return f"{size:.1f} {size_units[unit_index]}"
    
    def is_wakedock_managed(self, container_labels: Dict[str, str]) -> bool:
        """Check if container is managed by WakeDock
        
        Args:
            container_labels: Container labels
            
        Returns:
            True if container is managed by WakeDock
        """
        return container_labels.get('wakedock.managed', 'false').lower() == 'true'
    
    def get_service_name_from_labels(self, container_labels: Dict[str, str]) -> Optional[str]:
        """Extract service name from container labels
        
        Args:
            container_labels: Container labels
            
        Returns:
            Service name or None if not found
        """
        return container_labels.get('wakedock.service')
    
    def get_service_domain_from_labels(self, container_labels: Dict[str, str]) -> Optional[str]:
        """Extract service domain from container labels
        
        Args:
            container_labels: Container labels
            
        Returns:
            Service domain or None if not found
        """
        return container_labels.get('wakedock.domain')
    
    def build_container_config(self, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """Build Docker container configuration from service config
        
        Args:
            service_config: Service configuration dictionary
            
        Returns:
            Docker container configuration
        """
        config = {
            'image': service_config['image'],
            'name': service_config['name'],
            'detach': True,
            'restart_policy': service_config.get('restart_policy', {'Name': 'unless-stopped'}),
            'labels': service_config.get('labels', {})
        }
        
        # Add WakeDock management labels
        config['labels'].update({
            'wakedock.managed': 'true',
            'wakedock.service': service_config['name'],
            'wakedock.created_at': datetime.now().isoformat()
        })
        
        # Port configuration
        if 'ports' in service_config:
            config['ports'] = service_config['ports']
        
        # Environment variables
        if 'environment' in service_config:
            config['environment'] = service_config['environment']
        
        # Volume mounts
        if 'volumes' in service_config:
            config['volumes'] = service_config['volumes']
        
        # Network configuration
        if 'networks' in service_config:
            config['network'] = service_config['networks']
        elif 'network' in service_config:
            config['network'] = service_config['network']
        
        # Resource limits
        if 'resources' in service_config:
            resources = service_config['resources']
            if 'memory' in resources:
                config['mem_limit'] = resources['memory']
            if 'cpu' in resources:
                config['cpu_quota'] = int(resources['cpu'] * 100000)  # Convert to microseconds
        
        # Health check
        if 'healthcheck' in service_config:
            config['healthcheck'] = service_config['healthcheck']
        
        return config
    
    def parse_docker_stats(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Docker container stats
        
        Args:
            stats: Raw stats from Docker API
            
        Returns:
            Parsed stats dictionary
        """
        parsed_stats = {
            'timestamp': datetime.now().isoformat(),
            'cpu_usage': 0.0,
            'memory_usage': 0,
            'memory_limit': 0,
            'memory_percent': 0.0,
            'network_rx': 0,
            'network_tx': 0,
            'block_read': 0,
            'block_write': 0
        }
        
        try:
            # CPU calculation
            cpu_stats = stats.get('cpu_stats', {})
            precpu_stats = stats.get('precpu_stats', {})
            
            cpu_delta = cpu_stats.get('cpu_usage', {}).get('total_usage', 0) - \
                       precpu_stats.get('cpu_usage', {}).get('total_usage', 0)
            system_delta = cpu_stats.get('system_cpu_usage', 0) - \
                          precpu_stats.get('system_cpu_usage', 0)
            
            if system_delta > 0 and cpu_delta > 0:
                cpu_count = cpu_stats.get('online_cpus', 1)
                parsed_stats['cpu_usage'] = (cpu_delta / system_delta) * cpu_count * 100.0
            
            # Memory calculation
            memory_stats = stats.get('memory_stats', {})
            parsed_stats['memory_usage'] = memory_stats.get('usage', 0)
            parsed_stats['memory_limit'] = memory_stats.get('limit', 0)
            
            if parsed_stats['memory_limit'] > 0:
                parsed_stats['memory_percent'] = (parsed_stats['memory_usage'] / parsed_stats['memory_limit']) * 100.0
            
            # Network calculation
            networks = stats.get('networks', {})
            for network_stats in networks.values():
                parsed_stats['network_rx'] += network_stats.get('rx_bytes', 0)
                parsed_stats['network_tx'] += network_stats.get('tx_bytes', 0)
            
            # Block I/O calculation
            blkio_stats = stats.get('blkio_stats', {})
            io_service_bytes = blkio_stats.get('io_service_bytes_recursive', [])
            
            for io_stat in io_service_bytes:
                if io_stat.get('op') == 'Read':
                    parsed_stats['block_read'] += io_stat.get('value', 0)
                elif io_stat.get('op') == 'Write':
                    parsed_stats['block_write'] += io_stat.get('value', 0)
        
        except Exception as e:
            logger.warning(f"Failed to parse Docker stats: {e}")
        
        return parsed_stats
    
    def validate_service_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate service configuration
        
        Args:
            config: Service configuration to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields
        required_fields = ['name', 'image']
        for field in required_fields:
            if field not in config or not config[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate service name
        if 'name' in config:
            name = config['name']
            if not isinstance(name, str) or len(name.strip()) == 0:
                errors.append("Service name must be a non-empty string")
            elif not all(c.isalnum() or c in '-_.' for c in name):
                errors.append("Service name can only contain alphanumeric characters, hyphens, underscores, and dots")
        
        # Validate image
        if 'image' in config:
            image = config['image']
            if not isinstance(image, str) or len(image.strip()) == 0:
                errors.append("Image must be a non-empty string")
        
        # Validate ports
        if 'ports' in config:
            ports = config['ports']
            if not isinstance(ports, dict):
                errors.append("Ports must be a dictionary")
            else:
                for container_port, host_port in ports.items():
                    try:
                        int(container_port.split('/')[0])
                        if host_port is not None:
                            int(host_port)
                    except (ValueError, AttributeError):
                        errors.append(f"Invalid port configuration: {container_port}:{host_port}")
        
        # Validate environment
        if 'environment' in config:
            env = config['environment']
            if not isinstance(env, dict):
                errors.append("Environment must be a dictionary")
        
        # Validate volumes
        if 'volumes' in config:
            volumes = config['volumes']
            if not isinstance(volumes, dict):
                errors.append("Volumes must be a dictionary")
        
        return errors
    
    async def test_connection(self) -> bool:
        """Test Docker connection
        
        Returns:
            True if connection is successful
        """
        try:
            self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Docker connection test failed: {e}")
            return False
    
    def get_docker_info(self) -> Dict[str, Any]:
        """Get Docker daemon information
        
        Returns:
            Docker daemon information
        """
        try:
            info = self.client.info()
            return {
                'version': self.client.version(),
                'info': info,
                'containers_running': info.get('ContainersRunning', 0),
                'containers_paused': info.get('ContainersPaused', 0),
                'containers_stopped': info.get('ContainersStopped', 0),
                'images': info.get('Images', 0),
                'server_version': info.get('ServerVersion', 'Unknown'),
                'storage_driver': info.get('Driver', 'Unknown'),
                'total_memory': info.get('MemTotal', 0)
            }
        except Exception as e:
            logger.error(f"Failed to get Docker info: {e}")
            raise DockerConnectionError(f"Failed to get Docker daemon information: {e}")


# Global instance for easy access
docker_utils = DockerUtils()
