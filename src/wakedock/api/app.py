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

from wakedock.api.routes import services, health, proxy, system, security, cache, vault, analytics, audit, config
from wakedock.api.websocket import websocket_ping_task, websocket_router
from wakedock.api.auth.routes import router as auth_router
from wakedock.api.middleware import ProxyMiddleware
from wakedock.core.orchestrator import DockerOrchestrator
from wakedock.core.monitoring import MonitoringService
from wakedock.infrastructure.cache.service import get_cache_service
from wakedock.infrastructure.vault.service import get_vault_service
from wakedock.security.middleware import SecurityAuditMiddleware, RequestTimingMiddleware
from wakedock.performance.api.middleware import (
    PerformanceMiddleware,
    CacheMiddleware,
    ResponseOptimizationMiddleware,
    ConnectionPoolMiddleware
)
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
    
    # CORS middleware (must be first for proper functioning)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:3001", 
            "http://195.201.199.226:3000",
            "http://195.201.199.226:3001",
            "http://195.201.199.226",  # IP publique pour les requêtes browser
            "http://wakedock-dashboard:3000",
            "http://wakedock-dashboard:3001",
            # Production domains
            "https://admin.mtool.ovh",
            "https://api.mtool.ovh",
            "https://mtool.ovh"
        ],
        allow_credentials=False,  # Match frontend credentials: 'omit'
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"]  # Expose all headers for debugging
    )
    
    # Security middleware
    # Temporarily disabled due to AuditService.log_event issue
    # app.add_middleware(SecurityAuditMiddleware, log_requests=True, log_responses=True)
    app.add_middleware(RequestTimingMiddleware, slow_request_threshold=2.0)
    
    # Performance middleware
    app.add_middleware(PerformanceMiddleware)
    app.add_middleware(CacheMiddleware)
    app.add_middleware(ResponseOptimizationMiddleware)
    app.add_middleware(ConnectionPoolMiddleware)
    
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
    
    app.include_router(
        cache.router,
        prefix="/api/v1/cache",
        tags=["cache"]
    )
    
    app.include_router(
        vault.router,
        prefix="/api/v1/vault",
        tags=["vault"]
    )
    
    app.include_router(
        analytics.router,
        prefix="/api/v1/analytics",
        tags=["analytics"]
    )
    
    app.include_router(
        audit.router,
        prefix="/api/v1/audit",
        tags=["audit"]
    )
    
    app.include_router(
        config.router,
        prefix="/api",
        tags=["config"]
    )
    
    # WebSocket router - no prefix to match client expectations
    app.include_router(
        websocket_router,
        prefix="",
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
    app.state.cache_service = get_cache_service()
    app.state.vault_service = get_vault_service()
    
    @app.on_event("startup")
    async def startup_event():
        logger.info("WakeDock API started")
        
        # Cache initialization temporarily disabled to prevent recursion
        # if hasattr(app.state, 'cache_service') and app.state.cache_service:
        #     if not app.state.cache_service.is_initialized():
        #         try:
        #             await app.state.cache_service.initialize()
        #             logger.info("Cache service initialized in app startup")
        #         except Exception as e:
        #             logger.warning(f"Cache service initialization failed in app startup: {e}")
        logger.info("Cache service initialization in app startup disabled")
        
        # Initialize Vault service if enabled
        if hasattr(app.state, 'vault_service') and app.state.vault_service:
            if app.state.settings.vault.enabled and not app.state.vault_service.is_initialized():
                try:
                    await app.state.vault_service.initialize()
                    logger.info("Vault service initialized in app startup")
                except Exception as e:
                    logger.warning(f"Vault service initialization failed in app startup: {e}")
        
        # Start WebSocket ping task
        asyncio.create_task(websocket_ping_task())
        logger.info("WebSocket ping task started")
        
        # Connect Docker events handler to WebSocket if available
        if hasattr(app.state, 'docker_events_handler') and app.state.docker_events_handler:
            from wakedock.api.websocket import handle_docker_event
            app.state.docker_events_handler.subscribe(handle_docker_event)
            logger.info("Docker events handler connected to WebSocket")
        
        # Connect system metrics handler to WebSocket if available
        if hasattr(app.state, 'system_metrics_handler') and app.state.system_metrics_handler:
            from wakedock.api.websocket import broadcast_system_update
            app.state.system_metrics_handler.subscribe(broadcast_system_update)
            logger.info("System metrics handler connected to WebSocket")
        
        # Connect log streaming handler to WebSocket if available
        if hasattr(app.state, 'log_streaming_handler') and app.state.log_streaming_handler:
            from wakedock.api.websocket import broadcast_log_entry
            app.state.log_streaming_handler.subscribe(broadcast_log_entry)
            logger.info("Log streaming handler connected to WebSocket")
        
        # Connect notification manager to WebSocket if available
        if hasattr(app.state, 'notification_manager') and app.state.notification_manager:
            from wakedock.api.websocket import broadcast_notification
            app.state.notification_manager.subscribe(broadcast_notification)
            logger.info("Notification manager connected to WebSocket")
        
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("WakeDock API shutting down")
        
        # Shutdown Vault service if initialized
        if hasattr(app.state, 'vault_service') and app.state.vault_service:
            if app.state.vault_service.is_initialized():
                try:
                    await app.state.vault_service.shutdown()
                    logger.info("Vault service shutdown completed")
                except Exception as e:
                    logger.error(f"Vault service shutdown failed: {e}")
        
        # WebSocket connections will be closed automatically
    
    return app
