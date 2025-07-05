"""
Pydantic models for request validation.
"""

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, validator, Field

from .config import SecurityConfig
from .exceptions import ValidationError
from .types import (
    ServiceName, DockerImage, PortMapping, VolumeMount, 
    NetworkName, Username, Email, Password
)


class ServiceCreateRequest(BaseModel):
    """Service creation request validation."""
    
    name: ServiceName
    image: DockerImage
    ports: List[PortMapping] = Field(default_factory=list)
    environment: Dict[str, str] = Field(default_factory=dict)
    volumes: List[VolumeMount] = Field(default_factory=list)
    networks: List[NetworkName] = Field(default_factory=list)
    restart_policy: str = Field(default="unless-stopped")
    labels: Dict[str, str] = Field(default_factory=dict)
    
    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment variables."""
        validated = {}
        for key, value in v.items():
            # Validate key
            if not re.match(r'^[A-Z][A-Z0-9_]*$', key):
                raise ValidationError(f'invalid environment variable name: {key}')
            
            if key in SecurityConfig.BLOCKED_ENV_VARS:
                raise ValidationError(f'environment variable {key} is not allowed')
            
            # Validate value
            if len(str(value)) > 1024:
                raise ValidationError(f'environment variable {key} value too long')
            
            validated[key] = str(value)
        
        return validated
    
    @validator('restart_policy')
    def validate_restart_policy(cls, v):
        """Validate restart policy."""
        valid_policies = ['no', 'always', 'unless-stopped', 'on-failure']
        if v not in valid_policies:
            raise ValidationError(f'invalid restart policy: {v}')
        return v
    
    @validator('labels')
    def validate_labels(cls, v):
        """Validate Docker labels."""
        validated = {}
        for key, value in v.items():
            # Basic key validation
            if not re.match(r'^[a-zA-Z0-9._-]+$', key):
                raise ValidationError(f'invalid label key: {key}')
            
            if len(key) > 128:
                raise ValidationError(f'label key too long: {key}')
            
            if len(str(value)) > 1024:
                raise ValidationError(f'label value too long for key: {key}')
            
            validated[key] = str(value)
        
        return validated


class UserCreateRequest(BaseModel):
    """User creation request validation."""
    
    username: Username
    email: Email
    password: Password
    role: str = Field(default="user")
    
    @validator('role')
    def validate_role(cls, v):
        """Validate user role."""
        valid_roles = ['user', 'admin', 'operator', 'viewer']
        if v not in valid_roles:
            raise ValidationError(f'invalid role: {v}')
        return v


class ConfigUpdateRequest(BaseModel):
    """Configuration update request validation."""
    
    caddy: Optional[Dict[str, Any]] = None
    docker: Optional[Dict[str, Any]] = None
    database: Optional[Dict[str, Any]] = None
    security: Optional[Dict[str, Any]] = None
    
    @validator('caddy')
    def validate_caddy_config(cls, v):
        """Validate Caddy configuration."""
        if v is None:
            return v
        
        # Validate admin API endpoint
        if 'admin_api' in v:
            admin_api = v['admin_api']
            if not re.match(r'^[a-zA-Z0-9.-]+:\d+$', admin_api):
                raise ValidationError('invalid Caddy admin API format')
        
        return v
    
    @validator('docker')
    def validate_docker_config(cls, v):
        """Validate Docker configuration."""
        if v is None:
            return v
        
        # Validate socket path
        if 'socket' in v:
            socket_path = v['socket']
            if not socket_path.startswith('/var/run/docker.sock'):
                raise ValidationError('invalid Docker socket path')
        
        return v
