"""
Analytics Data Collector

Collects metrics and events from various sources including:
- System metrics (CPU, memory, disk, network)
- Service metrics (performance, usage, errors)  
- User activity events
- Docker container events
- API usage metrics
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict, deque
import psutil
import docker

from .types import (
    AnalyticsEvent, MetricPoint, ServiceMetrics, SystemMetrics,
    MetricType, AnalyticsConfig, UsageStats, PerformanceMetrics
)
from ..core.orchestrator import DockerOrchestrator
from ..api.websocket.manager import WebSocketManager

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects system and service metrics"""
    
    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.docker_client = docker.from_env()
        self.orchestrator = DockerOrchestrator()
        self._running = False
        self._collection_task = None
        self._metrics_buffer = deque(maxlen=10000)
        
    async def start(self):
        """Start metrics collection"""
        if self._running:
            return
            
        self._running = True
        self._collection_task = asyncio.create_task(self._collection_loop())
        logger.info("Metrics collection started")
        
    async def stop(self):
        """Stop metrics collection"""
        self._running = False
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
        logger.info("Metrics collection stopped")
        
    async def _collection_loop(self):
        """Main collection loop"""
        while self._running:
            try:
                # Collect system metrics
                system_metrics = await self._collect_system_metrics()
                if system_metrics:
                    self._buffer_metrics("system", system_metrics)
                
                # Collect service metrics
                service_metrics = await self._collect_service_metrics()
                for service_id, metrics in service_metrics.items():
                    self._buffer_metrics(f"service_{service_id}", metrics)
                    
                # Collect Docker metrics
                docker_metrics = await self._collect_docker_metrics()
                if docker_metrics:
                    self._buffer_metrics("docker", docker_metrics)
                    
                await asyncio.sleep(self.config.collection_interval)
                
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(5)  # Brief pause on error
                
    async def _collect_system_metrics(self) -> Optional[SystemMetrics]:
        """Collect system-wide metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_times = psutil.cpu_times()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics
            disk_usage = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # Network metrics
            network_io = psutil.net_io_counters()
            
            # Service count
            services = await self.orchestrator.list_services()
            active_services = len([s for s in services if s.get('status') == 'running'])
            
            return SystemMetrics(
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                disk_usage=(disk_usage.used / disk_usage.total) * 100,
                network_io={
                    "bytes_sent": float(network_io.bytes_sent),
                    "bytes_recv": float(network_io.bytes_recv),
                    "packets_sent": float(network_io.packets_sent),
                    "packets_recv": float(network_io.packets_recv)
                },
                active_services=active_services,
                total_requests=0,  # Will be populated from API metrics
                error_rate=0.0,
                avg_response_time=0.0
            )
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return None
            
    async def _collect_service_metrics(self) -> Dict[str, ServiceMetrics]:
        """Collect metrics for all services"""
        metrics = {}
        
        try:
            services = await self.orchestrator.list_services()
            
            for service in services:
                service_id = service.get('id')
                if not service_id:
                    continue
                    
                try:
                    # Get container stats
                    container_stats = await self._get_container_stats(service_id)
                    if container_stats:
                        metrics[service_id] = ServiceMetrics(
                            service_id=service_id,
                            service_name=service.get('name', 'unknown'),
                            cpu_usage=container_stats.get('cpu_percent', 0.0),
                            memory_usage=container_stats.get('memory_percent', 0.0),
                            network_io=container_stats.get('network_io', {}),
                            disk_io=container_stats.get('disk_io', {}),
                            request_count=0,  # Will be populated from API metrics
                            error_count=0,
                            response_time_avg=0.0,
                            uptime=container_stats.get('uptime', 0.0)
                        )
                        
                except Exception as e:
                    logger.error(f"Error collecting metrics for service {service_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error collecting service metrics: {e}")
            
        return metrics
        
    async def _collect_docker_metrics(self) -> Optional[Dict[str, Any]]:
        """Collect Docker daemon metrics"""
        try:
            info = self.docker_client.info()
            version = self.docker_client.version()
            
            # Container counts
            containers = self.docker_client.containers.list(all=True)
            running_containers = len([c for c in containers if c.status == 'running'])
            
            # Image counts
            images = self.docker_client.images.list()
            
            return {
                "containers_total": len(containers),
                "containers_running": running_containers,
                "images_total": len(images),
                "docker_version": version.get('Version', 'unknown'),
                "storage_driver": info.get('Driver', 'unknown'),
                "cpu_count": info.get('NCPU', 0),
                "memory_total": info.get('MemTotal', 0)
            }
            
        except Exception as e:
            logger.error(f"Error collecting Docker metrics: {e}")
            return None
            
    async def _get_container_stats(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific container"""
        try:
            containers = self.docker_client.containers.list(
                filters={"label": f"wakedock.service.id={service_id}"}
            )
            
            if not containers:
                return None
                
            container = containers[0]
            stats = container.stats(stream=False)
            
            # Calculate CPU percentage
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            
            cpu_percent = 0.0
            if system_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * 100.0
                
            # Calculate memory percentage
            memory_usage = stats['memory_stats']['usage']
            memory_limit = stats['memory_stats']['limit']
            memory_percent = (memory_usage / memory_limit) * 100.0
            
            # Network I/O
            network_io = {}
            if 'networks' in stats:
                for interface, data in stats['networks'].items():
                    network_io[f"{interface}_rx_bytes"] = data['rx_bytes']
                    network_io[f"{interface}_tx_bytes"] = data['tx_bytes']
                    
            # Block I/O
            disk_io = {}
            if 'blkio_stats' in stats and 'io_service_bytes_recursive' in stats['blkio_stats']:
                for entry in stats['blkio_stats']['io_service_bytes_recursive']:
                    if entry['op'] == 'Read':
                        disk_io['read_bytes'] = entry['value']
                    elif entry['op'] == 'Write':
                        disk_io['write_bytes'] = entry['value']
                        
            # Uptime
            created = container.attrs['Created']
            created_time = datetime.fromisoformat(created.replace('Z', '+00:00'))
            uptime = (datetime.now() - created_time.replace(tzinfo=None)).total_seconds()
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "network_io": network_io,
                "disk_io": disk_io,
                "uptime": uptime
            }
            
        except Exception as e:
            logger.error(f"Error getting container stats for {service_id}: {e}")
            return None
            
    def _buffer_metrics(self, source: str, metrics: Any):
        """Buffer metrics for batch processing"""
        timestamp = datetime.utcnow()
        self._metrics_buffer.append({
            "source": source,
            "metrics": metrics,
            "timestamp": timestamp
        })
        
    def get_buffered_metrics(self) -> List[Dict[str, Any]]:
        """Get and clear buffered metrics"""
        metrics = list(self._metrics_buffer)
        self._metrics_buffer.clear()
        return metrics


