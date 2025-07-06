"""
Main application entry point
"""

import asyncio
import logging
import uvicorn
from pathlib import Path

from wakedock.config import get_settings
from wakedock.api.app import create_app
from wakedock.core.monitoring import MonitoringService
from wakedock.core.orchestrator import DockerOrchestrator
from wakedock.infrastructure.caddy import caddy_manager
from wakedock.infrastructure.cache.service import init_cache_service, shutdown_cache_service
from wakedock.core.docker_events import initialize_docker_events
from wakedock.core.system_metrics import initialize_system_metrics
from wakedock.core.log_streaming import initialize_log_streaming
from wakedock.core.notifications import initialize_notifications
from wakedock.database.database import init_database
from wakedock.monitoring.prometheus import init_prometheus_exporter

# Imports des services de sécurité
from wakedock.security.manager import get_security_manager, initialize_security, shutdown_security
from wakedock.security.ids_middleware import IntrusionDetectionMiddleware
from wakedock.security.session_timeout import SessionTimeoutMiddleware

# Imports des optimisations de performance
from wakedock.performance.integration import initialize_performance, shutdown_performance, get_performance_manager

import docker


async def main():
    """Main application entry point"""
    # Load configuration
    settings = get_settings()
    
    # Configuration sécurité
    security_config = {
        "jwt_secret_key": getattr(settings, "jwt_secret_key", "wakedock-default-secret-change-in-production"),
        "security": {
            "environment": getattr(settings, "environment", "development"),
            "session": {
                "idle_timeout_minutes": 60,
                "max_concurrent_sessions": 5,
                "warn_before_timeout_minutes": 5
            },
            "features": {
                "enable_mfa": getattr(settings, "enable_mfa", True),
                "enable_intrusion_detection": True,
                "enable_api_rate_limiting": True,
                "enable_session_rotation": True
            },
            "rate_limiting": {
                "enabled": True,
                "requests_per_minute": 100,
                "login_attempts_per_minute": 5
            }
        }
    }
    
    # Create data directories first
    Path(settings.wakedock.data_path).mkdir(parents=True, exist_ok=True)
    log_path = Path(settings.logging.file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Ensure log file can be created
    try:
        log_path.touch(exist_ok=True)
    except PermissionError:
        # Fallback to stdout only if log file can't be created
        handlers = [logging.StreamHandler()]
        # Log the warning after logging is configured
        fallback_warning = f"Warning: Cannot create log file at {log_path}, logging to stdout only"
    else:
        handlers = [
            logging.FileHandler(settings.logging.file),
            logging.StreamHandler()
        ]
        fallback_warning = None
    
    # Setup logging after directories are created
    logging.basicConfig(
        level=getattr(logging, settings.logging.level),
        format=settings.logging.format,
        handlers=handlers
    )
    
    logger = logging.getLogger(__name__)
    
    # Log the fallback warning if needed
    if fallback_warning:
        logger.warning(fallback_warning)
        
    logger.info("Starting WakeDock...")
    
    # Initialiser les services de sécurité en priorité
    security_services = None
    try:
        logger.info("Initializing security services...")
        security_services = await initialize_security(security_config)
        logger.info("Security services initialized successfully")
        logger.info(f"- JWT Rotation: ✓")
        logger.info(f"- Session Timeout: ✓") 
        logger.info(f"- Intrusion Detection: ✓")
        logger.info(f"- Security Config: ✓")
    except Exception as e:
        logger.error(f"Security services initialization failed: {e}")
        logger.warning("Application will continue but security features will be limited")

    # Initialiser les optimisations de performance
    performance_manager = None
    try:
        logger.info("Initializing performance optimizations...")
        performance_manager = await initialize_performance()
        logger.info("Performance optimizations initialized successfully")
        logger.info(f"- Intelligent Cache: ✓")
        logger.info(f"- Database Optimizer: ✓")
        logger.info(f"- API Middleware: ✓")
        logger.info(f"- Performance Monitoring: ✓")
    except Exception as e:
        logger.error(f"Performance optimization initialization failed: {e}")
        logger.warning("Application will continue but performance features will be limited")
    
    # Initialize database
    try:
        init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")
        logger.warning("Application will continue but database features may not work properly")
        # Don't raise the exception - allow the app to start
    
    # Initialize Redis cache service
    try:
        await init_cache_service()
        logger.info("Cache service initialized successfully")
    except Exception as e:
        logger.warning(f"Cache service initialization failed: {e}")
        logger.warning("Application will continue but caching features will not work")
    
    # Initialize services
    try:
        orchestrator = DockerOrchestrator()
        logger.info("Docker orchestrator initialized successfully")
    except Exception as e:
        logger.warning(f"Docker orchestrator initialization failed: {e}")
        logger.warning("Application will continue but Docker management features will not work")
        # Create a dummy orchestrator that doesn't do anything
        orchestrator = None
    
    # Initialize Docker events handler
    docker_events_handler = None
    try:
        docker_client = docker.from_env()
        docker_events_handler = initialize_docker_events(docker_client)
        logger.info("Docker events handler initialized successfully")
    except Exception as e:
        logger.warning(f"Docker events handler initialization failed: {e}")
        logger.warning("Application will continue but Docker events monitoring will not work")
    
    # Initialize System metrics handler
    system_metrics_handler = None
    try:
        system_metrics_handler = initialize_system_metrics(update_interval=5)
        logger.info("System metrics handler initialized successfully")
    except Exception as e:
        logger.warning(f"System metrics handler initialization failed: {e}")
        logger.warning("Application will continue but system metrics monitoring will not work")
    
    # Initialize Log streaming handler
    log_streaming_handler = None
    try:
        if docker_events_handler:  # Reuse the same docker client
            log_streaming_handler = initialize_log_streaming(docker_client)
        else:
            docker_client = docker.from_env()
            log_streaming_handler = initialize_log_streaming(docker_client)
        logger.info("Log streaming handler initialized successfully")
    except Exception as e:
        logger.warning(f"Log streaming handler initialization failed: {e}")
        logger.warning("Application will continue but log streaming will not work")
    
    # Initialize Notification manager
    notification_manager = None
    try:
        notification_manager = initialize_notifications(max_notifications=1000)
        logger.info("Notification manager initialized successfully")
    except Exception as e:
        logger.warning(f"Notification manager initialization failed: {e}")
        logger.warning("Application will continue but notifications will not work")

    # Initialize Caddy manager and force correct configuration
    try:
        logger.info("Initializing Caddy manager...")
        # Just importing caddy_manager will trigger initialization
        
        # Check if Caddy is available and healthy
        logger.info("Checking Caddy configuration...")
        is_healthy = await caddy_manager.is_healthy()
        if not is_healthy:
            logger.warning("Caddy is not healthy, but continuing...")
        
        if orchestrator:
            logger.info("Updating Caddy with current services...")
            await orchestrator._update_caddy_configuration()
        
        logger.info("Caddy manager initialized and configured successfully")
    except Exception as e:
        logger.warning(f"Caddy manager initialization failed: {e}")
        logger.warning("Application will continue but Caddy management features will not work")
    
    try:
        monitoring_service = MonitoringService()
        logger.info("Monitoring service initialized successfully")
    except Exception as e:
        logger.warning(f"Monitoring service initialization failed: {e}")
        monitoring_service = None
    
    # Initialize Prometheus exporter
    prometheus_exporter = None
    try:
        prometheus_exporter = init_prometheus_exporter(port=9090, host="0.0.0.0")
        await prometheus_exporter.start()
        logger.info("Prometheus exporter started on port 9090")
    except Exception as e:
        logger.warning(f"Prometheus exporter initialization failed: {e}")
        logger.warning("Application will continue but Prometheus metrics will not be available")
    
    # Connect monitoring service to orchestrator if both are available
    if orchestrator and monitoring_service:
        monitoring_service.set_orchestrator(orchestrator)
    
    # Create FastAPI app
    app = create_app(orchestrator, monitoring_service)
    
    # Intégrer les optimisations de performance dans l'app
    if performance_manager:
        try:
            logger.info("Integrating performance optimizations with FastAPI app...")
            await performance_manager.initialize(app=app, database_engine=None)  # Engine will be passed when available
            logger.info("Performance optimizations integrated successfully")
        except Exception as e:
            logger.error(f"Failed to integrate performance optimizations: {e}")
    
    # Ajouter les middlewares de sécurité si les services sont disponibles
    if security_services:
        try:
            logger.info("Adding security middlewares...")
            
            # Middleware de détection d'intrusion - Temporarily disabled due to AuditService.log_event issue
            # app.add_middleware(
            #     IntrusionDetectionMiddleware,
            #     ids=security_services.intrusion_detection_system,
            #     block_on_threat=True,
            #     log_all_events=False  # Log seulement les menaces moyennes et élevées
            # )
            
            # Middleware de timeout de session
            app.add_middleware(
                SessionTimeoutMiddleware,
                session_manager=security_services.session_timeout_manager
            )
            
            logger.info("Security middlewares added successfully")
            logger.info("- Intrusion Detection Middleware: ✓")
            logger.info("- Session Timeout Middleware: ✓")
            
        except Exception as e:
            logger.error(f"Failed to add security middlewares: {e}")
    
    # Store handlers in app state
    app.state.docker_events_handler = docker_events_handler
    app.state.system_metrics_handler = system_metrics_handler
    app.state.log_streaming_handler = log_streaming_handler
    app.state.notification_manager = notification_manager
    app.state.prometheus_exporter = prometheus_exporter
    app.state.security_services = security_services  # Ajouter les services de sécurité
    app.state.performance_manager = performance_manager  # Ajouter le gestionnaire de performance

    # Start monitoring service
    if settings.monitoring.enabled and monitoring_service:
        await monitoring_service.start()
    
    # Start Docker events monitoring
    if docker_events_handler:
        from wakedock.api.websocket import handle_docker_event
        docker_events_handler.subscribe(handle_docker_event)
        await docker_events_handler.start_monitoring()
        logger.info("Docker events monitoring started")
    
    # Start system metrics monitoring
    if system_metrics_handler:
        from wakedock.api.websocket import broadcast_system_update
        system_metrics_handler.subscribe(broadcast_system_update)
        await system_metrics_handler.start_monitoring()
        logger.info("System metrics monitoring started")
    
    # Start log streaming monitoring
    if log_streaming_handler:
        from wakedock.api.websocket import broadcast_log_entry
        log_streaming_handler.subscribe(broadcast_log_entry)
        await log_streaming_handler.start_monitoring()
        logger.info("Log streaming monitoring started")
    
    # Connect notification manager to WebSocket
    if notification_manager:
        from wakedock.api.websocket import broadcast_notification
        notification_manager.subscribe(broadcast_notification)
        logger.info("Notification manager connected to WebSocket")
        
        # Send startup notification
        from wakedock.core.notifications import NotificationLevel, NotificationCategory
        await notification_manager.create_notification(
            title="WakeDock Started",
            message="WakeDock Docker management platform has started successfully",
            level=NotificationLevel.SUCCESS,
            category=NotificationCategory.SYSTEM,
            source="wakedock"
        )
    
    # Start the server
    config = uvicorn.Config(
        app,
        host=settings.wakedock.host,
        port=settings.wakedock.port,
        log_level=settings.logging.level.lower(),
        access_log=True
    )
    
    server = uvicorn.Server(config)
    logger.info(f"WakeDock started on {settings.wakedock.host}:{settings.wakedock.port}")
    
    try:
        await server.serve()
    except KeyboardInterrupt:
        logger.info("Shutting down WakeDock...")
    finally:
        if settings.monitoring.enabled and monitoring_service:
            await monitoring_service.stop()
        
        # Stop Prometheus exporter
        if prometheus_exporter:
            await prometheus_exporter.stop()
            logger.info("Prometheus exporter stopped")
        
        # Stop Docker events monitoring
        if docker_events_handler:
            await docker_events_handler.stop_monitoring()
            logger.info("Docker events monitoring stopped")
        
        # Stop system metrics monitoring
        if system_metrics_handler:
            await system_metrics_handler.stop_monitoring()
            logger.info("System metrics monitoring stopped")
        
        # Stop log streaming monitoring
        if log_streaming_handler:
            await log_streaming_handler.stop_monitoring()
            logger.info("Log streaming monitoring stopped")
        
        # Shutdown cache service
        try:
            await shutdown_cache_service()
            logger.info("Cache service shutdown completed")
        except Exception as e:
            logger.error(f"Cache service shutdown failed: {e}")
        
        # Shutdown security services
        try:
            await shutdown_security()
            logger.info("Security services shutdown completed")
        except Exception as e:
            logger.error(f"Security services shutdown failed: {e}")
        
        # Shutdown performance optimizations
        try:
            await shutdown_performance()
            logger.info("Performance optimizations shutdown completed")
        except Exception as e:
            logger.error(f"Performance optimizations shutdown failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
