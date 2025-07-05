"""
Security Configuration Management

Centralized security configuration with:
- Password policies
- Rate limiting settings
- Session management
- Audit settings
- Security feature toggles
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator
from enum import Enum
import re


class PasswordPolicy(BaseModel):
    """Password policy configuration"""
    min_length: int = Field(8, ge=4, le=64)
    max_length: int = Field(128, ge=8, le=256)
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digits: bool = True
    require_special_chars: bool = True
    special_chars: str = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # Password history and reuse
    prevent_reuse_count: int = Field(5, ge=0, le=24)
    
    # Expiration
    expire_days: int = Field(90, ge=0, le=365)
    warn_days_before_expiry: int = Field(7, ge=1, le=30)
    
    @validator('max_length')
    def max_length_greater_than_min(cls, v, values):
        if 'min_length' in values and v < values['min_length']:
            raise ValueError('max_length must be greater than min_length')
        return v
    
    def validate_password(self, password: str) -> tuple[bool, list[str]]:
        """Validate password against policy"""
        errors = []
        
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters long")
        
        if len(password) > self.max_length:
            errors.append(f"Password must be no more than {self.max_length} characters long")
        
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if self.require_digits and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        if self.require_special_chars and not re.search(f'[{re.escape(self.special_chars)}]', password):
            errors.append(f"Password must contain at least one special character: {self.special_chars}")
        
        return len(errors) == 0, errors


class RateLimitConfig(BaseModel):
    """Rate limiting configuration"""
    enabled: bool = True
    
    # Global rate limits
    requests_per_minute: int = Field(100, ge=1, le=10000)
    requests_per_hour: int = Field(1000, ge=1, le=100000)
    
    # Authentication rate limits
    login_attempts_per_minute: int = Field(5, ge=1, le=100)
    login_attempts_per_hour: int = Field(20, ge=1, le=1000)
    lockout_duration_minutes: int = Field(15, ge=1, le=1440)
    
    # API endpoint specific limits
    heavy_endpoint_per_minute: int = Field(10, ge=1, le=100)
    
    # IP-based blocking
    block_suspicious_ips: bool = True
    max_violations_before_block: int = Field(5, ge=1, le=50)
    ip_block_duration_hours: int = Field(24, ge=1, le=168)


class SessionConfig(BaseModel):
    """Session management configuration"""
    # JWT settings
    access_token_expire_minutes: int = Field(30, ge=5, le=1440)
    refresh_token_expire_days: int = Field(7, ge=1, le=90)
    
    # Session security
    require_secure_cookies: bool = True
    enable_session_rotation: bool = True
    max_concurrent_sessions: int = Field(5, ge=1, le=50)
    
    # Idle timeout
    idle_timeout_minutes: int = Field(60, ge=5, le=480)
    warn_before_timeout_minutes: int = Field(5, ge=1, le=30)
    
    # Remember me functionality
    allow_remember_me: bool = True
    remember_me_duration_days: int = Field(30, ge=1, le=365)


class AuditConfig(BaseModel):
    """Audit logging configuration"""
    enabled: bool = True
    
    # What to log
    log_successful_logins: bool = True
    log_failed_logins: bool = True
    log_user_management: bool = True
    log_service_operations: bool = True
    log_config_changes: bool = True
    log_api_requests: bool = False  # Can be very verbose
    log_security_events: bool = True
    
    # Retention settings
    retention_days: int = Field(365, ge=30, le=2555)  # ~7 years max
    auto_cleanup_enabled: bool = True
    
    # Export settings
    allow_export: bool = True
    max_export_records: int = Field(50000, ge=1000, le=1000000)
    
    # Real-time alerting
    enable_security_alerts: bool = True
    alert_on_multiple_failures: bool = True
    alert_threshold_failures: int = Field(5, ge=3, le=50)


class EncryptionConfig(BaseModel):
    """Encryption and cryptography settings"""
    # Algorithm preferences
    password_hash_algorithm: str = "bcrypt"
    jwt_algorithm: str = "HS256"
    
    # Key settings
    jwt_secret_key_length: int = Field(32, ge=16, le=64)
    auto_rotate_keys: bool = False
    key_rotation_days: int = Field(90, ge=30, le=365)
    
    # Database encryption
    encrypt_sensitive_fields: bool = True
    database_encryption_key_length: int = Field(32, ge=16, le=64)


class SecurityFeatures(BaseModel):
    """Security feature toggles"""
    # Multi-factor authentication
    enable_mfa: bool = False
    require_mfa_for_admin: bool = True
    mfa_methods: List[str] = ["totp", "email"]
    
    # Account security
    enable_account_lockout: bool = True
    enable_password_expiry: bool = True
    require_email_verification: bool = True
    
    # API security
    enable_api_rate_limiting: bool = True
    require_api_keys: bool = False
    enable_cors_protection: bool = True
    
    # Monitoring
    enable_intrusion_detection: bool = True
    enable_anomaly_detection: bool = False
    
    # Headers and protections
    enable_security_headers: bool = True
    enable_csrf_protection: bool = True
    enable_content_security_policy: bool = True


class SecurityConfig(BaseModel):
    """Complete security configuration"""
    password_policy: PasswordPolicy = PasswordPolicy()
    rate_limiting: RateLimitConfig = RateLimitConfig()
    session: SessionConfig = SessionConfig()
    audit: AuditConfig = AuditConfig()
    encryption: EncryptionConfig = EncryptionConfig()
    features: SecurityFeatures = SecurityFeatures()
    
    # Environment-specific settings
    environment: str = Field("production", regex="^(development|testing|staging|production)$")
    debug_mode: bool = False
    
    @validator('debug_mode')
    def debug_only_in_dev(cls, v, values):
        if v and values.get('environment') == 'production':
            raise ValueError('Debug mode cannot be enabled in production')
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return self.dict()
    
    def get_environment_overrides(self) -> Dict[str, Any]:
        """Get environment-specific configuration overrides"""
        if self.environment == "development":
            return {
                "password_policy": {"min_length": 4, "require_special_chars": False},
                "rate_limiting": {"requests_per_minute": 1000},
                "session": {"access_token_expire_minutes": 1440},
                "audit": {"log_api_requests": True}
            }
        elif self.environment == "testing":
            return {
                "password_policy": {"min_length": 4},
                "rate_limiting": {"requests_per_minute": 10000},
                "session": {"access_token_expire_minutes": 60},
                "audit": {"retention_days": 30}
            }
        else:
            return {}


class SecurityConfigManager:
    """Manager for security configuration"""
    
    def __init__(self):
        self._config = SecurityConfig()
        self._loaded_from_env = False
    
    def load_config(self, config_dict: Optional[Dict[str, Any]] = None) -> SecurityConfig:
        """Load configuration from dictionary or environment"""
        if config_dict:
            self._config = SecurityConfig(**config_dict)
        else:
            # Load from environment variables or defaults
            self._config = SecurityConfig()
        
        # Apply environment-specific overrides
        overrides = self._config.get_environment_overrides()
        if overrides:
            config_dict = self._config.dict()
            for section, values in overrides.items():
                if section in config_dict:
                    config_dict[section].update(values)
            self._config = SecurityConfig(**config_dict)
        
        self._loaded_from_env = True
        return self._config
    
    def get_config(self) -> SecurityConfig:
        """Get current security configuration"""
        if not self._loaded_from_env:
            self.load_config()
        return self._config
    
    def update_config(self, updates: Dict[str, Any]) -> SecurityConfig:
        """Update configuration with new values"""
        current_dict = self._config.dict()
        
        # Deep merge updates
        def deep_update(base_dict, update_dict):
            for key, value in update_dict.items():
                if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                    deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value
        
        deep_update(current_dict, updates)
        self._config = SecurityConfig(**current_dict)
        return self._config
    
    def validate_config(self) -> tuple[bool, List[str]]:
        """Validate current configuration"""
        errors = []
        
        # Check password policy consistency
        policy = self._config.password_policy
        if policy.warn_days_before_expiry >= policy.expire_days:
            errors.append("Password expiry warning days must be less than expiry days")
        
        # Check session configuration
        session = self._config.session
        if session.warn_before_timeout_minutes >= session.idle_timeout_minutes:
            errors.append("Session timeout warning must be less than idle timeout")
        
        # Check rate limiting
        rate_limit = self._config.rate_limiting
        if rate_limit.requests_per_hour < rate_limit.requests_per_minute * 60:
            errors.append("Hourly rate limit should be at least 60x the per-minute limit")
        
        return len(errors) == 0, errors
    
    def get_feature_flags(self) -> Dict[str, bool]:
        """Get all security feature flags"""
        features = self._config.features
        return {
            "mfa_enabled": features.enable_mfa,
            "mfa_required_for_admin": features.require_mfa_for_admin,
            "account_lockout": features.enable_account_lockout,
            "password_expiry": features.enable_password_expiry,
            "email_verification": features.require_email_verification,
            "api_rate_limiting": features.enable_api_rate_limiting,
            "cors_protection": features.enable_cors_protection,
            "intrusion_detection": features.enable_intrusion_detection,
            "security_headers": features.enable_security_headers,
            "csrf_protection": features.enable_csrf_protection,
            "content_security_policy": features.enable_content_security_policy
        }


# Global security configuration manager
_security_config_manager: Optional[SecurityConfigManager] = None


def get_security_config_manager() -> SecurityConfigManager:
    """Get global security configuration manager"""
    global _security_config_manager
    if _security_config_manager is None:
        _security_config_manager = SecurityConfigManager()
    return _security_config_manager


def get_security_config() -> SecurityConfig:
    """Get current security configuration"""
    return get_security_config_manager().get_config()