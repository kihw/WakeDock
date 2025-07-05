"""
WakeDock Security Validation Module

Provides comprehensive input validation, sanitization, and security checks.
"""

# Import all necessary components
from .config import SecurityConfig
from .exceptions import ValidationError, SecurityValidationError, InputSanitizationError
from .types import (
    SecureString, ServiceName, DockerImage, PortMapping, FilePath, 
    VolumeMount, EnvironmentVariable, NetworkName, IPAddress, URL, 
    Password, Username, Email
)
from .utils import (
    SecurityUtils, sanitize_html, sanitize_sql_identifier, 
    validate_json_input, sanitize_input
)
from .functions import (
    validate_service_name, validate_docker_image, validate_email, 
    validate_path, validate_password_strength
)

# Try to import models if pydantic is available
try:
    from .models import ServiceCreateRequest, UserCreateRequest, ConfigUpdateRequest
    PYDANTIC_AVAILABLE = True
except ImportError:
    # Fallback for environments without pydantic
    PYDANTIC_AVAILABLE = False
    ServiceCreateRequest = None
    UserCreateRequest = None
    ConfigUpdateRequest = None


# Export commonly used items
__all__ = [
    # Exceptions
    'ValidationError',
    'SecurityValidationError', 
    'InputSanitizationError',
    
    # Configuration
    'SecurityConfig',
    
    # Types
    'SecureString',
    'ServiceName',
    'DockerImage',
    'PortMapping',
    'FilePath',
    'VolumeMount',
    'EnvironmentVariable',
    'NetworkName',
    'IPAddress',
    'URL',
    'Password',
    'Username',
    'Email',
    
    # Models (if available)
    'ServiceCreateRequest',
    'UserCreateRequest',
    'ConfigUpdateRequest',
    
    # Utils
    'SecurityUtils',
    'sanitize_html',
    'sanitize_sql_identifier',
    'validate_json_input',
    'sanitize_input',
    
    # Functions
    'validate_service_name',
    'validate_docker_image',
    'validate_email',
    'validate_path',
    'validate_password_strength',
    
    # Status
    'PYDANTIC_AVAILABLE'
]
