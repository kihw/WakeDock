"""
Secure validated types for input validation.
"""

import re
import ipaddress
from typing import Any
from urllib.parse import urlparse
from pathlib import Path

# Simple validators fallback
class SimpleValidators:
    @staticmethod
    def email(email: str) -> bool:
        """Simple email validation."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def url(url: str) -> bool:
        """Simple URL validation."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    @staticmethod
    def domain(domain: str) -> bool:
        """Simple domain validation."""
        pattern = r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, domain) is not None

try:
    import validators
except ImportError:
    validators = SimpleValidators()

from .config import SecurityConfig
from .exceptions import ValidationError


class SecureString(str):
    """String type that provides validation and sanitization."""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise ValidationError('string required')
        
        # Basic sanitization
        v = v.strip()
        
        # Check for null bytes
        if '\x00' in v:
            raise ValidationError('null bytes not allowed')
        
        # Check for control characters
        if any(ord(c) < 32 and c not in '\t\n\r' for c in v):
            raise ValidationError('control characters not allowed')
        
        return cls(v)


class ServiceName(SecureString):
    """Validated service name."""
    
    @classmethod
    def validate(cls, v):
        v = super().validate(v)
        
        # Length check
        if len(v) > SecurityConfig.SERVICE_NAME_MAX_LENGTH:
            raise ValidationError(f'service name too long (max {SecurityConfig.SERVICE_NAME_MAX_LENGTH})')
        
        if len(v) < 1:
            raise ValidationError('service name cannot be empty')
        
        # Pattern check
        if not re.match(SecurityConfig.SERVICE_NAME_PATTERN, v):
            raise ValidationError('invalid service name format')
        
        # Blacklist check
        if v.lower() in SecurityConfig.SERVICE_NAME_BLACKLIST:
            raise ValidationError('service name is reserved')
        
        return cls(v)


class DockerImage(SecureString):
    """Validated Docker image name."""
    
    @classmethod
    def validate(cls, v):
        v = super().validate(v)
        
        # Parse image name
        parts = v.split('/')
        
        # Check registry
        if len(parts) >= 2:
            registry = parts[0]
            
            # If registry contains a dot or port, validate it
            if '.' in registry or ':' in registry:
                registry_host = registry.split(':')[0]
                
                # Allow localhost for development
                if registry_host not in ['localhost', '127.0.0.1']:
                    if registry_host not in SecurityConfig.TRUSTED_REGISTRIES:
                        raise ValidationError(f'untrusted registry: {registry_host}')
        
        # Basic format validation
        if not re.match(r'^[a-zA-Z0-9._/-]+(?::[a-zA-Z0-9._-]+)?$', v):
            raise ValidationError('invalid image name format')
        
        return cls(v)


class PortMapping(SecureString):
    """Validated port mapping."""
    
    @classmethod
    def validate(cls, v):
        v = super().validate(v)
        
        # Port mapping format: host_port:container_port[/protocol]
        pattern = r'^(\d+):(\d+)(?:/(tcp|udp))?$'
        match = re.match(pattern, v)
        
        if not match:
            raise ValidationError('invalid port mapping format')
        
        host_port = int(match.group(1))
        container_port = int(match.group(2))
        
        # Port range validation
        if not (1 <= host_port <= 65535):
            raise ValidationError('invalid host port range')
        
        if not (1 <= container_port <= 65535):
            raise ValidationError('invalid container port range')
        
        # Privileged port check
        if host_port < 1024:
            raise ValidationError('privileged ports not allowed')
        
        return cls(v)


class FilePath(SecureString):
    """Validated file path."""
    
    @classmethod
    def validate(cls, v):
        v = super().validate(v)
        
        # Normalize path
        try:
            path = Path(v).resolve()
            v = str(path)
        except (OSError, ValueError):
            raise ValidationError('invalid file path')
        
        # Check for blocked patterns
        for pattern in SecurityConfig.BLOCKED_PATH_PATTERNS:
            if re.search(pattern, v):
                raise ValidationError(f'blocked path pattern: {pattern}')
        
        # Check allowed prefixes (in production)
        # if not any(v.startswith(prefix) for prefix in SecurityConfig.ALLOWED_PATH_PREFIXES):
        #     raise ValidationError('path not in allowed directories')
        
        return cls(v)


class VolumeMount(SecureString):
    """Validated volume mount."""
    
    @classmethod
    def validate(cls, v):
        v = super().validate(v)
        
        # Volume mount format: host_path:container_path[:options]
        parts = v.split(':')
        
        if len(parts) < 2 or len(parts) > 3:
            raise ValidationError('invalid volume mount format')
        
        host_path, container_path = parts[0], parts[1]
        options = parts[2] if len(parts) == 3 else None
        
        # Validate paths
        FilePath.validate(host_path)
        FilePath.validate(container_path)
        
        # Validate options
        if options:
            valid_options = ['ro', 'rw', 'z', 'Z', 'consistent', 'cached', 'delegated']
            option_list = options.split(',')
            
            for option in option_list:
                if option not in valid_options:
                    raise ValidationError(f'invalid volume option: {option}')
        
        return cls(v)


