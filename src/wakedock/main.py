"""
Main application entry point for WakeDock.
Refactored for better maintainability and modularity.
"""

import asyncio
import logging
import uvicorn

from wakedock.config import get_settings
from wakedock.core.app_configurator import prepare_application, create_fastapi_app
from wakedock.core.service_initializer import initialize_all_services
from wakedock.infrastructure.cache.service import shutdown_cache_service
from wakedock.security.manager import shutdown_security
from wakedock.performance.integration import shutdown_performance


async def start_application_services(app, services):
    """Start all application services and connect them."""
    logger = logging.getLogger(__name__)
    settings = get_settings()
    
    # Start monitoring service
    monitoring_service = services.get("monitoring_service")
    if settings.monitoring.enabled and monitoring_service:
        await monitoring_service.start()
        logger.info("Monitoring service started")
    
    # Start WebSocket event handlers
    await start_websocket_handlers(services)
    
    # Send startup notification
    await send_startup_notification(services)


async def start_websocket_handlers(services):
    """Start WebSocket event handlers for real-time updates."""
    logger = logging.getLogger(__name__)
    
    # Start Docker events monitoring
    docker_events_handler = services.get("docker_events_handler")
    if docker_events_handler:
        from wakedock.api.websocket import handle_docker_event
        docker_events_handler.subscribe(handle_docker_event)
        await docker_events_handler.start_monitoring()
        logger.info("Docker events monitoring started")
    
    # Start system metrics monitoring
    system_metrics_handler = services.get("system_metrics_handler")
    if system_metrics_handler:
        from wakedock.api.websocket import broadcast_system_update
        system_metrics_handler.subscribe(broadcast_system_update)
        await system_metrics_handler.start_monitoring()
        logger.info("System metrics monitoring started")
    
    # Start log streaming monitoring
    log_streaming_handler = services.get("log_streaming_handler")
    if log_streaming_handler:
        from wakedock.api.websocket import broadcast_log_entry
        log_streaming_handler.subscribe(broadcast_log_entry)
        await log_streaming_handler.start_monitoring()
        logger.info("Log streaming monitoring started")
    
    # Connect notification manager to WebSocket
    notification_manager = services.get("notification_manager")
    if notification_manager:
        from wakedock.api.websocket import broadcast_notification
        notification_manager.subscribe(broadcast_notification)
        logger.info("Notification manager connected to WebSocket")


async def send_startup_notification(services):
    """Send startup notification through the notification system."""
    notification_manager = services.get("notification_manager")
    if notification_manager:
        from wakedock.core.notifications import NotificationLevel, NotificationCategory
        await notification_manager.create_notification(
            title="WakeDock Started",
            message="WakeDock Docker management platform has started successfully",
            level=NotificationLevel.SUCCESS,
            category=NotificationCategory.SYSTEM,
            source="wakedock"
        )


async def shutdown_application_services(services):
    """Gracefully shutdown all application services."""
    logger = logging.getLogger(__name__)
    settings = get_settings()
    
    # Stop monitoring service
    monitoring_service = services.get("monitoring_service")
    if settings.monitoring.enabled and monitoring_service:
        await monitoring_service.stop()
        logger.info("Monitoring service stopped")
    
    # Stop Prometheus exporter
    prometheus_exporter = services.get("prometheus_exporter")
    if prometheus_exporter:
        await prometheus_exporter.stop()
        logger.info("Prometheus exporter stopped")
    
    # Stop event handlers
    await stop_event_handlers(services)
    
    # Shutdown core services
    await shutdown_core_services()


async def stop_event_handlers(services):
    """Stop all event handlers."""
    logger = logging.getLogger(__name__)
    
    # Stop Docker events monitoring
    docker_events_handler = services.get("docker_events_handler")
    if docker_events_handler:
        await docker_events_handler.stop_monitoring()
        logger.info("Docker events monitoring stopped")
    
    # Stop system metrics monitoring
    system_metrics_handler = services.get("system_metrics_handler")
    if system_metrics_handler:
        await system_metrics_handler.stop_monitoring()
        logger.info("System metrics monitoring stopped")
    
    # Stop log streaming monitoring
    log_streaming_handler = services.get("log_streaming_handler")
    if log_streaming_handler:
        await log_streaming_handler.stop_monitoring()
        logger.info("Log streaming monitoring stopped")


async def shutdown_core_services():
    """Shutdown core infrastructure services."""
    logger = logging.getLogger(__name__)
    
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


async def main():
    """Main application entry point."""
    # Prepare application configuration and environment
    uvicorn_config, prep_status, fallback_warning = prepare_application()
    
    logger = logging.getLogger(__name__)
    
    # Log any fallback warnings
    if fallback_warning:
        logger.warning(fallback_warning)
    
    # Initialize all services
    services = await initialize_all_services()
    
    # Create FastAPI application
    app = create_fastapi_app(services)
    
    # Start application services
    await start_application_services(app, services)
    
    # Create and start the server
    server = uvicorn.Server(uvicorn.Config(app, **uvicorn_config))
    
    settings = get_settings()
    logger.info(f"WakeDock started on {uvicorn_config['host']}:{uvicorn_config['port']}")
    
    try:
        await server.serve()
    except KeyboardInterrupt:
        logger.info("Shutting down WakeDock...")
    finally:
        await shutdown_application_services(services)


if __name__ == "__main__":
    asyncio.run(main())