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
from wakedock.core.caddy import caddy_manager
from wakedock.core.docker_events import initialize_docker_events
from wakedock.core.system_metrics import initialize_system_metrics
from wakedock.database.database import init_database
import docker


async def main():
    """Main application entry point"""
    # Load configuration
    settings = get_settings()
    
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
    
    # Initialize database
    try:
        init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")
        logger.warning("Application will continue but database features may not work properly")
        # Don't raise the exception - allow the app to start
    
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

    # Initialize Caddy manager and force correct configuration
    try:
        logger.info("Initializing Caddy manager...")
        # Just importing caddy_manager will trigger initialization
        
        # Detect and fix Caddy default page if present
        logger.info("Checking Caddy configuration...")
        await caddy_manager.detect_and_fix_default_page()
        
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
    
    # Connect monitoring service to orchestrator if both are available
    if orchestrator and monitoring_service:
        monitoring_service.set_orchestrator(orchestrator)
    
    # Create FastAPI app
    app = create_app(orchestrator, monitoring_service)
    
    # Store handlers in app state
    app.state.docker_events_handler = docker_events_handler
    app.state.system_metrics_handler = system_metrics_handler
    
    # Start monitoring service
    if settings.monitoring.enabled and monitoring_service:
        await monitoring_service.start()
    
    # Start Docker events monitoring
    if docker_events_handler:
        from wakedock.api.routes.websocket import handle_docker_event
        docker_events_handler.subscribe(handle_docker_event)
        await docker_events_handler.start_monitoring()
        logger.info("Docker events monitoring started")
    
    # Start system metrics monitoring
    if system_metrics_handler:
        from wakedock.api.routes.websocket import broadcast_system_update
        system_metrics_handler.subscribe(broadcast_system_update)
        await system_metrics_handler.start_monitoring()
        logger.info("System metrics monitoring started")
    
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
        
        # Stop Docker events monitoring
        if docker_events_handler:
            await docker_events_handler.stop_monitoring()
            logger.info("Docker events monitoring stopped")
        
        # Stop system metrics monitoring
        if system_metrics_handler:
            await system_metrics_handler.stop_monitoring()
            logger.info("System metrics monitoring stopped")


if __name__ == "__main__":
    asyncio.run(main())
