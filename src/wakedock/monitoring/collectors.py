"""
Metrics Collectors

Various metrics collectors for different system components:
- System metrics (CPU, memory, disk, network)
- Service metrics (Docker containers, processes)
- Application metrics (custom business metrics)
"""

import asyncio
import logging
import psutil
import docker
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from collections import defaultdict
import time

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Base metrics collector"""
    
    def __init__(self, collection_interval: float = 15.0):
        self.collection_interval = collection_interval
        self._running = False
        self._task = None
        self._callbacks: List[Callable] = []
    
    def subscribe(self, callback: Callable):
        """Subscribe to metrics updates"""
        if callback not in self._callbacks:
            self._callbacks.append(callback)
    
    def unsubscribe(self, callback: Callable):
        """Unsubscribe from metrics updates"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    async def _notify_callbacks(self, metrics: Dict[str, Any]):
        """Notify all callbacks with new metrics"""
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(metrics)
                else:
                    callback(metrics)
            except Exception as e:
                logger.error(f"Error in metrics callback: {e}")
    
    async def start_collection(self):
        """Start metrics collection"""
        if self._running:
            return
            
        self._running = True
        self._task = asyncio.create_task(self._collection_loop())
        logger.info(f"{self.__class__.__name__} started")
    
    async def stop_collection(self):
        """Stop metrics collection"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(f"{self.__class__.__name__} stopped")
    
    async def _collection_loop(self):
        """Collection loop"""
        while self._running:
            try:
                metrics = await self.collect_metrics()
                if metrics:
                    await self._notify_callbacks(metrics)
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error in {self.__class__.__name__} collection loop: {e}")
                await asyncio.sleep(5)  # Short delay before retrying
    
    async def collect_metrics(self) -> Optional[Dict[str, Any]]:
        """Collect metrics - to be implemented by subclasses"""
        raise NotImplementedError


class SystemCollector(MetricsCollector):
    """System metrics collector"""
    
    def __init__(self, collection_interval: float = 15.0):
        super().__init__(collection_interval)
        self._last_network_stats = None
        self._last_disk_stats = None
    
    async def collect_metrics(self) -> Optional[Dict[str, Any]]:
        """Collect system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics
            disk_usage = {}
            disk_io = {}
            
            # Get disk usage for all partitions
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage[partition.mountpoint] = {
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": (usage.used / usage.total) * 100 if usage.total > 0 else 0
                    }
                except (PermissionError, OSError):
                    continue
            
            # Disk I/O stats
            try:
                disk_io_stats = psutil.disk_io_counters()
                if disk_io_stats:
                    disk_io = {
                        "read_bytes": disk_io_stats.read_bytes,
                        "write_bytes": disk_io_stats.write_bytes,
                        "read_count": disk_io_stats.read_count,
                        "write_count": disk_io_stats.write_count
                    }
            except Exception:
                pass
            
            # Network metrics
            network_io = {}
            try:
                network_stats = psutil.net_io_counters()
                if network_stats:
                    network_io = {
                        "bytes_sent": network_stats.bytes_sent,
                        "bytes_recv": network_stats.bytes_recv,
                        "packets_sent": network_stats.packets_sent,
                        "packets_recv": network_stats.packets_recv
                    }
            except Exception:
                pass
            
            # Load average (Unix systems)
            load_avg = None
            try:
                load_avg = psutil.getloadavg()
            except (AttributeError, OSError):
                pass
            
            # Boot time and uptime
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time
            
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "frequency": cpu_freq._asdict() if cpu_freq else None
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "percent": memory.percent,
                    "swap_total": swap.total,
                    "swap_used": swap.used,
                    "swap_percent": swap.percent
                },
                "disk": {
                    "usage": disk_usage,
                    "io": disk_io
                },
                "network": network_io,
                "load_average": load_avg,
                "uptime": uptime
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return None


