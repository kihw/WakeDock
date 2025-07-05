"""
Prometheus Metrics Export

Provides comprehensive Prometheus metrics for WakeDock including:
- System metrics (CPU, memory, disk, network)
- Service metrics (containers, health, performance)
- Application metrics (API calls, errors, response times)
- Custom business metrics
"""

import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from collections import defaultdict
import asyncio

try:
    from prometheus_client import (
        Counter, Histogram, Gauge, Info, Summary,
        CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST,
        multiprocess, values, start_http_server
    )
    from prometheus_client.core import CollectorRegistry
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Fallback classes for when prometheus_client is not available
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def dec(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    
    class Summary:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    
    class Info:
        def __init__(self, *args, **kwargs): pass
        def info(self, *args, **kwargs): pass
    
    class CollectorRegistry:
        def __init__(self): pass
        def register(self, *args): pass
        def unregister(self, *args): pass
    
    def generate_latest(registry): return b""
    CONTENT_TYPE_LATEST = "text/plain"

import psutil
import docker

logger = logging.getLogger(__name__)


class MetricsRegistry:
    """Central registry for all Prometheus metrics"""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        self._metrics = {}
        self._initialized = False
        
        if PROMETHEUS_AVAILABLE:
            self._setup_metrics()
        else:
            logger.warning("Prometheus client not available, metrics collection disabled")
    
    def _setup_metrics(self):
        """Setup all Prometheus metrics"""
        # System metrics
        self.system_cpu_usage = Gauge(
            'wakedock_system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )
        
        self.system_memory_usage = Gauge(
            'wakedock_system_memory_usage_percent',
            'System memory usage percentage',
            registry=self.registry
        )
        
        self.system_disk_usage = Gauge(
            'wakedock_system_disk_usage_percent',
            'System disk usage percentage',
            ['path'],
            registry=self.registry
        )
        
        self.system_network_bytes = Counter(
            'wakedock_system_network_bytes_total',
            'Total network bytes transferred',
            ['direction'],
            registry=self.registry
        )
        
        # Docker metrics
        self.docker_containers_total = Gauge(
            'wakedock_docker_containers_total',
            'Total number of Docker containers',
            ['status'],
            registry=self.registry
        )
        
        self.docker_images_total = Gauge(
            'wakedock_docker_images_total',
            'Total number of Docker images',
            registry=self.registry
        )
        
        # Service metrics
        self.service_status = Gauge(
            'wakedock_service_status',
            'Service status (1=running, 0=stopped)',
            ['service_name', 'service_id'],
            registry=self.registry
        )
        
        self.service_cpu_usage = Gauge(
            'wakedock_service_cpu_usage_percent',
            'Service CPU usage percentage',
            ['service_name', 'service_id'],
            registry=self.registry
        )
        
        self.service_memory_usage = Gauge(
            'wakedock_service_memory_usage_bytes',
            'Service memory usage in bytes',
            ['service_name', 'service_id'],
            registry=self.registry
        )
        
        self.service_network_bytes = Counter(
            'wakedock_service_network_bytes_total',
            'Total service network bytes',
            ['service_name', 'service_id', 'direction'],
            registry=self.registry
        )
        
        # API metrics
        self.api_requests_total = Counter(
            'wakedock_api_requests_total',
            'Total API requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self.api_request_duration = Histogram(
            'wakedock_api_request_duration_seconds',
            'API request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        self.api_active_connections = Gauge(
            'wakedock_api_active_connections',
            'Number of active API connections',
            registry=self.registry
        )
        
        # WebSocket metrics
        self.websocket_connections = Gauge(
            'wakedock_websocket_connections_total',
            'Total WebSocket connections',
            ['user_id'],
            registry=self.registry
        )
        
        self.websocket_messages_total = Counter(
            'wakedock_websocket_messages_total',
            'Total WebSocket messages',
            ['direction', 'type'],
            registry=self.registry
        )
        
        # Cache metrics
        self.cache_operations_total = Counter(
            'wakedock_cache_operations_total',
            'Total cache operations',
            ['operation', 'backend'],
            registry=self.registry
        )
        
        self.cache_hit_rate = Gauge(
            'wakedock_cache_hit_rate',
            'Cache hit rate percentage',
            ['backend'],
            registry=self.registry
        )
        
        self.cache_size_bytes = Gauge(
            'wakedock_cache_size_bytes',
            'Cache size in bytes',
            ['backend'],
            registry=self.registry
        )
        
        # Application info
        self.app_info = Info(
            'wakedock_app_info',
            'Application information',
            registry=self.registry
        )
        
        self.app_uptime_seconds = Gauge(
            'wakedock_app_uptime_seconds',
            'Application uptime in seconds',
            registry=self.registry
        )
        
        # Health checks
        self.health_check_status = Gauge(
            'wakedock_health_check_status',
            'Health check status (1=healthy, 0=unhealthy)',
            ['component'],
            registry=self.registry
        )
        
        self._initialized = True
    
    def is_available(self) -> bool:
        """Check if Prometheus metrics are available"""
        return PROMETHEUS_AVAILABLE and self._initialized
    
    def get_registry(self) -> CollectorRegistry:
        """Get the Prometheus registry"""
        return self.registry
    
    def record_api_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record an API request"""
        if not self.is_available():
            return
            
        self.api_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        self.api_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def update_system_metrics(self, cpu: float, memory: float, disk: Dict[str, float]):
        """Update system metrics"""
        if not self.is_available():
            return
            
        self.system_cpu_usage.set(cpu)
        self.system_memory_usage.set(memory)
        
        for path, usage in disk.items():
            self.system_disk_usage.labels(path=path).set(usage)
    
    def update_docker_metrics(self, containers: Dict[str, int], images: int):
        """Update Docker metrics"""
        if not self.is_available():
            return
            
        for status, count in containers.items():
            self.docker_containers_total.labels(status=status).set(count)
        
        self.docker_images_total.set(images)
    
    def update_service_metrics(self, service_name: str, service_id: str, 
                             status: bool, cpu: float, memory: int):
        """Update service metrics"""
        if not self.is_available():
            return
            
        self.service_status.labels(
            service_name=service_name,
            service_id=service_id
        ).set(1 if status else 0)
        
        self.service_cpu_usage.labels(
            service_name=service_name,
            service_id=service_id
        ).set(cpu)
        
        self.service_memory_usage.labels(
            service_name=service_name,
            service_id=service_id
        ).set(memory)
    
    def record_websocket_connection(self, user_id: str, connected: bool):
        """Record WebSocket connection"""
        if not self.is_available():
            return
            
        if connected:
            self.websocket_connections.labels(user_id=user_id).inc()
        else:
            self.websocket_connections.labels(user_id=user_id).dec()
    
    def record_websocket_message(self, direction: str, message_type: str):
        """Record WebSocket message"""
        if not self.is_available():
            return
            
        self.websocket_messages_total.labels(
            direction=direction,
            type=message_type
        ).inc()
    
    def update_cache_metrics(self, backend: str, hit_rate: float, size_bytes: int):
        """Update cache metrics"""
        if not self.is_available():
            return
            
        self.cache_hit_rate.labels(backend=backend).set(hit_rate)
        self.cache_size_bytes.labels(backend=backend).set(size_bytes)
    
    def record_cache_operation(self, operation: str, backend: str):
        """Record cache operation"""
        if not self.is_available():
            return
            
        self.cache_operations_total.labels(
            operation=operation,
            backend=backend
        ).inc()
    
    def set_app_info(self, version: str, commit: str = "", build_date: str = ""):
        """Set application information"""
        if not self.is_available():
            return
            
        self.app_info.info({
            'version': version,
            'commit': commit,
            'build_date': build_date
        })
    
    def update_uptime(self, uptime_seconds: float):
        """Update application uptime"""
        if not self.is_available():
            return
            
        self.app_uptime_seconds.set(uptime_seconds)
    
    def update_health_status(self, component: str, healthy: bool):
        """Update health check status"""
        if not self.is_available():
            return
            
        self.health_check_status.labels(component=component).set(1 if healthy else 0)


class PrometheusExporter:
    """Prometheus metrics exporter"""
    
    def __init__(self, port: int = 9090, host: str = "0.0.0.0"):
        self.port = port
        self.host = host
        self.registry = MetricsRegistry()
        self.docker_client = None
        self._running = False
        self._collection_task = None
        self._start_time = time.time()
        
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.warning(f"Could not connect to Docker: {e}")
    
    async def start(self):
        """Start the Prometheus exporter"""
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus client not available, exporter disabled")
            return
            
        if self._running:
            return
            
        try:
            # Start HTTP server for metrics endpoint
            start_http_server(self.port, self.host, self.registry.get_registry())
            
            # Set initial app info
            self.registry.set_app_info(
                version="1.0.0",
                build_date=datetime.now().isoformat()
            )
            
            # Start background collection
            self._running = True
            self._collection_task = asyncio.create_task(self._collection_loop())
            
            logger.info(f"Prometheus exporter started on {self.host}:{self.port}/metrics")
            
        except Exception as e:
            logger.error(f"Failed to start Prometheus exporter: {e}")
            raise
    
    async def stop(self):
        """Stop the Prometheus exporter"""
        self._running = False
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Prometheus exporter stopped")
    
    async def _collection_loop(self):
        """Background metrics collection loop"""
        while self._running:
            try:
                await self._collect_metrics()
                await asyncio.sleep(15)  # Collect every 15 seconds
                
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(5)
    
    async def _collect_metrics(self):
        """Collect all metrics"""
        # Update uptime
        uptime = time.time() - self._start_time
        self.registry.update_uptime(uptime)
        
        # Collect system metrics
        await self._collect_system_metrics()
        
        # Collect Docker metrics
        if self.docker_client:
            await self._collect_docker_metrics()
        
        # Update health status
        self.registry.update_health_status("prometheus_exporter", True)
    
    async def _collect_system_metrics(self):
        """Collect system metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk_usage = {}
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage[partition.mountpoint] = (usage.used / usage.total) * 100
                except (PermissionError, OSError):
                    continue
            
            # Update metrics
            self.registry.update_system_metrics(
                cpu=cpu_percent,
                memory=memory.percent,
                disk=disk_usage
            )
            
            # Network metrics
            network = psutil.net_io_counters()
            # Note: Counter metrics should be incremented, not set
            # This is a simplified example
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    async def _collect_docker_metrics(self):
        """Collect Docker metrics"""
        try:
            # Container counts by status
            containers = self.docker_client.containers.list(all=True)
            container_counts = defaultdict(int)
            
            for container in containers:
                container_counts[container.status] += 1
            
            # Image count
            images = self.docker_client.images.list()
            
            self.registry.update_docker_metrics(
                containers=dict(container_counts),
                images=len(images)
            )
            
        except Exception as e:
            logger.error(f"Error collecting Docker metrics: {e}")
    
    def get_metrics(self) -> str:
        """Get metrics in Prometheus format"""
        if not self.registry.is_available():
            return ""
            
        return generate_latest(self.registry.get_registry()).decode('utf-8')
    
    def record_api_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record an API request metric"""
        self.registry.record_api_request(method, endpoint, status_code, duration)
    
    def record_websocket_event(self, event_type: str, **kwargs):
        """Record WebSocket event metrics"""
        if event_type == "connection":
            self.registry.record_websocket_connection(
                kwargs.get("user_id", "unknown"),
                kwargs.get("connected", True)
            )
        elif event_type == "message":
            self.registry.record_websocket_message(
                kwargs.get("direction", "unknown"),
                kwargs.get("message_type", "unknown")
            )


# Global exporter instance
_prometheus_exporter: Optional[PrometheusExporter] = None


def get_prometheus_exporter() -> Optional[PrometheusExporter]:
    """Get global Prometheus exporter instance"""
    return _prometheus_exporter


def init_prometheus_exporter(port: int = 9090, host: str = "0.0.0.0") -> PrometheusExporter:
    """Initialize global Prometheus exporter"""
    global _prometheus_exporter
    _prometheus_exporter = PrometheusExporter(port=port, host=host)
    return _prometheus_exporter