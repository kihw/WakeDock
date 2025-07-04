"""
FastAPI application factory
"""

from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging
import asyncio

from wakedock.api.routes import services, health, proxy, system, security, websocket
from wakedock.api.auth.routes import router as auth_router
from wakedock.api.middleware import ProxyMiddleware
from wakedock.core.orchestrator import DockerOrchestrator
from wakedock.core.monitoring import MonitoringService
from wakedock.config import get_settings

logger = logging.getLogger(__name__)


def create_app(orchestrator: Optional[DockerOrchestrator] = None, monitoring: Optional[MonitoringService] = None) -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title="WakeDock API",
        description="Intelligent Docker orchestration with Caddy reverse proxy",
        version="1.0.0",
        docs_url="/api/docs" if settings.wakedock.debug else None,
        redoc_url="/api/redoc" if settings.wakedock.debug else None,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add proxy middleware
    app.add_middleware(ProxyMiddleware, orchestrator=orchestrator)
    
    # Include routers
    app.include_router(
        health.router,
        prefix="/api/v1",
        tags=["health"]
    )
    
    app.include_router(
        services.router,
        prefix="/api/v1/services",
        tags=["services"]
    )
    
    app.include_router(
        system.router,
        prefix="/api/v1/system",
        tags=["system"]
    )
    
    app.include_router(
        security.router,
        prefix="/api/v1",
        tags=["security"]
    )
    
    # Duplicate routes for internal container communication (without /api prefix)
    app.include_router(
        health.router,
        prefix="/v1",
        tags=["health-internal"]
    )
    
    app.include_router(
        services.router,
        prefix="/v1/services",
        tags=["services-internal"]
    )
    
    app.include_router(
        system.router,
        prefix="/v1/system",
        tags=["system-internal"]
    )
    
    app.include_router(
        auth_router,
        prefix="/api/v1",
        tags=["authentication"]
    )
    
    # WebSocket router
    app.include_router(
        websocket.router,
        prefix="/api/v1",
        tags=["websocket"]
    )
    
    app.include_router(
        proxy.router,
        prefix="",
        tags=["proxy"]
    )
    
    # Store dependencies in app state
    app.state.orchestrator = orchestrator
    app.state.monitoring_service = monitoring
    app.state.settings = settings
    
    @app.on_event("startup")
    async def startup_event():
        logger.info("WakeDock API started")
        # Start WebSocket ping task
        asyncio.create_task(websocket.websocket_ping_task())
        logger.info("WebSocket ping task started")
        
        # Connect Docker events handler to WebSocket if available
        if hasattr(app.state, 'docker_events_handler') and app.state.docker_events_handler:
            from wakedock.api.routes.websocket import handle_docker_event
            app.state.docker_events_handler.subscribe(handle_docker_event)
            logger.info("Docker events handler connected to WebSocket")
        
        # Connect system metrics handler to WebSocket if available
        if hasattr(app.state, 'system_metrics_handler') and app.state.system_metrics_handler:
            from wakedock.api.routes.websocket import broadcast_system_update
            app.state.system_metrics_handler.subscribe(broadcast_system_update)
            logger.info("System metrics handler connected to WebSocket")
        
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("WakeDock API shutting down")
        # WebSocket connections will be closed automatically
    
    return app
