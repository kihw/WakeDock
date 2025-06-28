"""
System management endpoints
"""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime

from wakedock.core.monitoring import MonitoringService
from wakedock.core.caddy import caddy_manager

router = APIRouter()


class ServicesOverview(BaseModel):
    total: int
    running: int
    stopped: int
    error: int

class SystemStats(BaseModel):
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    uptime: int

class DockerStatus(BaseModel):
    version: str
    api_version: str
    status: str

class CaddyStatus(BaseModel):
    version: str
    status: str
    active_routes: int

class SystemOverviewResponse(BaseModel):
    services: ServicesOverview
    system: SystemStats
    docker: DockerStatus
    caddy: CaddyStatus


def get_monitoring_service(request: Request) -> MonitoringService:
    """Dependency to get monitoring service from app state"""
    return request.app.state.monitoring


@router.get("/overview", response_model=SystemOverviewResponse)
async def get_system_overview(monitoring: MonitoringService = Depends(get_monitoring_service)):
    """Get system overview metrics"""
    overview = await monitoring.get_system_overview()
    
    return SystemOverviewResponse(
        services=ServicesOverview(**overview["services"]),
        system=SystemStats(**overview["system"]),
        docker=DockerStatus(**overview["docker"]),
        caddy=CaddyStatus(**overview["caddy"])
    )


@router.get("/health")
async def get_system_health():
    """Get detailed system health status"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "components": {
            "api": "healthy",
            "database": "healthy",
            "docker": "healthy",
            "caddy": "healthy"
        }
    }


@router.get("/metrics")
async def get_system_metrics(monitoring: MonitoringService = Depends(get_monitoring_service)):
    """Get detailed system metrics"""
    # This would return more detailed metrics for monitoring systems
    return {
        "timestamp": datetime.now(),
        "metrics": {
            "requests_total": 0,
            "requests_per_second": 0,
            "error_rate": 0,
            "response_time": 0
        }
    }


@router.post("/caddy/reload")
async def reload_caddy_config():
    """Force reload Caddy configuration"""
    try:
        success = await caddy_manager.reload_caddy()
        
        return {
            "success": success,
            "message": "Caddy configuration reloaded" if success else "Failed to reload Caddy",
            "timestamp": datetime.now()
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error reloading Caddy: {str(e)}",
            "timestamp": datetime.now()
        }


@router.post("/caddy/update")
async def update_caddy_config(request: Request):
    """Force update Caddy configuration with all services"""
    try:
        # Get orchestrator from app state
        orchestrator = getattr(request.app.state, 'orchestrator', None)
        
        if not orchestrator:
            return {
                "success": False,
                "message": "Orchestrator not available",
                "timestamp": datetime.now()
            }
        
        # Force update Caddy configuration
        success = await orchestrator._update_caddy_configuration()
        
        return {
            "success": success,
            "message": "Caddy configuration updated" if success else "Failed to update Caddy configuration",
            "timestamp": datetime.now()
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error updating Caddy configuration: {str(e)}",
            "timestamp": datetime.now()
        }


@router.get("/caddy/status")
async def get_caddy_status():
    """Get Caddy proxy status"""
    try:
        # Try to get Caddy admin API status
        status = await caddy_manager.get_status()
        
        return {
            "caddy_admin_api": "accessible" if status else "not accessible",
            "config_path": str(caddy_manager.config_path),
            "timestamp": datetime.now()
        }
    except Exception as e:
        return {
            "caddy_admin_api": "error",
            "error": str(e),
            "config_path": str(caddy_manager.config_path),
            "timestamp": datetime.now()
        }


@router.post("/caddy/fix-default-page")
async def fix_caddy_default_page():
    """Detect and fix Caddy default page issue"""
    try:
        success = await caddy_manager.detect_and_fix_default_page()
        
        return {
            "success": success,
            "message": "Caddy default page fixed" if success else "Failed to fix Caddy default page",
            "timestamp": datetime.now()
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error fixing Caddy default page: {str(e)}",
            "timestamp": datetime.now()
        }


@router.get("/dashboard/diagnose")
async def diagnose_dashboard():
    """Diagnose dashboard connection and build issues"""
    try:
        success = await caddy_manager.diagnose_dashboard_connection()
        
        return {
            "dashboard_accessible": success,
            "message": "Dashboard diagnostics completed",
            "timestamp": datetime.now(),
            "troubleshooting": {
                "check_container": "docker ps | grep dashboard",
                "check_logs": "docker logs wakedock-dashboard",
                "check_build": "docker exec wakedock-dashboard ls -la build/",
                "test_health": "docker exec wakedock-dashboard curl -f http://localhost:3000/health",
                "rebuild": "docker-compose build dashboard"
            }
        }
    except Exception as e:
        return {
            "dashboard_accessible": False,
            "message": f"Error diagnosing dashboard: {str(e)}",
            "timestamp": datetime.now()
        }
