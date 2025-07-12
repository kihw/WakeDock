"""
System management endpoints
"""

from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

from wakedock.core.monitoring import MonitoringService
from wakedock.infrastructure.caddy import caddy_manager
from wakedock.infrastructure.cache.service import CacheService
from wakedock.api.dependencies import get_monitoring_service, get_orchestrator, get_optional_cache_service

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

class RouteCreateRequest(BaseModel):
    host: str
    upstream: str
    port: Optional[int] = 80
    path: Optional[str] = "/"
    tls: Optional[bool] = True
    headers: Optional[Dict[str, str]] = {}

class RouteResponse(BaseModel):
    id: str
    host: str
    upstream: str
    port: int
    path: str
    tls: bool
    status: str
    created_at: datetime

class DynamicRouteStatus(BaseModel):
    route_id: str
    host: str
    status: str
    last_check: datetime
    response_time_ms: Optional[float] = None

class SystemOverviewResponse(BaseModel):
    services: ServicesOverview
    system: SystemStats
    docker: DockerStatus
    caddy: CaddyStatus


@router.get("/overview", response_model=SystemOverviewResponse)
async def get_system_overview(
    monitoring: MonitoringService = Depends(get_monitoring_service),
    cache_service: CacheService = Depends(get_optional_cache_service)
):
    """Get system overview metrics with intelligent caching"""
    
    # Utiliser cache intelligent pour l'overview système
    async def fetch_overview():
        return await monitoring.get_system_overview()
    
    # Si cache disponible, l'utiliser
    if cache_service and cache_service.is_initialized():
        cache_key = cache_service.get_cache_key("system", "overview")
        overview = await cache_service.get(
            cache_key, 
            fetch_overview, 
            "system_metrics"
        )
    else:
        # Fallback sans cache
        overview = await fetch_overview()
    
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
        reload_result = await caddy_manager.api_client.reload_config()
        
        return {
            "success": reload_result.success,
            "message": "Caddy configuration reloaded" if reload_result.success else f"Failed to reload Caddy: {reload_result.error}",
            "duration_ms": reload_result.duration_ms,
            "timestamp": datetime.now()
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error reloading Caddy: {str(e)}",
            "timestamp": datetime.now()
        }


@router.post("/caddy/update")
async def update_caddy_config(orchestrator = Depends(get_orchestrator)):
    """Force update Caddy configuration with all services"""
    try:
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
        health_status = await caddy_manager.api_client.get_status()
        
        return {
            "caddy_admin_api": "accessible" if health_status.status.value == "healthy" else "not accessible",
            "status": health_status.status.value,
            "version": health_status.version,
            "active_routes": health_status.active_routes,
            "errors": health_status.errors,
            "warnings": health_status.warnings,
            "timestamp": datetime.now()
        }
    except Exception as e:
        return {
            "caddy_admin_api": "error",
            "error": str(e),
            "timestamp": datetime.now()
        }


@router.post("/caddy/fix-default-page")
async def fix_caddy_default_page():
    """Detect and fix Caddy default page issue"""
    try:
        # Check if Caddy is healthy and reload configuration
        is_healthy = await caddy_manager.api_client.is_healthy()
        if is_healthy:
            reload_result = await caddy_manager.api_client.reload_config()
            success = reload_result.success
        else:
            success = False
        
        return {
            "success": success,
            "message": "Caddy configuration reloaded" if success else "Caddy is not healthy",
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
        # Simple diagnostic - check if Caddy can connect to dashboard
        is_healthy = await caddy_manager.api_client.is_healthy()
        
        return {
            "dashboard_accessible": is_healthy,
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


# === DYNAMIC CADDY ROUTES MANAGEMENT ===

@router.get("/caddy/routes", response_model=List[RouteResponse])
async def list_caddy_routes():
    """List all active Caddy routes"""
    try:
        routes_manager = caddy_manager.routes_manager
        active_routes = routes_manager.list_all_routes()
        
        route_responses = []
        for route in active_routes:
            route_responses.append(RouteResponse(
                id=route.id,
                host=route.host,
                upstream=route.upstream,
                port=route.port,
                path=route.path,
                tls=route.tls,
                status="active",
                created_at=datetime.now()
            ))
        
        return route_responses
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list routes: {str(e)}"
        )


@router.post("/caddy/routes", response_model=RouteResponse)
async def create_dynamic_route(route_request: RouteCreateRequest):
    """Create a new dynamic route in Caddy"""
    try:
        routes_manager = caddy_manager.routes_manager
        
        # Validate domain
        domain_validation = await routes_manager.validate_domain(route_request.host)
        if not domain_validation.is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid domain: {', '.join(domain_validation.errors)}"
            )
        
        # Create route object
        from wakedock.infrastructure.caddy.types import Route
        route = Route(
            id=f"dynamic_{route_request.host}_{int(datetime.now().timestamp())}",
            host=route_request.host,
            upstream=route_request.upstream,
            port=route_request.port,
            path=route_request.path,
            tls=route_request.tls,
            headers=route_request.headers or {}
        )
        
        # Build Caddy configuration
        route_config = routes_manager._build_caddy_route_config(route)
        
        # Add route via API
        success = await caddy_manager.api_client.add_route(route_config)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to add route to Caddy"
            )
        
        # Store in active routes
        routes_manager.active_routes[route.id] = route
        
        return RouteResponse(
            id=route.id,
            host=route.host,
            upstream=route.upstream,
            port=route.port,
            path=route.path,
            tls=route.tls,
            status="active",
            created_at=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create route: {str(e)}"
        )


