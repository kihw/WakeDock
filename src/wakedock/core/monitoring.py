"""
Monitoring service for tracking service usage and auto-shutdown
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import time

from wakedock.core.orchestrator import DockerOrchestrator
from wakedock.config import get_settings

logger = logging.getLogger(__name__)


class MonitoringService:
    """Service for monitoring containers and handling auto-shutdown"""
    
    def __init__(self):
        self.settings = get_settings()
        self.orchestrator: DockerOrchestrator = None
        self.monitoring_task: asyncio.Task = None
        self.running = False
        self.metrics_history: Dict[str, List[Dict[str, Any]]] = {}
    
    async def start(self):
        """Start the monitoring service"""
        logger.info("Starting monitoring service...")
        self.running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    async def stop(self):
        """Stop the monitoring service"""
        logger.info("Stopping monitoring service...")
        self.running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
    
    def set_orchestrator(self, orchestrator: DockerOrchestrator):
        """Set the orchestrator instance"""
        self.orchestrator = orchestrator
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                await self._collect_metrics()
                await self._check_auto_shutdown()
                await asyncio.sleep(self.settings.monitoring.collect_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(30)  # Wait before retrying
    
    async def _collect_metrics(self):
        """Collect metrics for all running services"""
        if not self.orchestrator:
            return
        
        services = await self.orchestrator.list_services()
        
        for service in services:
            if service["status"] == "running":
                try:
                    stats = await self.orchestrator.get_service_stats(service["id"])
                    if stats:
                        self._store_metrics(service["id"], stats)
                except Exception as e:
                    logger.error(f"Failed to collect metrics for {service['name']}: {str(e)}")
    
    def _store_metrics(self, service_id: str, stats: Dict[str, Any]):
        """Store metrics in history"""
        if service_id not in self.metrics_history:
            self.metrics_history[service_id] = []
        
        # Add timestamp if not present
        if "timestamp" not in stats:
            stats["timestamp"] = datetime.now()
        
        self.metrics_history[service_id].append(stats)
        
        # Keep only recent metrics (based on retention period)
        retention_days = int(self.settings.monitoring.metrics_retention.replace("d", ""))
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        self.metrics_history[service_id] = [
            metric for metric in self.metrics_history[service_id]
            if metric["timestamp"] > cutoff_date
        ]
    
    async def _check_auto_shutdown(self):
        """Check services for auto-shutdown conditions"""
        if not self.orchestrator:
            return
        
        services = await self.orchestrator.list_services()
        
        for service in services:
            if service["status"] == "running":
                try:
                    should_shutdown = await self._should_shutdown_service(service)
                    if should_shutdown:
                        logger.info(f"Auto-shutting down service: {service['name']}")
                        await self.orchestrator.sleep_service(service["id"])
                except Exception as e:
                    logger.error(f"Error checking auto-shutdown for {service['name']}: {str(e)}")
    
    async def _should_shutdown_service(self, service: Dict[str, Any]) -> bool:
        """Check if a service should be shut down"""
        auto_shutdown = service.get("auto_shutdown", {})
        
        # Check inactivity timeout
        inactive_minutes = auto_shutdown.get("inactive_minutes", 30)
        if service.get("last_accessed"):
            last_access = service["last_accessed"]
            if isinstance(last_access, str):
                last_access = datetime.fromisoformat(last_access.replace("Z", "+00:00"))
            
            inactive_time = datetime.now() - last_access
            if inactive_time > timedelta(minutes=inactive_minutes):
                logger.info(f"Service {service['name']} inactive for {inactive_time}")
                return True
        
        # Check resource usage thresholds
        cpu_threshold = auto_shutdown.get("cpu_threshold", 5.0)
        memory_threshold = auto_shutdown.get("memory_threshold", 100)  # MB
        check_interval = auto_shutdown.get("check_interval", 300)  # seconds
        
        # Get recent metrics
        service_metrics = self.metrics_history.get(service["id"], [])
        if not service_metrics:
            return False
        
        # Check if resource usage has been consistently low
        cutoff_time = datetime.now() - timedelta(seconds=check_interval)
        recent_metrics = [
            metric for metric in service_metrics
            if metric["timestamp"] > cutoff_time
        ]
        
        if len(recent_metrics) < 3:  # Need at least 3 data points
            return False
        
        # Check CPU threshold
        low_cpu_count = sum(1 for metric in recent_metrics if metric.get("cpu_percent", 100) < cpu_threshold)
        cpu_ratio = low_cpu_count / len(recent_metrics)
        
        # Check memory threshold (convert to MB)
        memory_threshold_bytes = memory_threshold * 1024 * 1024
        low_memory_count = sum(1 for metric in recent_metrics if metric.get("memory_usage", float('inf')) < memory_threshold_bytes)
        memory_ratio = low_memory_count / len(recent_metrics)
        
        # Shutdown if both CPU and memory usage are consistently low
        if cpu_ratio >= 0.8 and memory_ratio >= 0.8:
            logger.info(f"Service {service['name']} has low resource usage - CPU: {cpu_ratio*100:.1f}%, Memory: {memory_ratio*100:.1f}%")
            return True
        
        return False
    
    async def get_service_metrics(self, service_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get metrics history for a service"""
        if service_id not in self.metrics_history:
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            metric for metric in self.metrics_history[service_id]
            if metric["timestamp"] > cutoff_time
        ]
    
    async def get_system_overview(self) -> Dict[str, Any]:
        """Get system overview metrics"""
        import psutil
        import time
        
        # Get services data
        if self.orchestrator:
            services = await self.orchestrator.list_services()
            total_services = len(services)
            running_services = len([s for s in services if s["status"] == "running"])
            stopped_services = len([s for s in services if s["status"] == "stopped"])
            error_services = len([s for s in services if s["status"] == "error"])
            
            # Calculate total resource usage
            total_cpu = 0
            total_memory = 0
            
            for service in services:
                if service["status"] == "running" and service.get("resource_usage"):
                    total_cpu += service["resource_usage"].get("cpu_percent", 0)
                    total_memory += service["resource_usage"].get("memory_usage", 0)
        else:
            total_services = running_services = stopped_services = error_services = 0
            total_cpu = total_memory = 0
        
        # Get system stats
        try:
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            uptime = int(time.time() - psutil.boot_time())
        except Exception:
            cpu_usage = 0.0
            memory = type('obj', (object,), {'percent': 0.0})()
            disk = type('obj', (object,), {'percent': 0.0})()
            uptime = 0
        
        # Get Docker status and detailed info
        docker_status = "healthy"
        docker_version = "unknown"
        docker_api_version = "unknown"
        docker_containers = 0
        docker_images = 0
        docker_networks = 0
        docker_volumes = 0
        
        if self.orchestrator and hasattr(self.orchestrator, 'client'):
            try:
                # Get Docker version
                version_info = self.orchestrator.client.version()
                docker_version = version_info.get('Version', 'unknown')
                docker_api_version = version_info.get('ApiVersion', 'unknown')
                
                # Get Docker system info
                docker_info = await self.orchestrator.get_docker_system_info()
                if docker_info:
                    docker_containers = docker_info.get('containers_running', 0)
                    docker_images = docker_info.get('images', 0)
                
                # Get counts for networks and volumes
                networks = await self.orchestrator.list_networks()
                volumes = await self.orchestrator.list_volumes()
                docker_networks = len(networks) if networks else 0
                docker_volumes = len(volumes) if volumes else 0
                
            except Exception as e:
                logger.warning(f"Error getting Docker info: {e}")
                docker_status = "unhealthy"
        
        return {
            "services": {
                "total": total_services,
                "running": running_services,
                "stopped": stopped_services,
                "error": error_services
            },
            "system": {
                "cpu_usage": round(cpu_usage, 2),
                "memory_usage": round(memory.percent, 2),
                "disk_usage": round(disk.percent, 2),
                "uptime": uptime
            },
            "docker": {
                "version": docker_version,
                "api_version": docker_api_version,
                "status": docker_status,
                "containers": docker_containers,
                "images": docker_images,
                "networks": docker_networks,
                "volumes": docker_volumes
            },
            "caddy": {
                "version": "2.0",  # Could be fetched from Caddy API
                "status": "healthy",  # Could be checked via health endpoint
                "active_routes": 3  # Base routes: API, dashboard, health
            }
        }
    
    async def get_container_metrics(self, container_id: str) -> Dict[str, Any]:
        """Get real-time metrics for a specific container"""
        if not self.orchestrator:
            return {}
        
        try:
            stats = await self.orchestrator.get_container_stats(container_id)
            container_details = await self.orchestrator.get_container_details(container_id)
            
            if not stats or not container_details:
                return {}
            
            return {
                "container_id": container_id,
                "name": container_details.get("name", "unknown"),
                "image": container_details.get("image", "unknown"),
                "status": container_details.get("status", "unknown"),
                "uptime": container_details.get("uptime", 0),
                "metrics": {
                    "cpu_usage": stats.get("cpu_usage", 0),
                    "memory_usage": stats.get("memory_usage", 0),
                    "memory_limit": stats.get("memory_limit", 0),
                    "memory_percent": stats.get("memory_percent", 0),
                    "network_rx": stats.get("network_rx", 0),
                    "network_tx": stats.get("network_tx", 0),
                    "block_read": stats.get("block_read", 0),
                    "block_write": stats.get("block_write", 0)
                },
                "timestamp": stats.get("timestamp", datetime.now().isoformat())
            }
        except Exception as e:
            logger.error(f"Error getting container metrics: {e}")
            return {}
    
    async def get_all_container_metrics(self) -> List[Dict[str, Any]]:
        """Get metrics for all containers"""
        if not self.orchestrator:
            return []
        
        try:
            containers = await self.orchestrator.list_containers(all_containers=False)
            metrics = []
            
            for container in containers:
                container_metrics = await self.get_container_metrics(container["id"])
                if container_metrics:
                    metrics.append(container_metrics)
            
            return metrics
        except Exception as e:
            logger.error(f"Error getting all container metrics: {e}")
            return []
    
    async def get_resource_alerts(self) -> List[Dict[str, Any]]:
        """Get current resource alerts"""
        alerts = []
        
        try:
            # System resource alerts
            import psutil
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # High CPU usage alert
            if cpu_usage > 80:
                alerts.append({
                    "type": "system",
                    "level": "warning" if cpu_usage < 90 else "critical",
                    "message": f"High CPU usage: {cpu_usage:.1f}%",
                    "timestamp": datetime.now().isoformat()
                })
            
            # High memory usage alert
            if memory.percent > 80:
                alerts.append({
                    "type": "system",
                    "level": "warning" if memory.percent < 90 else "critical",
                    "message": f"High memory usage: {memory.percent:.1f}%",
                    "timestamp": datetime.now().isoformat()
                })
            
            # High disk usage alert
            if disk.percent > 80:
                alerts.append({
                    "type": "system",
                    "level": "warning" if disk.percent < 90 else "critical",
                    "message": f"High disk usage: {disk.percent:.1f}%",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Container resource alerts
            if self.orchestrator:
                services = await self.orchestrator.list_services()
                for service in services:
                    if service["status"] == "running":
                        try:
                            stats = await self.orchestrator.get_service_stats(service["id"])
                            if stats:
                                # High container CPU usage
                                cpu_percent = stats.get("cpu_percent", 0)
                                if cpu_percent > 80:
                                    alerts.append({
                                        "type": "container",
                                        "service_id": service["id"],
                                        "service_name": service["name"],
                                        "level": "warning" if cpu_percent < 90 else "critical",
                                        "message": f"High CPU usage in {service['name']}: {cpu_percent:.1f}%",
                                        "timestamp": datetime.now().isoformat()
                                    })
                                
                                # High container memory usage
                                memory_percent = stats.get("memory_percent", 0)
                                if memory_percent > 80:
                                    alerts.append({
                                        "type": "container",
                                        "service_id": service["id"],
                                        "service_name": service["name"],
                                        "level": "warning" if memory_percent < 90 else "critical",
                                        "message": f"High memory usage in {service['name']}: {memory_percent:.1f}%",
                                        "timestamp": datetime.now().isoformat()
                                    })
                        except Exception as e:
                            logger.warning(f"Error checking alerts for {service['name']}: {e}")
            
            # Docker daemon alerts
            if self.orchestrator and hasattr(self.orchestrator, 'client'):
                try:
                    self.orchestrator.client.ping()
                except Exception:
                    alerts.append({
                        "type": "docker",
                        "level": "critical",
                        "message": "Docker daemon is not responding",
                        "timestamp": datetime.now().isoformat()
                    })
            
        except Exception as e:
            logger.error(f"Error getting resource alerts: {e}")
        
        return alerts
    
    def get_metrics_summary(self, service_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get a summary of metrics for a service over a time period"""
        if service_id not in self.metrics_history:
            return {}
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [
            metric for metric in self.metrics_history[service_id]
            if metric["timestamp"] > cutoff_time
        ]
        
        if not recent_metrics:
            return {}
        
        # Calculate averages, min, max
        cpu_values = [m.get("cpu_percent", 0) for m in recent_metrics]
        memory_values = [m.get("memory_usage", 0) for m in recent_metrics]
        
        return {
            "service_id": service_id,
            "period_hours": hours,
            "data_points": len(recent_metrics),
            "cpu": {
                "avg": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                "min": min(cpu_values) if cpu_values else 0,
                "max": max(cpu_values) if cpu_values else 0
            },
            "memory": {
                "avg": sum(memory_values) / len(memory_values) if memory_values else 0,
                "min": min(memory_values) if memory_values else 0,
                "max": max(memory_values) if memory_values else 0
            },
            "first_timestamp": recent_metrics[0]["timestamp"] if recent_metrics else None,
            "last_timestamp": recent_metrics[-1]["timestamp"] if recent_metrics else None
        }
