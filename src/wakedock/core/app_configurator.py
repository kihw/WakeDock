"""
Application configuration and setup module for WakeDock.
Handles logging configuration, Docker validation, and app creation.
"""

import logging
import logging.config
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

import docker

from wakedock.config import get_settings
from wakedock.api.app import create_app
from wakedock.log_config import setup_logging


logger = logging.getLogger(__name__)


def setup_application_logging() -> Optional[str]:
    """Set up application logging configuration."""
    fallback_warning = None
    
    try:
        setup_logging()
        logger.info("Logging configuration loaded successfully")
    except Exception as e:
        # Fallback to basic console logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fallback_warning = f"Could not load logging configuration: {e}. Using fallback console logging."
    
    return fallback_warning


def validate_docker_connection() -> bool:
    """Validate Docker daemon connection."""
    try:
        client = docker.from_env()
        client.ping()
        logger.info("Docker connection validated successfully")
        
        # Get Docker info for additional logging
        info = client.info()
        logger.info(f"Docker version: {info.get('ServerVersion', 'Unknown')}")
        logger.info(f"Docker containers running: {info.get('ContainersRunning', 0)}")
        
        return True
    except docker.errors.DockerException as e:
        logger.warning(f"Docker connection failed: {e}")
        logger.warning("Docker-related features will not be available")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error during Docker validation: {e}")
        return False


def create_fastapi_app(services: Dict[str, Any]) -> Any:
    """Create and configure the FastAPI application."""
    try:
        # Create orchestrator and monitoring service if not already provided
        orchestrator = services.get("orchestrator")
        if not orchestrator:
            from wakedock.core.orchestrator import DockerOrchestrator
            orchestrator = DockerOrchestrator()
            logger.info("DockerOrchestrator created")
        
        monitoring_service = services.get("monitoring_service")
        
        app = create_app(orchestrator=orchestrator, monitoring=monitoring_service)
        logger.info("FastAPI application created successfully")
        
        # Store service references in app state for access in routes
        app.state.security_services = services.get("security_services")
        app.state.performance_manager = services.get("performance_manager")
        app.state.monitoring_service = monitoring_service
        app.state.orchestrator = orchestrator
        
        return app
    except Exception as e:
        logger.error(f"Failed to create FastAPI application: {e}")
        raise


def get_uvicorn_config() -> Dict[str, Any]:
    """Get Uvicorn server configuration."""
    settings = get_settings()
    
    config = {
        "host": getattr(settings, "host", "0.0.0.0"),
        "port": getattr(settings, "port", 8000),
        "log_level": getattr(settings, "log_level", "info").lower(),
        "reload": getattr(settings, "debug", False),
        "workers": 1 if getattr(settings, "debug", False) else getattr(settings, "workers", 4),
        "access_log": getattr(settings, "access_log", True),
        "server_header": False,  # Security: hide server info
        "date_header": False,    # Security: hide date header
    }
    
    # SSL configuration if available
    ssl_keyfile = getattr(settings, "ssl_keyfile", None)
    ssl_certfile = getattr(settings, "ssl_certfile", None)
    
    if ssl_keyfile and ssl_certfile:
        if Path(ssl_keyfile).exists() and Path(ssl_certfile).exists():
            config["ssl_keyfile"] = ssl_keyfile
            config["ssl_certfile"] = ssl_certfile
            logger.info("SSL configuration loaded")
        else:
            logger.warning("SSL files not found, running without SSL")
    
    return config


def validate_environment() -> Tuple[bool, List[str]]:
    """Validate the application environment."""
    issues = []
    settings = get_settings()
    
    # Check required environment variables
    required_vars = ["database_url", "redis_url"]
    for var in required_vars:
        if not getattr(settings, var, None):
            issues.append(f"Missing required environment variable: {var.upper()}")
    
    # Check file permissions for data directories
    data_path = getattr(settings, "data_path", "/app/data")
    if not Path(data_path).exists():
        try:
            Path(data_path).mkdir(parents=True, exist_ok=True)
            logger.info(f"Created data directory: {data_path}")
        except Exception as e:
            issues.append(f"Cannot create data directory {data_path}: {e}")
    
    # Check if data directory is writable
    if Path(data_path).exists() and not Path(data_path).is_dir():
        issues.append(f"Data path {data_path} is not a directory")
    elif Path(data_path).exists():
        try:
            test_file = Path(data_path) / ".write_test"
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            issues.append(f"Data directory {data_path} is not writable: {e}")
    
    # Check log directory
    log_path = getattr(settings, "log_path", "/app/logs")
    if not Path(log_path).exists():
        try:
            Path(log_path).mkdir(parents=True, exist_ok=True)
            logger.info(f"Created log directory: {log_path}")
        except Exception as e:
            issues.append(f"Cannot create log directory {log_path}: {e}")
    
    # Security checks
    if getattr(settings, "environment", "development") == "production":
        # Check for production-ready settings
        if getattr(settings, "debug", True):
            issues.append("Debug mode should be disabled in production")
        
        jwt_secret = getattr(settings, "jwt_secret_key", "")
        if not jwt_secret or len(jwt_secret) < 32:
            issues.append("JWT secret key must be at least 32 characters in production")
        
        if "default" in jwt_secret.lower() or "change" in jwt_secret.lower():
            issues.append("JWT secret key appears to be using default/placeholder value")
    
    success = len(issues) == 0
    if success:
        logger.info("Environment validation passed")
    else:
        logger.warning(f"Environment validation found {len(issues)} issues:")
        for issue in issues:
            logger.warning(f"  - {issue}")
    
    return success, issues


def log_startup_banner() -> None:
    """Log the WakeDock startup banner."""
    settings = get_settings()
    version = getattr(settings, "version", "1.0.0")
    environment = getattr(settings, "environment", "development")
    
    banner = f"""
    ╔══════════════════════════════════════════════════╗
    ║                   WakeDock                       ║
    ║            Docker Management Platform            ║
    ║                                                  ║
    ║  Version: {version:<37} ║
    ║  Environment: {environment:<31} ║
    ║  Mode: {'Production' if environment == 'production' else 'Development':<38} ║
    ╚══════════════════════════════════════════════════╝
    """
    
    logger.info(banner)


def prepare_application() -> Tuple[Any, Dict[str, Any], Optional[str]]:
    """Prepare the application for startup."""
    # Set up logging first
    fallback_warning = setup_application_logging()
    
    # Log startup banner
    log_startup_banner()
    
    # Validate environment
    env_valid, env_issues = validate_environment()
    if not env_valid:
        logger.error("Environment validation failed. Application may not work correctly.")
        for issue in env_issues:
            logger.error(f"  - {issue}")
    
    # Validate Docker connection
    docker_valid = validate_docker_connection()
    
    # Get Uvicorn configuration
    uvicorn_config = get_uvicorn_config()
    
    return uvicorn_config, {
        "environment_valid": env_valid,
        "environment_issues": env_issues,
        "docker_valid": docker_valid,
    }, fallback_warning