class AnalyticsCollector:
    """Main analytics data collector"""
    
    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.metrics_collector = MetricsCollector(config)
        self.event_handlers: List[Callable] = []
        self._events_buffer = deque(maxlen=50000)
        self._api_metrics = defaultdict(lambda: defaultdict(int))
        
    async def start(self):
        """Start analytics collection"""
        await self.metrics_collector.start()
        logger.info("Analytics collection started")
        
    async def stop(self):
        """Stop analytics collection"""
        await self.metrics_collector.stop()
        logger.info("Analytics collection stopped")
        
    def track_event(self, event: AnalyticsEvent):
        """Track an analytics event"""
        self._events_buffer.append(event)
        
        # Notify event handlers
        for handler in self.event_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
                
    def track_api_call(self, endpoint: str, method: str, status_code: int, 
                      response_time: float, user_id: Optional[str] = None):
        """Track API call metrics"""
        self._api_metrics[endpoint]["total_calls"] += 1
        self._api_metrics[endpoint]["total_response_time"] += response_time
        
        if status_code >= 400:
            self._api_metrics[endpoint]["error_count"] += 1
            
        # Create analytics event
        event = AnalyticsEvent(
            event_id=f"api_{int(time.time() * 1000000)}",
            event_type="api_call",
            source="api",
            data={
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "response_time": response_time
            },
            user_id=user_id
        )
        self.track_event(event)
        
    def track_user_activity(self, user_id: str, action: str, details: Dict[str, Any]):
        """Track user activity"""
        event = AnalyticsEvent(
            event_id=f"user_{int(time.time() * 1000000)}",
            event_type="user_activity",
            source="user",
            data={
                "action": action,
                **details
            },
            user_id=user_id
        )
        self.track_event(event)
        
    def track_service_event(self, service_id: str, event_type: str, details: Dict[str, Any]):
        """Track service-related events"""
        event = AnalyticsEvent(
            event_id=f"service_{int(time.time() * 1000000)}",
            event_type=event_type,
            source="service",
            data={
                "service_id": service_id,
                **details
            }
        )
        self.track_event(event)
        
    def add_event_handler(self, handler: Callable[[AnalyticsEvent], None]):
        """Add event handler"""
        self.event_handlers.append(handler)
        
    def get_buffered_events(self) -> List[AnalyticsEvent]:
        """Get and clear buffered events"""
        events = list(self._events_buffer)
        self._events_buffer.clear()
        return events
        
    def get_api_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get API metrics summary"""
        summary = {}
        for endpoint, metrics in self._api_metrics.items():
            total_calls = metrics["total_calls"]
            if total_calls > 0:
                avg_response_time = metrics["total_response_time"] / total_calls
                error_rate = (metrics["error_count"] / total_calls) * 100
            else:
                avg_response_time = 0
                error_rate = 0
                
            summary[endpoint] = {
                "total_calls": total_calls,
                "avg_response_time": avg_response_time,
                "error_count": metrics["error_count"],
                "error_rate": error_rate
            }
            
        return summary


# Global collector instance
_analytics_collector: Optional[AnalyticsCollector] = None


def get_analytics_collector() -> Optional[AnalyticsCollector]:
    """Get global analytics collector instance"""
    return _analytics_collector


def init_analytics_collector(config: AnalyticsConfig) -> AnalyticsCollector:
    """Initialize global analytics collector"""
    global _analytics_collector
    _analytics_collector = AnalyticsCollector(config)
    return _analytics_collector