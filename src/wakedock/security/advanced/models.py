"""
Advanced Security Models

Database models for advanced security features including:
- Security rules and policies
- Security events and logging
- Threat assessment and response
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import ipaddress

from wakedock.database.models.base import Base


class ThreatLevel(str, Enum):
    """Security threat levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityRuleType(str, Enum):
    """Types of security rules"""
    IP_WHITELIST = "ip_whitelist"
    IP_BLACKLIST = "ip_blacklist"
    GEO_BLOCKING = "geo_blocking"
    RATE_LIMITING = "rate_limiting"
    MFA_REQUIRED = "mfa_required"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


class SecurityActionType(str, Enum):
    """Security action types"""
    ALLOW = "allow"
    DENY = "deny"
    LOG = "log"
    ALERT = "alert"
    BLOCK_TEMPORARY = "block_temporary"
    BLOCK_PERMANENT = "block_permanent"
    REQUIRE_MFA = "require_mfa"


class SecurityRule(Base):
    """Security rules and policies"""
    __tablename__ = "security_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    rule_type = Column(SQLEnum(SecurityRuleType), nullable=False, index=True)
    
    # Rule configuration
    config = Column(JSON, default=lambda: {})  # Rule-specific configuration
    
    # Conditions
    conditions = Column(JSON, default=lambda: {
        "ip_ranges": [],
        "countries": [],
        "user_agents": [],
        "request_patterns": [],
        "time_windows": []
    })
    
    # Actions
    action = Column(SQLEnum(SecurityActionType), default=SecurityActionType.DENY, nullable=False)
    action_config = Column(JSON, default=lambda: {
        "block_duration": 3600,  # seconds
        "notification_channels": [],
        "custom_response": None
    })
    
    # Priority and status
    priority = Column(Integer, default=100, nullable=False)  # Lower = higher priority
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Organization context (for multi-tenancy)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    
    # Metadata
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_triggered_at = Column(DateTime, nullable=True)
    trigger_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    organization = relationship("Organization")
    created_by = relationship("User")
    events = relationship("SecurityEvent", back_populates="rule", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SecurityRule(id={self.id}, name='{self.name}', type='{self.rule_type}')>"
    
    def matches_ip(self, ip_address: str) -> bool:
        """Check if IP address matches this rule's conditions"""
        try:
            ip = ipaddress.ip_address(ip_address)
            for ip_range in self.conditions.get("ip_ranges", []):
                if ip in ipaddress.ip_network(ip_range, strict=False):
                    return True
            return False
        except (ipaddress.AddressValueError, ValueError):
            return False
    
    def matches_country(self, country_code: str) -> bool:
        """Check if country code matches this rule's conditions"""
        return country_code.upper() in [c.upper() for c in self.conditions.get("countries", [])]
    
    def is_expired(self) -> bool:
        """Check if temporary rule has expired"""
        if self.action == SecurityActionType.BLOCK_TEMPORARY:
            block_duration = self.action_config.get("block_duration", 3600)
            if self.last_triggered_at:
                return (datetime.utcnow() - self.last_triggered_at).total_seconds() > block_duration
        return False


class SecurityEvent(Base):
    """Security events and incidents"""
    __tablename__ = "security_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    threat_level = Column(SQLEnum(ThreatLevel), default=ThreatLevel.LOW, nullable=False, index=True)
    
    # Event details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    source_ip = Column(String(45), nullable=True, index=True)  # IPv4/IPv6
    user_agent = Column(Text, nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
    
    # Request context
    request_method = Column(String(10), nullable=True)
    request_path = Column(String(500), nullable=True)
    request_headers = Column(JSON, nullable=True)
    request_body_size = Column(Integer, nullable=True)
    
    # Response context
    response_status = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    
    # Security context
    rule_id = Column(Integer, ForeignKey("security_rules.id"), nullable=True, index=True)
    action_taken = Column(SQLEnum(SecurityActionType), nullable=True)
    blocked = Column(Boolean, default=False, nullable=False)
    
    # Organization context
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Additional data
    event_metadata = Column(JSON, default=lambda: {})
    tags = Column(JSON, default=lambda: [])
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Investigation
    is_false_positive = Column(Boolean, default=False, nullable=False)
    investigated_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    investigation_notes = Column(Text, nullable=True)
    
    # Relationships
    rule = relationship("SecurityRule", back_populates="events")
    organization = relationship("Organization")
    user = relationship("User", foreign_keys=[user_id])
    investigated_by = relationship("User", foreign_keys=[investigated_by_user_id])
    
    def __repr__(self):
        return f"<SecurityEvent(id={self.id}, type='{self.event_type}', threat='{self.threat_level}')>"
    
    @property
    def is_resolved(self) -> bool:
        """Check if event has been resolved"""
        return self.resolved_at is not None
    
    def mark_resolved(self, user_id: Optional[int] = None):
        """Mark event as resolved"""
        self.resolved_at = datetime.utcnow()
        if user_id:
            self.investigated_by_user_id = user_id


class IPWhitelist(Base):
    """IP whitelist entries"""
    __tablename__ = "ip_whitelist"
    
    id = Column(Integer, primary_key=True, index=True)
    ip_range = Column(String(50), nullable=False, index=True)  # CIDR notation
    label = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    # Organization context
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    
    # Metadata
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Usage tracking
    last_used_at = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    organization = relationship("Organization")
    created_by = relationship("User")
    
    def __repr__(self):
        return f"<IPWhitelist(id={self.id}, ip_range='{self.ip_range}')>"
    
    def contains_ip(self, ip_address: str) -> bool:
        """Check if IP address is in this whitelist entry"""
        try:
            ip = ipaddress.ip_address(ip_address)
            network = ipaddress.ip_network(self.ip_range, strict=False)
            return ip in network
        except (ipaddress.AddressValueError, ValueError):
            return False
    
    def is_expired(self) -> bool:
        """Check if whitelist entry has expired"""
        return self.expires_at is not None and datetime.utcnow() > self.expires_at


class GeoBlock(Base):
    """Geographic blocking rules"""
    __tablename__ = "geo_blocks"
    
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(2), nullable=False, index=True)  # ISO 3166-1 alpha-2
    country_name = Column(String(100), nullable=True)
    block_type = Column(String(20), default="deny", nullable=False)  # deny, allow, monitor
    
    # Organization context
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    
    # Configuration
    exceptions = Column(JSON, default=lambda: [])  # IP ranges to exclude
    notification_enabled = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Statistics
    block_count = Column(Integer, default=0, nullable=False)
    last_triggered_at = Column(DateTime, nullable=True)
    
    # Relationships
    organization = relationship("Organization")
    created_by = relationship("User")
    
    def __repr__(self):
        return f"<GeoBlock(id={self.id}, country='{self.country_code}', type='{self.block_type}')>"


class MFAMethod(Base):
    """Multi-factor authentication methods"""
    __tablename__ = "mfa_methods"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    method_type = Column(String(50), nullable=False, index=True)  # totp, sms, email, hardware_key, backup_codes
    
    # Method configuration
    config = Column(JSON, default=lambda: {})  # Method-specific config
    backup_codes = Column(JSON, default=lambda: [])  # For backup code method
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)
    
    # Security
    secret_key = Column(String(255), nullable=True)  # Encrypted secret for TOTP
    phone_number = Column(String(20), nullable=True)  # For SMS
    email_address = Column(String(255), nullable=True)  # For email MFA
    
    # Usage tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    use_count = Column(Integer, default=0, nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<MFAMethod(id={self.id}, user_id={self.user_id}, type='{self.method_type}')>"