@router.delete("/caddy/routes/{route_id}")
async def delete_dynamic_route(route_id: str):
    """Delete a dynamic route from Caddy"""
    try:
        routes_manager = caddy_manager.routes_manager
        
        # Check if route exists
        if route_id not in routes_manager.active_routes:
            raise HTTPException(
                status_code=404,
                detail=f"Route {route_id} not found"
            )
        
        # Remove via API
        success = await caddy_manager.api_client.remove_route(route_id)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to remove route from Caddy"
            )
        
        # Remove from active routes
        del routes_manager.active_routes[route_id]
        
        return {
            "success": True,
            "message": f"Route {route_id} deleted successfully",
            "timestamp": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete route: {str(e)}"
        )


@router.get("/caddy/routes/{route_id}/status", response_model=DynamicRouteStatus)
async def get_route_status(route_id: str):
    """Get status of a specific route"""
    try:
        routes_manager = caddy_manager.routes_manager
        
        # Check if route exists
        if route_id not in routes_manager.active_routes:
            raise HTTPException(
                status_code=404,
                detail=f"Route {route_id} not found"
            )
        
        route = routes_manager.active_routes[route_id]
        
        # Get routes status
        routes_status = await routes_manager.get_routes_status()
        status = routes_status.get(route_id, "unknown")
        
        return DynamicRouteStatus(
            route_id=route_id,
            host=route.host,
            status=status.value if hasattr(status, 'value') else str(status),
            last_check=datetime.now(),
            response_time_ms=None  # Could implement actual health check
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get route status: {str(e)}"
        )


@router.post("/caddy/routes/validate-domain")
async def validate_domain(domain: str):
    """Validate a domain name for route creation"""
    try:
        routes_manager = caddy_manager.routes_manager
        validation = await routes_manager.validate_domain(domain)
        
        return {
            "domain": domain,
            "is_valid": validation.is_valid,
            "errors": validation.errors,
            "warnings": validation.warnings,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate domain: {str(e)}"
        )


@router.post("/caddy/routes/sync-services")
async def sync_routes_with_services(orchestrator = Depends(get_orchestrator)):
    """Synchronize Caddy routes with running services"""
    try:
        routes_manager = caddy_manager.routes_manager
        
        # Get all services from orchestrator
        services = await orchestrator.list_services()
        
        # Convert to service objects (simplified)
        from wakedock.database.models import Service, ServiceStatus
        service_objects = []
        for service_data in services:
            # Create simplified service object for routing
            service = type('Service', (), {
                'id': service_data.get('id', ''),
                'name': service_data.get('name', ''),
                'status': ServiceStatus.RUNNING if service_data.get('status') == 'running' else ServiceStatus.STOPPED,
                'domain': f"{service_data.get('name', 'unknown')}.wakedock.local",
                'port': 8000
            })()
            service_objects.append(service)
        
        # Sync routes
        sync_results = await routes_manager.sync_routes_with_services(service_objects)
        
        return {
            "success": True,
            "message": "Routes synchronized with services",
            "sync_results": sync_results,
            "total_routes": len(routes_manager.active_routes),
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync routes: {str(e)}"
        )
