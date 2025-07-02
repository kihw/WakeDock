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
from wakedock.database.database import init_database


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
    
    # Start monitoring service
    if settings.monitoring.enabled:
        await monitoring_service.start()
    
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
        if settings.monitoring.enabled:
            await monitoring_service.stop()


if __name__ == "__main__":
    asyncio.run(main())