class EnvironmentVariable(SecureString):
    """Validated environment variable."""
    
    @classmethod
    def validate(cls, v):
        v = super().validate(v)
        
        # Environment variable format: KEY=VALUE
        if '=' not in v:
            raise ValidationError('environment variable must contain =')
        
        key, value = v.split('=', 1)
        
        # Validate key
        if not re.match(r'^[A-Z][A-Z0-9_]*$', key):
            raise ValidationError('invalid environment variable name')
        
        # Check blacklist
        if key in SecurityConfig.BLOCKED_ENV_VARS:
            raise ValidationError(f'environment variable {key} is not allowed')
        
        # Validate value (basic checks)
        if len(value) > 1024:
            raise ValidationError('environment variable value too long')
        
        return cls(v)


class NetworkName(SecureString):
    """Validated network name."""
    
    @classmethod
    def validate(cls, v):
        v = super().validate(v)
        
        # Network name validation
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*$', v):
            raise ValidationError('invalid network name format')
        
        if len(v) > 64:
            raise ValidationError('network name too long')
        
        return cls(v)


class IPAddress(SecureString):
    """Validated IP address."""
    
    @classmethod
    def validate(cls, v):
        v = super().validate(v)
        
        try:
            ip = ipaddress.ip_address(v)
        except ValueError:
            raise ValidationError('invalid IP address')
        
        # Check if it's a private/allowed IP
        is_allowed = False
        
        for network in SecurityConfig.ALLOWED_PRIVATE_NETWORKS:
            if ip in ipaddress.ip_network(network):
                is_allowed = True
                break
        
        if not is_allowed and not ip.is_loopback:
            raise ValidationError('IP address not in allowed networks')
        
        return cls(v)


class URL(SecureString):
    """Validated URL."""
    
    @classmethod
    def validate(cls, v):
        v = super().validate(v)
        
        # Basic URL validation
        if not validators.url(v):
            raise ValidationError('invalid URL format')
        
        parsed = urlparse(v)
        
        # Check scheme
        if parsed.scheme not in ['http', 'https']:
            raise ValidationError('only HTTP/HTTPS URLs allowed')
        
        # Check for localhost/private IPs in production
        if parsed.hostname:
            try:
                ip = ipaddress.ip_address(parsed.hostname)
                if not ip.is_private and not ip.is_loopback:
                    # Allow public IPs for webhooks, etc.
                    pass
            except ValueError:
                # Hostname is not an IP, validate as domain
                if not validators.domain(parsed.hostname):
                    raise ValidationError('invalid hostname in URL')
        
        return cls(v)


class Password(SecureString):
    """Validated password."""
    
    @classmethod
    def validate(cls, v):
        v = super().validate(v)
        
        # Length check
        if len(v) < SecurityConfig.MIN_PASSWORD_LENGTH:
            raise ValidationError(f'password too short (min {SecurityConfig.MIN_PASSWORD_LENGTH} characters)')
        
        if len(v) > SecurityConfig.MAX_PASSWORD_LENGTH:
            raise ValidationError(f'password too long (max {SecurityConfig.MAX_PASSWORD_LENGTH} characters)')
        
        # Character requirements
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v)
        
        if SecurityConfig.PASSWORD_REQUIRE_UPPERCASE and not has_upper:
            raise ValidationError('password must contain uppercase letters')
        
        if SecurityConfig.PASSWORD_REQUIRE_LOWERCASE and not has_lower:
            raise ValidationError('password must contain lowercase letters')
        
        if SecurityConfig.PASSWORD_REQUIRE_NUMBERS and not has_digit:
            raise ValidationError('password must contain numbers')
        
        if SecurityConfig.PASSWORD_REQUIRE_SPECIAL_CHARS and not has_special:
            raise ValidationError('password must contain special characters')
        
        # Blacklist check
        v_lower = v.lower()
        for blocked in SecurityConfig.PASSWORD_BLACKLIST:
            if blocked in v_lower:
                raise ValidationError('password contains blocked terms')
        
        return cls(v)


class Username(SecureString):
    """Validated username."""
    
    @classmethod
    def validate(cls, v):
        v = super().validate(v)
        
        # Length check
        if len(v) < 3:
            raise ValidationError('username too short')
        
        if len(v) > 32:
            raise ValidationError('username too long')
        
        # Pattern check
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValidationError('username contains invalid characters')
        
        # Cannot start with number or special character
        if not v[0].isalpha():
            raise ValidationError('username must start with a letter')
        
        # Blacklist check
        if v.lower() in ['admin', 'root', 'user', 'test', 'guest', 'system']:
            raise ValidationError('username is reserved')
        
        return cls(v)


class Email(SecureString):
    """Validated email address."""
    
    @classmethod
    def validate(cls, v):
        v = super().validate(v)
        
        if not validators.email(v):
            raise ValidationError('invalid email format')
        
        # Additional checks
        if len(v) > 254:
            raise ValidationError('email address too long')
        
        local, domain = v.split('@')
        
        if len(local) > 64:
            raise ValidationError('email local part too long')
        
        return cls(v)