class ServiceCollector(MetricsCollector):
    """Service/Docker metrics collector"""
    
    def __init__(self, collection_interval: float = 15.0):
        super().__init__(collection_interval)
        self.docker_client = None
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.warning(f"Could not connect to Docker: {e}")
    
    async def collect_metrics(self) -> Optional[Dict[str, Any]]:
        """Collect service metrics"""
        if not self.docker_client:
            return None
            
        try:
            # Container metrics
            containers = self.docker_client.containers.list(all=True)
            container_stats = {}
            container_counts = defaultdict(int)
            
            for container in containers:
                try:
                    # Count by status
                    container_counts[container.status] += 1
                    
                    # Get detailed stats for running containers
                    if container.status == 'running':
                        stats = container.stats(stream=False)
                        
                        # Calculate CPU percentage
                        cpu_percent = 0
                        if 'cpu_stats' in stats and 'precpu_stats' in stats:
                            cpu_stats = stats['cpu_stats']
                            precpu_stats = stats['precpu_stats']
                            
                            cpu_delta = cpu_stats['cpu_usage']['total_usage'] - \
                                       precpu_stats['cpu_usage']['total_usage']
                            system_delta = cpu_stats['system_cpu_usage'] - \
                                          precpu_stats['system_cpu_usage']
                            
                            if system_delta > 0:
                                cpu_percent = (cpu_delta / system_delta) * \
                                            len(cpu_stats['cpu_usage']['percpu_usage']) * 100
                        
                        # Memory usage
                        memory_usage = 0
                        memory_limit = 0
                        if 'memory_stats' in stats:
                            memory_stats = stats['memory_stats']
                            memory_usage = memory_stats.get('usage', 0)
                            memory_limit = memory_stats.get('limit', 0)
                        
                        # Network I/O
                        network_rx = 0
                        network_tx = 0
                        if 'networks' in stats:
                            for interface, net_stats in stats['networks'].items():
                                network_rx += net_stats.get('rx_bytes', 0)
                                network_tx += net_stats.get('tx_bytes', 0)
                        
                        # Block I/O
                        block_read = 0
                        block_write = 0
                        if 'blkio_stats' in stats:
                            blkio_stats = stats['blkio_stats']
                            if 'io_service_bytes_recursive' in blkio_stats:
                                for entry in blkio_stats['io_service_bytes_recursive']:
                                    if entry['op'] == 'Read':
                                        block_read += entry['value']
                                    elif entry['op'] == 'Write':
                                        block_write += entry['value']
                        
                        container_stats[container.id] = {
                            "name": container.name,
                            "image": container.image.tags[0] if container.image.tags else "unknown",
                            "status": container.status,
                            "cpu_percent": cpu_percent,
                            "memory_usage": memory_usage,
                            "memory_limit": memory_limit,
                            "memory_percent": (memory_usage / memory_limit * 100) if memory_limit > 0 else 0,
                            "network_rx_bytes": network_rx,
                            "network_tx_bytes": network_tx,
                            "block_read_bytes": block_read,
                            "block_write_bytes": block_write
                        }
                        
                except Exception as e:
                    logger.error(f"Error getting stats for container {container.name}: {e}")
                    continue
            
            # Image metrics
            images = self.docker_client.images.list()
            image_count = len(images)
            
            # Volume metrics
            volumes = self.docker_client.volumes.list()
            volume_count = len(volumes)
            
            # Network metrics
            networks = self.docker_client.networks.list()
            network_count = len(networks)
            
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "containers": {
                    "stats": container_stats,
                    "counts": dict(container_counts),
                    "total": len(containers)
                },
                "images": {
                    "count": image_count
                },
                "volumes": {
                    "count": volume_count
                },
                "networks": {
                    "count": network_count
                }
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting service metrics: {e}")
            return None


class ApplicationCollector(MetricsCollector):
    """Application-specific metrics collector"""
    
    def __init__(self, collection_interval: float = 30.0):
        super().__init__(collection_interval)
        self.custom_metrics = {}
    
    def set_custom_metric(self, key: str, value: Any, labels: Optional[Dict[str, str]] = None):
        """Set a custom metric value"""
        self.custom_metrics[key] = {
            "value": value,
            "labels": labels or {},
            "timestamp": datetime.now().isoformat()
        }
    
    def increment_counter(self, key: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        if key not in self.custom_metrics:
            self.custom_metrics[key] = {
                "value": 0,
                "labels": labels or {},
                "timestamp": datetime.now().isoformat()
            }
        
        self.custom_metrics[key]["value"] += value
        self.custom_metrics[key]["timestamp"] = datetime.now().isoformat()
    
    async def collect_metrics(self) -> Optional[Dict[str, Any]]:
        """Collect application metrics"""
        try:
            # Process metrics
            process = psutil.Process()
            
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "process": {
                    "pid": process.pid,
                    "memory_info": process.memory_info()._asdict(),
                    "cpu_percent": process.cpu_percent(),
                    "num_threads": process.num_threads(),
                    "open_files": len(process.open_files()),
                    "connections": len(process.connections())
                },
                "custom": self.custom_metrics.copy()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")
            return None


# Global collector instances
_system_collector: Optional[SystemCollector] = None
_service_collector: Optional[ServiceCollector] = None
_application_collector: Optional[ApplicationCollector] = None


def get_system_collector() -> Optional[SystemCollector]:
    """Get global system collector instance"""
    return _system_collector


def get_service_collector() -> Optional[ServiceCollector]:
    """Get global service collector instance"""
    return _service_collector


def get_application_collector() -> Optional[ApplicationCollector]:
    """Get global application collector instance"""
    return _application_collector


def init_collectors(system_interval: float = 15.0, 
                   service_interval: float = 15.0,
                   application_interval: float = 30.0) -> tuple:
    """Initialize all collectors"""
    global _system_collector, _service_collector, _application_collector
    
    _system_collector = SystemCollector(system_interval)
    _service_collector = ServiceCollector(service_interval)
    _application_collector = ApplicationCollector(application_interval)
    
    return _system_collector, _service_collector, _application_collector