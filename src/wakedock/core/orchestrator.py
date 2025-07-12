"""
Docker orchestration service
"""

import asyncio
import logging
import os
import subprocess
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

import docker
from docker.models.containers import Container
from docker.models.images import Image

from wakedock.config import get_settings, ServiceSettings
from wakedock.infrastructure.caddy import caddy_manager
from wakedock.utils.docker_utils import DockerUtils

logger = logging.getLogger(__name__)


class DockerOrchestrator:
    """Manages Docker containers and services"""
    
    def __init__(self):
        self.settings = get_settings()
        self.services: Dict[str, Dict[str, Any]] = {}
        self.container_map: Dict[str, str] = {}  # container_id -> service_id
        self.client = None
        self.docker_utils = None
        self._initialize_docker_client()
        self._load_services()
    
    def _initialize_docker_client(self):
        """Initialize Docker client with error handling"""
        try:
            self.client = docker.from_env()
            # Test connection
            self.client.ping()
            # Initialize Docker utils with client
            self.docker_utils = DockerUtils(self.client)
            logger.info("✅ Docker client initialized successfully")
        except docker.errors.DockerException as e:
            logger.error(f"❌ Failed to connect to Docker daemon: {e}")
            if "Permission denied" in str(e):
                logger.error("💡 This is likely a Docker socket permission issue.")
                logger.error("💡 Make sure the container has access to /var/run/docker.sock")
            self.client = None
            self.docker_utils = None
        except Exception as e:
            logger.error(f"❌ Unexpected error initializing Docker client: {e}")
            self.client = None
            self.docker_utils = None
    
    def _load_services(self):
        """Load services from configuration"""
        for service_config in self.settings.services:
            service_id = f"wakedock-{service_config.name}"
            self.services[service_id] = {
                "id": service_id,
                "name": service_config.name,
                "subdomain": service_config.subdomain,
                "docker_image": service_config.docker_image,
                "docker_compose": service_config.docker_compose,
                "ports": service_config.ports,
                "environment": service_config.environment,
                "auto_shutdown": service_config.auto_shutdown.dict(),
                "loading_page": service_config.loading_page.dict(),
                "health_check": service_config.health_check.dict(),
                "status": "stopped",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "last_accessed": None,
                "resource_usage": None,
                "container_id": None
            }
    
    async def list_services(self) -> List[Dict[str, Any]]:
        """List all services"""
        return list(self.services.values())
    
    async def get_service(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Get service by ID"""
        return self.services.get(service_id)
    
    async def get_service_by_subdomain(self, subdomain: str) -> Optional[Dict[str, Any]]:
        """Get service by subdomain"""
        for service in self.services.values():
            if service["subdomain"] == subdomain:
                return service
        return None
    
    async def create_service(self, service_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new service"""
        service_id = f"wakedock-{service_data['name']}"
        
        if service_id in self.services:
            raise ValueError(f"Service {service_data['name']} already exists")
        
        # Validate service data
        if not service_data.get("docker_image") and not service_data.get("docker_compose"):
            raise ValueError("Either docker_image or docker_compose must be specified")
        
        # Create service entry
        service = {
            "id": service_id,
            "name": service_data["name"],
            "subdomain": service_data["subdomain"],
            "docker_image": service_data.get("docker_image"),
            "docker_compose": service_data.get("docker_compose"),
            "ports": service_data.get("ports", []),
            "environment": service_data.get("environment", {}),
            "auto_shutdown": service_data.get("auto_shutdown", {}),
            "loading_page": service_data.get("loading_page", {}),
            "status": "stopped",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "last_accessed": None,
            "resource_usage": None,
            "container_id": None
        }
        
        self.services[service_id] = service
        return service
    
    async def update_service(self, service_id: str, service_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update service configuration"""
        if service_id not in self.services:
            return None
        
        service = self.services[service_id]
        
        # Update fields
        for key, value in service_data.items():
            if key in ["name", "subdomain", "docker_image", "docker_compose", "ports", "environment", "auto_shutdown", "loading_page"]:
                service[key] = value
        
        service["updated_at"] = datetime.now()
        return service
    
    async def delete_service(self, service_id: str) -> bool:
        """Delete a service"""
        if service_id not in self.services:
            return False
        
        # Stop service if running
        await self.sleep_service(service_id)
        
        # Remove from services
        del self.services[service_id]
        return True
    
    async def is_service_running(self, service_id: str) -> bool:
        """Check if service is running"""
        if not self._check_docker_available():
            return False
            
        service = self.services.get(service_id)
        if not service:
            return False
        
        container_id = service.get("container_id")
        if not container_id:
            return False
        
        try:
            container = self.client.containers.get(container_id)
            is_running = container.status == "running"
            
            # Update service status
            service["status"] = "running" if is_running else "stopped"
            return is_running
        except docker.errors.NotFound:
            service["status"] = "stopped"
            service["container_id"] = None
            return False
    
    async def wake_service(self, service_id: str) -> bool:
        """Wake up a service"""
        service = self.services.get(service_id)
        if not service:
            return False
        
        logger.info(f"Waking up service: {service['name']}")
        
        try:
            success = False
            if service.get("docker_compose"):
                # Use docker-compose
                success = await self._start_compose_service(service)
            else:
                # Use docker image
                success = await self._start_docker_service(service)
            
            # Update Caddy configuration if service started successfully
            if success and service.get("domain"):
                from wakedock.database.models import Service, ServiceStatus
                # Create a service object for Caddy
                caddy_service = type('Service', (), {
                    'name': service['name'],
                    'domain': service.get('domain'),
                    'status': ServiceStatus.RUNNING,
                    'ports': service.get('ports', []),
                    'enable_ssl': service.get('enable_ssl', True),
                    'enable_auth': service.get('enable_auth', False)
                })()
                
                # Add route to Caddy (legacy method)
                await caddy_manager.add_service_route(caddy_service)
                
                # Regenerate complete Caddyfile with all services
                await self._update_caddy_configuration()
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to wake service {service['name']}: {str(e)}")
            return False
    
    async def _start_docker_service(self, service: Dict[str, Any]) -> bool:
        """Start a Docker service from image"""
        if not self._check_docker_available():
            return False
            
        try:
            # Check if container already exists
            container_name = f"wakedock-{service['name']}"
            
            try:
                container = self.client.containers.get(container_name)
                if container.status == "running":
                    service["status"] = "running"
                    service["container_id"] = container.id
                    return True
                else:
                    # Start existing container
                    container.start()
                    service["status"] = "running"
                    service["container_id"] = container.id
                    return True
            except docker.errors.NotFound:
                pass
            
            # Create new container
            ports = {}
            if service["ports"]:
                for port_mapping in service["ports"]:
                    if ":" in port_mapping:
                        host_port, container_port = port_mapping.split(":")
                        ports[container_port] = host_port
            
            container = self.client.containers.run(
                service["docker_image"],
                name=container_name,
                ports=ports,
                environment=service["environment"],
                detach=True,
                network="caddy_net"
            )
            
            service["status"] = "running"
            service["container_id"] = container.id
            self.container_map[container.id] = service["id"]
            
            logger.info(f"Started container {container_name} with ID {container.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Docker service {service['name']}: {str(e)}")
            service["status"] = "error"
            return False
    
    async def _start_compose_service(self, service: Dict[str, Any]) -> bool:
        """Start a Docker Compose service"""
        try:
            compose_file = service["docker_compose"]
            if not os.path.exists(compose_file):
                logger.error(f"Docker Compose file not found: {compose_file}")
                return False
            
            # Use docker-compose to start service
            result = subprocess.run([
                "docker-compose", "-f", compose_file, "up", "-d"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to start compose service: {result.stderr}")
                return False
            
            service["status"] = "running"
            logger.info(f"Started compose service: {service['name']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start compose service {service['name']}: {str(e)}")
            service["status"] = "error"
            return False
    
    async def sleep_service(self, service_id: str) -> bool:
        """Put a service to sleep"""
        service = self.services.get(service_id)
        if not service:
            return False
        
        logger.info(f"Putting service to sleep: {service['name']}")
        
        try:
            success = False
            if service.get("docker_compose"):
                success = await self._stop_compose_service(service)
            else:
                success = await self._stop_docker_service(service)
            
            # Remove route from Caddy if service stopped successfully
            if success and service.get("domain"):
                from wakedock.database.models import Service, ServiceStatus
                # Create a service object for Caddy
                caddy_service = type('Service', (), {
                    'name': service['name'],
                    'domain': service.get('domain'),
                    'status': ServiceStatus.STOPPED
                })()
                
                # Remove route from Caddy (legacy method)
                await caddy_manager.remove_service_route(caddy_service)
                
                # Regenerate complete Caddyfile with remaining services
                await self._update_caddy_configuration()
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to sleep service {service['name']}: {str(e)}")
            return False
    
    async def _stop_docker_service(self, service: Dict[str, Any]) -> bool:
        """Stop a Docker service"""
        try:
            container_id = service.get("container_id")
            if container_id:
                try:
                    container = self.client.containers.get(container_id)
                    container.stop()
                    service["status"] = "stopped"
                    service["container_id"] = None
                    self.container_map.pop(container_id, None)
                    logger.info(f"Stopped container for service: {service['name']}")
                    return True
                except docker.errors.NotFound:
                    service["status"] = "stopped"
                    service["container_id"] = None
                    return True
            
            # Try to find container by name
            container_name = f"wakedock-{service['name']}"
            try:
                container = self.client.containers.get(container_name)
                container.stop()
                service["status"] = "stopped"
                logger.info(f"Stopped container: {container_name}")
                return True
            except docker.errors.NotFound:
                service["status"] = "stopped"
                return True
            
        except Exception as e:
            logger.error(f"Failed to stop Docker service {service['name']}: {str(e)}")
            return False
    
    async def _stop_compose_service(self, service: Dict[str, Any]) -> bool:
        """Stop a Docker Compose service"""
        try:
            compose_file = service["docker_compose"]
            if not os.path.exists(compose_file):
                logger.error(f"Docker Compose file not found: {compose_file}")
                return False
            
            # Use docker-compose to stop service
            result = subprocess.run([
                "docker-compose", "-f", compose_file, "down"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to stop compose service: {result.stderr}")
                return False
            
            service["status"] = "stopped"
            logger.info(f"Stopped compose service: {service['name']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop compose service {service['name']}: {str(e)}")
            return False
    
    async def get_service_url(self, service_id: str) -> Optional[str]:
        """Get the URL for a running service"""
        service = self.services.get(service_id)
        if not service or service["status"] != "running":
            return None
        
        # For now, assume services run on their first port
        ports = service.get("ports", [])
        if ports:
            port_mapping = ports[0]
            if ":" in port_mapping:
                host_port = port_mapping.split(":")[0]
                return f"http://localhost:{host_port}"
        
        # Default to container name and port 80
        container_name = f"wakedock-{service['name']}"
        return f"http://{container_name}:80"
    
    async def update_service_access(self, service_id: str):
        """Update last accessed time for a service"""
        service = self.services.get(service_id)
        if service:
            service["last_accessed"] = datetime.now()
    
    async def get_service_stats(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Get resource usage statistics for a service"""
        service = self.services.get(service_id)
        if not service or not service.get("container_id"):
            return None
        
        try:
            container = self.client.containers.get(service["container_id"])
            stats = container.stats(stream=False)
            
            # Calculate CPU percentage
            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            system_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
            cpu_percent = (cpu_delta / system_delta) * len(stats["cpu_stats"]["cpu_usage"]["percpu_usage"]) * 100
            
            # Calculate memory usage
            memory_usage = stats["memory_stats"]["usage"]
            memory_limit = stats["memory_stats"]["limit"]
            memory_percent = (memory_usage / memory_limit) * 100
            
            resource_stats = {
                "cpu_percent": round(cpu_percent, 2),
                "memory_usage": memory_usage,
                "memory_limit": memory_limit,
                "memory_percent": round(memory_percent, 2),
                "network_rx": stats["networks"]["eth0"]["rx_bytes"] if "networks" in stats else 0,
                "network_tx": stats["networks"]["eth0"]["tx_bytes"] if "networks" in stats else 0,
                "timestamp": datetime.now()
            }
            
            service["resource_usage"] = resource_stats
            return resource_stats
            
        except Exception as e:
            logger.error(f"Failed to get stats for service {service['name']}: {str(e)}")
            return None
    
    async def _update_caddy_configuration(self):
        """Update Caddy configuration with all running services."""
        try:
            from wakedock.database.models import Service, ServiceStatus
            
            # Collect all running services
            running_services = []
            
            for service_id, service_data in self.services.items():
                if service_data.get("status") == "running" and service_data.get("domain"):
                    # Create service object for Caddy
                    caddy_service = type('Service', (), {
                        'name': service_data['name'],
                        'domain': service_data.get('domain'),
                        'status': ServiceStatus.RUNNING,
                        'ports': service_data.get('ports', []),
                        'enable_ssl': service_data.get('enable_ssl', True),
                        'enable_auth': service_data.get('enable_auth', False)
                    })()
                    running_services.append(caddy_service)
            
            # Update Caddy configuration with all services
            logger.info(f"Updating Caddy configuration with {len(running_services)} running services")
            success = await caddy_manager.update_service_config(running_services)
            
            if success:
                logger.info("✅ Caddy configuration updated successfully")
            else:
                logger.error("❌ Failed to update Caddy configuration")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Error updating Caddy configuration: {e}")
            return False

    async def list_containers(self, all_containers: bool = False) -> List[Dict[str, Any]]:
        """List all Docker containers with detailed information"""
        if not self._check_docker_available():
            return []
        
        try:
            containers = self.client.containers.list(all=all_containers)
            container_list = []
            
            for container in containers:
                container_info = {
                    "id": container.id,
                    "short_id": container.short_id,
                    "name": container.name,
                    "image": container.image.tags[0] if container.image.tags else container.image.id,
                    "status": container.status,
                    "state": container.attrs.get('State', {}),
                    "created": container.attrs.get('Created', ''),
                    "started_at": container.attrs.get('State', {}).get('StartedAt', ''),
                    "finished_at": container.attrs.get('State', {}).get('FinishedAt', ''),
                    "ports": self.docker_utils.parse_container_ports(container.attrs.get('NetworkSettings', {}).get('Ports', {})),
                    "environment": self.docker_utils.parse_container_environment(container.attrs.get('Config', {}).get('Env', [])),
                    "volumes": self.docker_utils.parse_container_volumes(container.attrs.get('Mounts', [])),
                    "networks": self.docker_utils.parse_container_networks(container.attrs.get('NetworkSettings', {}).get('Networks', {})),
                    "labels": container.attrs.get('Config', {}).get('Labels', {}),
                    "uptime": self.docker_utils.calculate_container_uptime(container.attrs.get('State', {}).get('StartedAt', '')),
                    "size": container.attrs.get('SizeRootFs', 0),
                    "size_formatted": self.docker_utils.format_container_size(container.attrs.get('SizeRootFs', 0)),
                    "is_wakedock_managed": self.docker_utils.is_wakedock_managed(container.attrs.get('Config', {}).get('Labels', {})),
                    "service_name": self.docker_utils.get_service_name_from_labels(container.attrs.get('Config', {}).get('Labels', {}))
                }
                container_list.append(container_info)
            
            return container_list
            
        except Exception as e:
            logger.error(f"Failed to list containers: {e}")
            return []

    async def get_container_details(self, container_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific container"""
        if not self._check_docker_available():
            return None
        
        try:
            container = self.client.containers.get(container_id)
            
            # Get detailed container information
            details = {
                "id": container.id,
                "short_id": container.short_id,
                "name": container.name,
                "image": container.image.tags[0] if container.image.tags else container.image.id,
                "status": container.status,
                "state": container.attrs.get('State', {}),
                "created": container.attrs.get('Created', ''),
                "started_at": container.attrs.get('State', {}).get('StartedAt', ''),
                "finished_at": container.attrs.get('State', {}).get('FinishedAt', ''),
                "ports": self.docker_utils.parse_container_ports(container.attrs.get('NetworkSettings', {}).get('Ports', {})),
                "environment": self.docker_utils.parse_container_environment(container.attrs.get('Config', {}).get('Env', [])),
                "volumes": self.docker_utils.parse_container_volumes(container.attrs.get('Mounts', [])),
                "networks": self.docker_utils.parse_container_networks(container.attrs.get('NetworkSettings', {}).get('Networks', {})),
                "labels": container.attrs.get('Config', {}).get('Labels', {}),
                "uptime": self.docker_utils.calculate_container_uptime(container.attrs.get('State', {}).get('StartedAt', '')),
                "size": container.attrs.get('SizeRootFs', 0),
                "size_formatted": self.docker_utils.format_container_size(container.attrs.get('SizeRootFs', 0)),
                "is_wakedock_managed": self.docker_utils.is_wakedock_managed(container.attrs.get('Config', {}).get('Labels', {})),
                "service_name": self.docker_utils.get_service_name_from_labels(container.attrs.get('Config', {}).get('Labels', {})),
                "config": container.attrs.get('Config', {}),
                "host_config": container.attrs.get('HostConfig', {}),
                "network_settings": container.attrs.get('NetworkSettings', {}),
                "platform": container.attrs.get('Platform', ''),
                "driver": container.attrs.get('Driver', ''),
                "mount_label": container.attrs.get('MountLabel', ''),
                "process_label": container.attrs.get('ProcessLabel', ''),
                "app_armor_profile": container.attrs.get('AppArmorProfile', ''),
                "exec_ids": container.attrs.get('ExecIDs', []),
                "log_path": container.attrs.get('LogPath', ''),
                "restart_count": container.attrs.get('RestartCount', 0),
                "args": container.attrs.get('Args', []),
                "exec_driver": container.attrs.get('ExecDriver', ''),
                "host_name_path": container.attrs.get('HostnamePath', ''),
                "hosts_path": container.attrs.get('HostsPath', ''),
                "resolv_conf_path": container.attrs.get('ResolvConfPath', ''),
                "seccomp_profile": container.attrs.get('SeccompProfile', ''),
                "no_new_privileges": container.attrs.get('NoNewPrivileges', False)
            }
            
            return details
            
        except docker.errors.NotFound:
            logger.warning(f"Container {container_id} not found")
            return None
        except Exception as e:
            logger.error(f"Failed to get container details for {container_id}: {e}")
            return None

    async def restart_service(self, service_id: str) -> bool:
        """Restart a service"""
        service = self.services.get(service_id)
        if not service:
            return False
        
        logger.info(f"Restarting service: {service['name']}")
        
        try:
            # Stop the service first
            stop_success = await self.sleep_service(service_id)
            if not stop_success:
                logger.error(f"Failed to stop service {service['name']} before restart")
                return False
            
            # Wait a moment for cleanup
            await asyncio.sleep(1)
            
            # Start the service again
            start_success = await self.wake_service(service_id)
            if start_success:
                logger.info(f"Successfully restarted service: {service['name']}")
                return True
            else:
                logger.error(f"Failed to start service {service['name']} after restart")
                return False
                
        except Exception as e:
            logger.error(f"Failed to restart service {service['name']}: {str(e)}")
            return False

    async def restart_container(self, container_id: str) -> bool:
        """Restart a specific container"""
        if not self._check_docker_available():
            return False
        
        try:
            container = self.client.containers.get(container_id)
            container.restart()
            logger.info(f"Successfully restarted container: {container.name}")
            return True
            
        except docker.errors.NotFound:
            logger.warning(f"Container {container_id} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to restart container {container_id}: {e}")
            return False

    async def start_container(self, container_id: str) -> bool:
        """Start a specific container"""
        if not self._check_docker_available():
            return False
        
        try:
            container = self.client.containers.get(container_id)
            container.start()
            logger.info(f"Successfully started container: {container.name}")
            return True
            
        except docker.errors.NotFound:
            logger.warning(f"Container {container_id} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to start container {container_id}: {e}")
            return False

    async def stop_container(self, container_id: str) -> bool:
        """Stop a specific container"""
        if not self._check_docker_available():
            return False
        
        try:
            container = self.client.containers.get(container_id)
            container.stop()
            logger.info(f"Successfully stopped container: {container.name}")
            return True
            
        except docker.errors.NotFound:
            logger.warning(f"Container {container_id} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to stop container {container_id}: {e}")
            return False

    async def remove_container(self, container_id: str, force: bool = False) -> bool:
        """Remove a specific container"""
        if not self._check_docker_available():
            return False
        
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=force)
            logger.info(f"Successfully removed container: {container.name}")
            return True
            
        except docker.errors.NotFound:
            logger.warning(f"Container {container_id} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to remove container {container_id}: {e}")
            return False

    async def get_container_logs(self, container_id: str, tail: int = 100, since: Optional[str] = None) -> Optional[str]:
        """Get logs from a specific container"""
        if not self._check_docker_available():
            return None
        
        try:
            container = self.client.containers.get(container_id)
            logs = container.logs(tail=tail, since=since, timestamps=True)
            
            # Decode logs if they're bytes
            if isinstance(logs, bytes):
                logs = logs.decode('utf-8', errors='ignore')
            
            return logs
            
        except docker.errors.NotFound:
            logger.warning(f"Container {container_id} not found")
            return None
        except Exception as e:
            logger.error(f"Failed to get logs for container {container_id}: {e}")
            return None

    async def get_container_stats(self, container_id: str) -> Optional[Dict[str, Any]]:
        """Get resource usage statistics for a container"""
        if not self._check_docker_available():
            return None
        
        try:
            container = self.client.containers.get(container_id)
            stats = container.stats(stream=False)
            
            # Parse stats using docker utils
            parsed_stats = self.docker_utils.parse_docker_stats(stats)
            return parsed_stats
            
        except docker.errors.NotFound:
            logger.warning(f"Container {container_id} not found")
            return None
        except Exception as e:
            logger.error(f"Failed to get stats for container {container_id}: {e}")
            return None

    async def list_images(self) -> List[Dict[str, Any]]:
        """List all Docker images"""
        if not self._check_docker_available():
            return []
        
        try:
            images = self.client.images.list()
            image_list = []
            
            for image in images:
                image_info = {
                    "id": image.id,
                    "short_id": image.short_id,
                    "tags": image.tags,
                    "created": image.attrs.get('Created', ''),
                    "size": image.attrs.get('Size', 0),
                    "size_formatted": self.docker_utils.format_container_size(image.attrs.get('Size', 0)),
                    "virtual_size": image.attrs.get('VirtualSize', 0),
                    "virtual_size_formatted": self.docker_utils.format_container_size(image.attrs.get('VirtualSize', 0)),
                    "labels": image.attrs.get('Config', {}).get('Labels', {}) or {},
                    "parent": image.attrs.get('Parent', ''),
                    "comment": image.attrs.get('Comment', ''),
                    "author": image.attrs.get('Author', ''),
                    "architecture": image.attrs.get('Architecture', ''),
                    "os": image.attrs.get('Os', ''),
                    "docker_version": image.attrs.get('DockerVersion', ''),
                    "config": image.attrs.get('Config', {}),
                    "container": image.attrs.get('Container', ''),
                    "container_config": image.attrs.get('ContainerConfig', {}),
                    "graph_driver": image.attrs.get('GraphDriver', {}),
                    "root_fs": image.attrs.get('RootFS', {}),
                    "metadata": image.attrs.get('Metadata', {})
                }
                image_list.append(image_info)
            
            return image_list
            
        except Exception as e:
            logger.error(f"Failed to list images: {e}")
            return []

    async def pull_image(self, image_name: str, tag: str = "latest") -> bool:
        """Pull a Docker image"""
        if not self._check_docker_available():
            return False
        
        try:
            full_image_name = f"{image_name}:{tag}"
            logger.info(f"Pulling image: {full_image_name}")
            
            image = self.client.images.pull(image_name, tag=tag)
            logger.info(f"Successfully pulled image: {full_image_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pull image {image_name}:{tag}: {e}")
            return False

    async def remove_image(self, image_id: str, force: bool = False) -> bool:
        """Remove a Docker image"""
        if not self._check_docker_available():
            return False
        
        try:
            self.client.images.remove(image_id, force=force)
            logger.info(f"Successfully removed image: {image_id}")
            return True
            
        except docker.errors.ImageNotFound:
            logger.warning(f"Image {image_id} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to remove image {image_id}: {e}")
            return False

    async def list_networks(self) -> List[Dict[str, Any]]:
        """List all Docker networks"""
        if not self._check_docker_available():
            return []
        
        try:
            networks = self.client.networks.list()
            network_list = []
            
            for network in networks:
                network_info = {
                    "id": network.id,
                    "short_id": network.short_id,
                    "name": network.name,
                    "driver": network.attrs.get('Driver', ''),
                    "scope": network.attrs.get('Scope', ''),
                    "internal": network.attrs.get('Internal', False),
                    "attachable": network.attrs.get('Attachable', False),
                    "ingress": network.attrs.get('Ingress', False),
                    "created": network.attrs.get('Created', ''),
                    "labels": network.attrs.get('Labels', {}) or {},
                    "containers": network.attrs.get('Containers', {}),
                    "options": network.attrs.get('Options', {}),
                    "config": network.attrs.get('IPAM', {}).get('Config', []) if network.attrs.get('IPAM') else [],
                    "enable_ipv6": network.attrs.get('EnableIPv6', False)
                }
                network_list.append(network_info)
            
            return network_list
            
        except Exception as e:
            logger.error(f"Failed to list networks: {e}")
            return []

    async def list_volumes(self) -> List[Dict[str, Any]]:
        """List all Docker volumes"""
        if not self._check_docker_available():
            return []
        
        try:
            volumes = self.client.volumes.list()
            volume_list = []
            
            for volume in volumes:
                volume_info = {
                    "name": volume.name,
                    "driver": volume.attrs.get('Driver', ''),
                    "mountpoint": volume.attrs.get('Mountpoint', ''),
                    "created": volume.attrs.get('CreatedAt', ''),
                    "labels": volume.attrs.get('Labels', {}) or {},
                    "options": volume.attrs.get('Options', {}),
                    "scope": volume.attrs.get('Scope', ''),
                    "status": volume.attrs.get('Status', {}),
                    "usage_data": volume.attrs.get('UsageData', {})
                }
                volume_list.append(volume_info)
            
            return volume_list
            
        except Exception as e:
            logger.error(f"Failed to list volumes: {e}")
            return []

    async def get_docker_system_info(self) -> Dict[str, Any]:
        """Get Docker system information"""
        if not self._check_docker_available():
            return {}
        
        try:
            return self.docker_utils.get_docker_info()
        except Exception as e:
            logger.error(f"Failed to get Docker system info: {e}")
            return {}

    def _check_docker_available(self) -> bool:
        """Check if Docker client is available"""
        if self.client is None:
            logger.warning("⚠️ Docker client not available - operations will be skipped")
            return False
        return True
