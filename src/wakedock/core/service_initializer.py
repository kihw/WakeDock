"""
Service initialization module for WakeDock.
Handles the initialization of various services in a modular way.
"""

import logging
from typing import Dict, Any, Optional, Tuple

from wakedock.config import get_settings
from wakedock.security.manager import initialize_security, get_security_manager
from wakedock.performance.integration import initialize_performance, get_performance_manager
from wakedock.database.database import init_database
from wakedock.infrastructure.cache.service import init_cache_service
from wakedock.core.docker_events import initialize_docker_events
from wakedock.core.system_metrics import initialize_system_metrics, SystemMetricsHandler
from wakedock.core.log_streaming import initialize_log_streaming
from wakedock.core.notifications import initialize_notifications, NotificationManager
from wakedock.infrastructure.caddy import caddy_manager
from wakedock.monitoring.prometheus import init_prometheus_exporter
from wakedock.core.monitoring import MonitoringService
from wakedock.core.orchestrator import DockerOrchestrator
from wakedock.analytics.storage import init_analytics_storage
from wakedock.analytics.collector import AnalyticsCollector, init_analytics_collector
from wakedock.analytics.usage_collector import initialize_usage_analytics_collector
from wakedock.analytics.types import AnalyticsConfig

logger = logging.getLogger(__name__)


async def init_security_services(security_config: Dict[str, Any]) -> Optional[Any]:
    """Initialize security services."""
    try:
        logger.info("Initializing security services...")
        security_services = await initialize_security(security_config)
        logger.info("Security services initialized successfully")
        logger.info("- JWT Rotation: ✓")
        logger.info("- Session Timeout: ✓") 
        logger.info("- Intrusion Detection: ✓")
        logger.info("- Security Config: ✓")
        return security_services
    except Exception as e:
        logger.error(f"Security services initialization failed: {e}")
        logger.warning("Application will continue but security features will be limited")
        return None


async def init_performance_services() -> Optional[Any]:
    """Initialize performance optimization services."""
    try:
        logger.info("Initializing performance optimizations...")
        performance_manager = await initialize_performance()
        logger.info("Performance optimizations initialized successfully")
        logger.info("- Intelligent Cache: ✓")
        logger.info("- Database Optimizer: ✓")
        logger.info("- API Middleware: ✓")
        logger.info("- Performance Monitoring: ✓")
        return performance_manager
    except Exception as e:
        logger.error(f"Performance optimization initialization failed: {e}")
        logger.warning("Application will continue but performance features will be limited")
        return None


def init_database_service() -> bool:
    """Initialize database service with retry logic."""
    import time
    max_retries = 5
    retry_delay = 2  # Start with 2 seconds
    
    for attempt in range(max_retries):
        try:
            init_database()
            logger.info("Database initialized successfully")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Database initialization attempt {attempt + 1} failed: {e}")
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.warning(f"Database initialization failed after {max_retries} attempts: {e}")
                logger.warning("Application will continue but database features may not work properly")
                return False


async def init_cache_services() -> bool:
    """Initialize cache services."""
    try:
        await init_cache_service()
        logger.info("Cache service initialized successfully")
        return True
    except Exception as e:
        logger.warning(f"Cache service initialization failed: {e}")
        logger.warning("Application will continue but caching features may not work properly")
        return False


async def init_caddy_service() -> bool:
    """Initialize Caddy proxy service."""
    try:
        await caddy_manager.initialize()
        logger.info("Caddy manager initialized successfully")
        return True
    except Exception as e:
        logger.warning(f"Caddy initialization failed: {e}")
        logger.warning("Application will continue but proxy features may not work properly")
        return False


async def init_monitoring_services() -> Tuple[Optional[Any], bool]:
    """Initialize monitoring and metrics services."""
    prometheus_success = False
    monitoring_service = None
    
    try:
        init_prometheus_exporter()
        logger.info("Prometheus exporter initialized successfully")
        prometheus_success = True
    except Exception as e:
        logger.warning(f"Prometheus exporter initialization failed: {e}")
        logger.warning("Metrics export will not be available")
    
    try:
        monitoring_service = MonitoringService()
        logger.info("Monitoring service initialized successfully")
    except Exception as e:
        logger.warning(f"Monitoring service initialization failed: {e}")
        logger.warning("System monitoring features may not work properly")
    
    return monitoring_service, prometheus_success


async def init_analytics_services() -> Optional[Any]:
    """Initialize analytics services."""
    try:
        logger.info("Initializing analytics services...")
        
        # Initialize analytics storage
        analytics_storage = await init_analytics_storage()
        
        # Initialize analytics collector
        analytics_config = AnalyticsConfig(
            enabled=True,
            retention_days=30,
            collection_interval=60,
            storage_backend="postgres",
            batch_size=1000
        )
        analytics_collector = init_analytics_collector(analytics_config)
        
        # Initialize usage analytics collector
        usage_collector = initialize_usage_analytics_collector(analytics_storage)
        
        # Start analytics services
        await analytics_collector.start()
        await usage_collector.start_collection()
        
        logger.info("Analytics services initialized successfully")
        logger.info("- Analytics Storage: ✓")
        logger.info("- Metrics Collector: ✓")
        logger.info("- Usage Analytics: ✓")
        
        return {
            "storage": analytics_storage,
            "collector": analytics_collector,
            "usage_collector": usage_collector
        }
    except Exception as e:
        logger.error(f"Analytics services initialization failed: {e}")
        logger.warning("Application will continue but analytics features will be limited")
        return None


