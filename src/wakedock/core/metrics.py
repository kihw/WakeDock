"""
System metrics and health monitoring service.
Collects and provides system metrics for monitoring and alerting.
"""

import asyncio
import logging
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """System metrics data structure."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used: int
    memory_total: int
    disk_percent: float
    disk_used: int
    disk_total: int
    network_io: Dict[str, int]
    docker_stats: Dict[str, Any]
    uptime: float
    load_average: Optional[List[float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemMetrics':
        """Create from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class SystemMetricsCollector:
    """Collects system metrics and health information."""
    
    def __init__(self, collection_interval: int = 30):
        self.collection_interval = collection_interval
        self.metrics_history: List[SystemMetrics] = []
        self.max_history_size = 1000  # Keep last 1000 metrics
        self.docker_client = None
        self._boot_time = psutil.boot_time()
        self._init_docker_client()
    
    def _init_docker_client(self):
        """Initialize Docker client for container stats."""
        try:
            import docker
            self.docker_client = docker.from_env()
            self.docker_client.ping()
            logger.info("Docker client initialized for metrics collection")
        except Exception as e:
            logger.warning(f"Could not initialize Docker client for metrics: {e}")
            self.docker_client = None
    
    async def collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = memory.used
            memory_total = memory.total
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used = disk.used
            disk_total = disk.total
            
            # Network I/O
            network_io = self._get_network_io()
            
            # Docker stats
            docker_stats = await self._get_docker_stats()
            
            # System uptime
            uptime = time.time() - self._boot_time
            
            # Load average (Unix systems)
            load_average = None
            try:
                if hasattr(os, 'getloadavg'):
                    load_average = list(os.getloadavg())
            except (AttributeError, OSError):
                pass
            
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used=memory_used,
                memory_total=memory_total,
                disk_percent=disk_percent,
                disk_used=disk_used,
                disk_total=disk_total,
                network_io=network_io,
                docker_stats=docker_stats,
                uptime=uptime,
                load_average=load_average
            )
            
            # Add to history
            self.metrics_history.append(metrics)
            
            # Trim history if too large
            if len(self.metrics_history) > self.max_history_size:
                self.metrics_history = self.metrics_history[-self.max_history_size:]
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            raise
    
    def _get_network_io(self) -> Dict[str, int]:
        """Get network I/O statistics."""
        try:
            net_io = psutil.net_io_counters()
            return {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }
        except Exception as e:
            logger.warning(f"Could not get network I/O stats: {e}")
            return {
                'bytes_sent': 0,
                'bytes_recv': 0,
                'packets_sent': 0,
                'packets_recv': 0
            }
    
    async def _get_docker_stats(self) -> Dict[str, Any]:
        """Get Docker container statistics."""
        if not self.docker_client:
            return {
                'containers_running': 0,
                'containers_total': 0,
                'images_count': 0,
                'containers': []
            }
        
        try:
            # Get container counts
            containers = self.docker_client.containers.list(all=True)
            running_containers = [c for c in containers if c.status == 'running']
            
            # Get image count
            images = self.docker_client.images.list()
            
            # Get detailed stats for running containers
            container_stats = []
            for container in running_containers[:10]:  # Limit to 10 containers for performance
                try:
                    stats = container.stats(stream=False)
                    
                    # Calculate CPU percentage
                    cpu_percent = 0
                    if 'cpu_stats' in stats and 'precpu_stats' in stats:
                        cpu_stats = stats['cpu_stats']
                        precpu_stats = stats['precpu_stats']
                        
                        cpu_usage = cpu_stats['cpu_usage']['total_usage']
                        precpu_usage = precpu_stats['cpu_usage']['total_usage']
                        
                        system_usage = cpu_stats['system_cpu_usage']
                        presystem_usage = precpu_stats['system_cpu_usage']
                        
                        if system_usage > presystem_usage:
                            cpu_delta = cpu_usage - precpu_usage
                            system_delta = system_usage - presystem_usage
                            cpu_percent = (cpu_delta / system_delta) * len(cpu_stats['cpu_usage']['percpu_usage']) * 100
                    
                    # Calculate memory usage
                    memory_usage = 0
                    memory_limit = 0
                    if 'memory_stats' in stats:
                        memory_stats = stats['memory_stats']
                        memory_usage = memory_stats.get('usage', 0)
                        memory_limit = memory_stats.get('limit', 0)
                    
                    container_stats.append({
                        'id': container.short_id,
                        'name': container.name,
                        'image': container.image.tags[0] if container.image.tags else 'unknown',
                        'status': container.status,
                        'cpu_percent': round(cpu_percent, 2),
                        'memory_usage': memory_usage,
                        'memory_limit': memory_limit,
                        'memory_percent': round((memory_usage / memory_limit) * 100, 2) if memory_limit > 0 else 0
                    })
                    
                except Exception as e:
                    logger.warning(f"Could not get stats for container {container.name}: {e}")
                    continue
            
            return {
                'containers_running': len(running_containers),
                'containers_total': len(containers),
                'images_count': len(images),
                'containers': container_stats
            }
            
        except Exception as e:
            logger.warning(f"Could not get Docker stats: {e}")
            return {
                'containers_running': 0,
                'containers_total': 0,
                'images_count': 0,
                'containers': []
            }
    
    def get_latest_metrics(self) -> Optional[SystemMetrics]:
        """Get the latest collected metrics."""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_metrics_history(self, hours: int = 24) -> List[SystemMetrics]:
        """Get metrics history for the specified number of hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]
    
    def get_average_metrics(self, hours: int = 1) -> Optional[Dict[str, float]]:
        """Get average metrics for the specified time period."""
        metrics = self.get_metrics_history(hours)
        if not metrics:
            return None
        
        return {
            'cpu_percent': sum(m.cpu_percent for m in metrics) / len(metrics),
            'memory_percent': sum(m.memory_percent for m in metrics) / len(metrics),
            'disk_percent': sum(m.disk_percent for m in metrics) / len(metrics),
            'containers_running': sum(m.docker_stats.get('containers_running', 0) for m in metrics) / len(metrics)
        }
    
    async def start_collection(self):
        """Start the metrics collection loop."""
        logger.info(f"Starting system metrics collection (interval: {self.collection_interval}s)")
        
        while True:
            try:
                await self.collect_metrics()
                logger.debug("System metrics collected successfully")
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
            
            await asyncio.sleep(self.collection_interval)
    
    def export_metrics(self, filepath: str, hours: int = 24):
        """Export metrics to a JSON file."""
        metrics = self.get_metrics_history(hours)
        data = {
            'export_time': datetime.now().isoformat(),
            'hours': hours,
            'metrics_count': len(metrics),
            'metrics': [m.to_dict() for m in metrics]
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Exported {len(metrics)} metrics to {filepath}")
    
    def check_health_thresholds(self) -> Dict[str, Any]:
        """Check if system metrics exceed health thresholds."""
        latest = self.get_latest_metrics()
        if not latest:
            return {'status': 'unknown', 'alerts': []}
        
        alerts = []
        status = 'healthy'
        
        # CPU threshold
        if latest.cpu_percent > 90:
            alerts.append({
                'type': 'critical',
                'metric': 'cpu',
                'value': latest.cpu_percent,
                'threshold': 90,
                'message': f'CPU usage critically high: {latest.cpu_percent:.1f}%'
            })
            status = 'critical'
        elif latest.cpu_percent > 75:
            alerts.append({
                'type': 'warning',
                'metric': 'cpu',
                'value': latest.cpu_percent,
                'threshold': 75,
                'message': f'CPU usage high: {latest.cpu_percent:.1f}%'
            })
            if status == 'healthy':
                status = 'warning'
        
        # Memory threshold
        if latest.memory_percent > 95:
            alerts.append({
                'type': 'critical',
                'metric': 'memory',
                'value': latest.memory_percent,
                'threshold': 95,
                'message': f'Memory usage critically high: {latest.memory_percent:.1f}%'
            })
            status = 'critical'
        elif latest.memory_percent > 80:
            alerts.append({
                'type': 'warning',
                'metric': 'memory',
                'value': latest.memory_percent,
                'threshold': 80,
                'message': f'Memory usage high: {latest.memory_percent:.1f}%'
            })
            if status == 'healthy':
                status = 'warning'
        
        # Disk threshold
        if latest.disk_percent > 95:
            alerts.append({
                'type': 'critical',
                'metric': 'disk',
                'value': latest.disk_percent,
                'threshold': 95,
                'message': f'Disk usage critically high: {latest.disk_percent:.1f}%'
            })
            status = 'critical'
        elif latest.disk_percent > 85:
            alerts.append({
                'type': 'warning',
                'metric': 'disk',
                'value': latest.disk_percent,
                'threshold': 85,
                'message': f'Disk usage high: {latest.disk_percent:.1f}%'
            })
            if status == 'healthy':
                status = 'warning'
        
        return {
            'status': status,
            'alerts': alerts,
            'timestamp': latest.timestamp.isoformat()
        }


# Global metrics collector instance
metrics_collector = SystemMetricsCollector()


async def start_metrics_collection():
    """Start the global metrics collection."""
    await metrics_collector.start_collection()


def get_system_metrics() -> Optional[SystemMetrics]:
    """Get the latest system metrics."""
    return metrics_collector.get_latest_metrics()


def get_system_health() -> Dict[str, Any]:
    """Get system health status."""
    return metrics_collector.check_health_thresholds()
