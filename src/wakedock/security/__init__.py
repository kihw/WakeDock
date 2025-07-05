"""
WakeDock Security Module

Provides comprehensive security features including input validation,
rate limiting, and security utilities.
"""

from .validation import (
    ValidationError,
    SecurityConfig,
    SecureString,
    ServiceName,
    DockerImage,
    PortMapping,
    FilePath,
    VolumeMount,
    EnvironmentVariable,
    NetworkName,
    IPAddress,
    URL,
    Password,
    Username,
    Email,
    ServiceCreateRequest,
    UserCreateRequest,
    ConfigUpdateRequest,
    SecurityUtils,
    sanitize_html,
    sanitize_sql_identifier,
    validate_json_input
)

from .rate_limit import (
    RateLimit,
    RateLimitResult,
    RateLimitError,
    RateLimitStrategy,
    RateLimitManager,
    RateLimitMiddleware,
    rate_limit,
    get_rate_limiter,
    init_rate_limiting
)

# Enhanced security features
from .audit import (
    AuditLog, AuditEventType, AuditSeverity, AuditEventData,
    AuditLogger, AuditService, get_audit_service
)

from .rbac import (
    Permission, ResourceType, Role, PermissionModel, RBACService,
    get_rbac_service, require_permission, require_permissions, RequirePermission
)

from .middleware import (
    SecurityAuditMiddleware, RequestTimingMiddleware, CORSSecurityMiddleware
)

from .config import (
    PasswordPolicy, RateLimitConfig, SessionConfig, AuditConfig,
    EncryptionConfig, SecurityFeatures, SecurityConfig,
    SecurityConfigManager, get_security_config_manager, get_security_config
)


__all__ = [
    # Validation
    'ValidationError',
    'SecurityConfig',
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
    'ServiceCreateRequest',
    'UserCreateRequest',
    'ConfigUpdateRequest',
    'SecurityUtils',
    'sanitize_html',
    'sanitize_sql_identifier',
    'validate_json_input',
    
    # Rate Limiting
    'RateLimit',
    'RateLimitResult',
    'RateLimitError',
    'RateLimitStrategy',
    'RateLimitManager',
    'RateLimitMiddleware',
    'rate_limit',
    'get_rate_limiter',
    'init_rate_limiting',
    
    # Enhanced security features
    # Audit system
    'AuditLog', 'AuditEventType', 'AuditSeverity', 'AuditEventData',
    'AuditLogger', 'AuditService', 'get_audit_service',
    
    # RBAC system
    'Permission', 'ResourceType', 'Role', 'PermissionModel', 'RBACService',
    'get_rbac_service', 'require_permission', 'require_permissions', 'RequirePermission',
    
    # Middleware
    'SecurityAuditMiddleware', 'RequestTimingMiddleware', 'CORSSecurityMiddleware',
    
    # Configuration
    'PasswordPolicy', 'RateLimitConfig', 'SessionConfig', 'AuditConfig',
    'EncryptionConfig', 'SecurityFeatures', 'SecurityConfig',
    'SecurityConfigManager', 'get_security_config_manager', 'get_security_config'
]