async def init_core_services() -> Tuple[bool, bool, bool, bool]:
    """Initialize core application services."""
    docker_events_success = False
    metrics_success = False
    logs_success = False
    notifications_success = False
    
    # Initialize Docker client for services that need it
    docker_client = None
    try:
        import docker
        docker_client = docker.from_env()
    except Exception as e:
        logger.warning(f"Failed to initialize Docker client: {e}")
    
    try:
        if docker_client:
            initialize_docker_events(docker_client)
            logger.info("Docker events service initialized successfully")
            docker_events_success = True
        else:
            logger.warning("Docker client not available for events initialization")
    except Exception as e:
        logger.warning(f"Docker events initialization failed: {e}")
        logger.warning("Docker event monitoring will not be available")
    
    try:
        # Initialize system metrics handler
        handler = initialize_system_metrics()
        await handler.start_monitoring()
        logger.info("System metrics service initialized successfully")
        metrics_success = True
    except Exception as e:
        logger.warning(f"System metrics initialization failed: {e}")
        logger.warning("System metrics collection will not be available")
    
    try:
        if docker_client:
            initialize_log_streaming(docker_client)
            logger.info("Log streaming service initialized successfully")
            logs_success = True
        else:
            logger.warning("Docker client not available for log streaming initialization")
    except Exception as e:
        logger.warning(f"Log streaming initialization failed: {e}")
        logger.warning("Log streaming will not be available")
    
    try:
        # Initialize notification manager
        manager = initialize_notifications()
        logger.info("Notification service initialized successfully")
        notifications_success = True
    except Exception as e:
        logger.warning(f"Notification service initialization failed: {e}")
        logger.warning("Notifications will not be available")
    
    return docker_events_success, metrics_success, logs_success, notifications_success


def get_security_config() -> Dict[str, Any]:
    """Get security configuration."""
    settings = get_settings()
    
    return {
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
                "enable_audit_log": getattr(settings, "enable_audit_log", True),
                "enable_intrusion_detection": getattr(settings, "enable_intrusion_detection", True),
                "enable_jwt_rotation": getattr(settings, "enable_jwt_rotation", True),
                "enable_session_timeout": getattr(settings, "enable_session_timeout", True)
            },
            "password": {
                "min_length": 12,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_numbers": True,
                "require_special_chars": True,
                "max_failed_attempts": 5,
                "lockout_duration_minutes": 30
            },
            "rate_limiting": {
                "login_attempts_per_minute": 5,
                "api_requests_per_minute": 100,
                "global_requests_per_hour": 1000
            }
        }
    }


def log_initialization_summary(
    security_success: bool,
    performance_success: bool,
    database_success: bool,
    cache_success: bool,
    caddy_success: bool,
    monitoring_success: bool,
    prometheus_success: bool,
    analytics_success: bool,
    core_services_success: Tuple[bool, bool, bool, bool]
) -> None:
    """Log a summary of the initialization process."""
    logger.info("=== WakeDock Initialization Summary ===")
    logger.info(f"Security Services: {'✓' if security_success else '✗'}")
    logger.info(f"Performance Services: {'✓' if performance_success else '✗'}")
    logger.info(f"Database: {'✓' if database_success else '✗'}")
    logger.info(f"Cache: {'✓' if cache_success else '✗'}")
    logger.info(f"Caddy Proxy: {'✓' if caddy_success else '✗'}")
    logger.info(f"Monitoring: {'✓' if monitoring_success else '✗'}")
    logger.info(f"Prometheus: {'✓' if prometheus_success else '✗'}")
    logger.info(f"Analytics: {'✓' if analytics_success else '✗'}")
    
    docker_events, metrics, logs, notifications = core_services_success
    logger.info(f"Docker Events: {'✓' if docker_events else '✗'}")
    logger.info(f"System Metrics: {'✓' if metrics else '✗'}")
    logger.info(f"Log Streaming: {'✓' if logs else '✗'}")
    logger.info(f"Notifications: {'✓' if notifications else '✗'}")
    logger.info("======================================")


async def initialize_all_services() -> Dict[str, Any]:
    """Initialize all WakeDock services."""
    logger.info("Starting WakeDock service initialization...")
    
    # Get configuration
    security_config = get_security_config()
    
    # Initialize services in order of priority
    security_services = await init_security_services(security_config)
    performance_manager = await init_performance_services()
    database_success = init_database_service()
    cache_success = await init_cache_services()
    caddy_success = await init_caddy_service()
    monitoring_service, prometheus_success = await init_monitoring_services()
    analytics_services = await init_analytics_services()
    core_services_success = await init_core_services()
    
    # Log summary
    log_initialization_summary(
        security_success=security_services is not None,
        performance_success=performance_manager is not None,
        database_success=database_success,
        cache_success=cache_success,
        caddy_success=caddy_success,
        monitoring_success=monitoring_service is not None,
        prometheus_success=prometheus_success,
        analytics_success=analytics_services is not None,
        core_services_success=core_services_success
    )
    
    return {
        "security_services": security_services,
        "performance_manager": performance_manager,
        "monitoring_service": monitoring_service,
        "analytics_services": analytics_services,
        "database_success": database_success,
        "cache_success": cache_success,
        "caddy_success": caddy_success,
        "prometheus_success": prometheus_success,
        "core_services_success": core_services_success
    }