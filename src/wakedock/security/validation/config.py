"""
Security configuration constants and settings.
"""

class SecurityConfig:
    """Security configuration constants."""
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 12
    MAX_PASSWORD_LENGTH = 128
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_NUMBERS = True
    PASSWORD_REQUIRE_SPECIAL_CHARS = True
    PASSWORD_BLACKLIST = [
        'password', '123456', 'admin', 'root', 'user', 'test',
        'wakedock', 'docker', 'caddy', 'postgres', 'redis'
    ]
    
    # Service name validation
    SERVICE_NAME_PATTERN = r'^[a-zA-Z0-9][a-zA-Z0-9._-]*$'
    SERVICE_NAME_MAX_LENGTH = 64
    SERVICE_NAME_BLACKLIST = ['admin', 'root', 'system', 'api', 'www']
    
    # Network validation
    ALLOWED_PRIVATE_NETWORKS = [
        '10.0.0.0/8',
        '172.16.0.0/12',
        '192.168.0.0/16',
        '127.0.0.0/8'
    ]
    
    # Docker image validation
    TRUSTED_REGISTRIES = [
        'docker.io',
        'gcr.io',
        'ghcr.io',
        'quay.io',
        'registry.redhat.io'
    ]
    
    # File path validation
    ALLOWED_PATH_PREFIXES = ['/app', '/data', '/tmp', '/var/log']
    BLOCKED_PATH_PATTERNS = [
        r'\.\./',  # Directory traversal
        r'/etc/',  # System config
        r'/root/', # Root directory
        r'/proc/', # Process info
        r'/sys/',  # System info
    ]
    
    # Environment variable validation
    BLOCKED_ENV_VARS = [
        'PATH', 'HOME', 'USER', 'SHELL', 'PWD',
        'SSH_AUTH_SOCK', 'SSH_AGENT_PID',
        'SUDO_USER', 'SUDO_UID', 'SUDO_GID'
    ]
