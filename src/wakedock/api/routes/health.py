"""
Health check endpoints
"""

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel
from typing import Dict, Any
import psutil
import time
from datetime import datetime

from wakedock.config import get_settings
from wakedock.monitoring.prometheus import get_prometheus_exporter, CONTENT_TYPE_LATEST

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    uptime: float
    system: Dict[str, Any]


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint - optimized for speed"""
    settings = get_settings()
    
    # Minimal system metrics for fast health check
    try:
        memory = psutil.virtual_memory()
        system_info = {
            "cpu_percent": 0,  # Skip CPU check for speed
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent
            },
            "disk": {
                "total": 0,  # Skip disk check for speed
                "free": 0,
                "percent": 0
            }
        }
    except Exception:
        # Fallback if psutil fails
        system_info = {
            "cpu_percent": 0,
            "memory": {"total": 0, "available": 0, "percent": 0},
            "disk": {"total": 0, "free": 0, "percent": 0}
        }
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version="1.0.0",
        uptime=time.time() - psutil.boot_time(),
        system=system_info
    )


@router.get("/metrics")
async def metrics(request: Request):
    """Prometheus metrics endpoint"""
    # Try to get metrics from the Prometheus exporter
    prometheus_exporter = getattr(request.app.state, 'prometheus_exporter', None)
    if prometheus_exporter:
        metrics_data = prometheus_exporter.get_metrics()
        if metrics_data:
            return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)
    
    # Fallback to basic metrics if Prometheus exporter is not available
    cpu_percent = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    metrics = [
        f"# HELP wakedock_cpu_percent CPU usage percentage",
        f"# TYPE wakedock_cpu_percent gauge",
        f"wakedock_cpu_percent {cpu_percent}",
        f"",
        f"# HELP wakedock_memory_usage_bytes Memory usage in bytes",
        f"# TYPE wakedock_memory_usage_bytes gauge", 
        f"wakedock_memory_usage_bytes {memory.used}",
        f"",
        f"# HELP wakedock_memory_total_bytes Total memory in bytes",
        f"# TYPE wakedock_memory_total_bytes gauge",
        f"wakedock_memory_total_bytes {memory.total}",
        f"",
        f"# HELP wakedock_disk_usage_bytes Disk usage in bytes",
        f"# TYPE wakedock_disk_usage_bytes gauge",
        f"wakedock_disk_usage_bytes {disk.used}",
        f"",
        f"# HELP wakedock_disk_total_bytes Total disk space in bytes",
        f"# TYPE wakedock_disk_total_bytes gauge",
        f"wakedock_disk_total_bytes {disk.total}",
    ]
    
    return Response(content="\n".join(metrics), media_type=CONTENT_TYPE_LATEST)
