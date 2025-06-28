"""
CORS middleware configuration for the WakeDock API.
Handles Cross-Origin Resource Sharing for the web dashboard.
"""

from typing import List, Optional, Union
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import logging

logger = logging.getLogger(__name__)


class CORSConfig:
    """CORS configuration for different environments."""
    
    # Development configuration
    DEVELOPMENT = {
        "allow_origins": ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"],
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        "allow_headers": ["*"],
        "expose_headers": ["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
        "max_age": 86400  # 24 hours
    }
    
    # Production configuration (more restrictive)
    PRODUCTION = {
        "allow_origins": [],  # Must be set via environment variables
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "PATCH"],
        "allow_headers": [
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With"
        ],
        "expose_headers": ["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
        "max_age": 3600  # 1 hour
    }
    
    # Testing configuration
    TESTING = {
        "allow_origins": ["*"],
        "allow_credentials": False,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
        "expose_headers": [],
        "max_age": 0
    }


def setup_cors(
    app: FastAPI,
    environment: str = "development",
    custom_origins: Optional[List[str]] = None,
    custom_config: Optional[dict] = None
) -> None:
    """
    Set up CORS middleware for the FastAPI app.
    
    Args:
        app: FastAPI application instance
        environment: Environment name (development, production, testing)
        custom_origins: Custom list of allowed origins
        custom_config: Custom CORS configuration
    """
    
    # Get base configuration for environment
    if custom_config:
        config = custom_config
    elif environment == "production":
        config = CORSConfig.PRODUCTION.copy()
    elif environment == "testing":
        config = CORSConfig.TESTING.copy()
    else:
        config = CORSConfig.DEVELOPMENT.copy()
    
    # Override origins if provided
    if custom_origins:
        config["allow_origins"] = custom_origins
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        **config
    )
    
    logger.info(
        f"CORS configured for {environment} environment",
        extra={
            "allowed_origins": config["allow_origins"],
            "allow_credentials": config["allow_credentials"],
            "allowed_methods": config["allow_methods"]
        }
    )


def get_cors_origins_from_env() -> List[str]:
    """
    Get CORS origins from environment variables.
    
    Returns:
        List of allowed origins
    """
    import os
    
    origins_env = os.getenv("CORS_ORIGINS", "")
    if not origins_env:
        return []
    
    # Split by comma and clean up
    origins = [origin.strip() for origin in origins_env.split(",")]
    origins = [origin for origin in origins if origin]  # Remove empty strings
    
    return origins


def validate_cors_origin(origin: str) -> bool:
    """
    Validate a CORS origin format.
    
    Args:
        origin: Origin URL to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not origin:
        return False
    
    # Allow wildcard
    if origin == "*":
        return True
    
    # Basic URL validation
    try:
        from urllib.parse import urlparse
        parsed = urlparse(origin)
        return bool(parsed.scheme and parsed.netloc)
    except Exception:
        return False


def create_cors_config(
    allowed_origins: Union[List[str], str] = None,
    allow_credentials: bool = True,
    allow_methods: List[str] = None,
    allow_headers: List[str] = None,
    expose_headers: List[str] = None,
    max_age: int = 3600
) -> dict:
    """
    Create a custom CORS configuration.
    
    Args:
        allowed_origins: Allowed origins (list or comma-separated string)
        allow_credentials: Whether to allow credentials
        allow_methods: Allowed HTTP methods
        allow_headers: Allowed headers
        expose_headers: Headers to expose to the client
        max_age: Cache duration for preflight requests
        
    Returns:
        CORS configuration dictionary
    """
    
    # Process origins
    if isinstance(allowed_origins, str):
        if allowed_origins == "*":
            origins = ["*"]
        else:
            origins = [origin.strip() for origin in allowed_origins.split(",")]
    elif isinstance(allowed_origins, list):
        origins = allowed_origins
    else:
        origins = []
    
    # Validate origins
    valid_origins = []
    for origin in origins:
        if validate_cors_origin(origin):
            valid_origins.append(origin)
        else:
            logger.warning(f"Invalid CORS origin ignored: {origin}")
    
    # Default methods
    if allow_methods is None:
        allow_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    
    # Default headers
    if allow_headers is None:
        allow_headers = [
            "Accept",
            "Accept-Language", 
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With"
        ]
    
    # Default expose headers
    if expose_headers is None:
        expose_headers = [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining", 
            "X-RateLimit-Reset"
        ]
    
    return {
        "allow_origins": valid_origins,
        "allow_credentials": allow_credentials,
        "allow_methods": allow_methods,
        "allow_headers": allow_headers,
        "expose_headers": expose_headers,
        "max_age": max_age
    }


# Preset configurations for common scenarios
SECURE_CORS_CONFIG = create_cors_config(
    allowed_origins=[],  # Must be explicitly set
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    max_age=3600
)

DEVELOPMENT_CORS_CONFIG = create_cors_config(
    allowed_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=86400
)

PERMISSIVE_CORS_CONFIG = create_cors_config(
    allowed_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=0
)
