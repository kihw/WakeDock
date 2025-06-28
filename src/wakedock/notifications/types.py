"""
Notification types and data models for WakeDock notifications.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, validator


class NotificationType(Enum):
    """Types of notifications that can be sent."""
    
    # Service events
    SERVICE_STARTED = "service_started"
    SERVICE_STOPPED = "service_stopped"
    SERVICE_FAILED = "service_failed"
    SERVICE_RESTARTED = "service_restarted"
    SERVICE_CREATED = "service_created"
    SERVICE_DELETED = "service_deleted"
    
    # System events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    SYSTEM_ERROR = "system_error"
    SYSTEM_WARNING = "system_warning"
    
    # Health and monitoring
    HEALTH_CHECK_FAILED = "health_check_failed"
    HEALTH_CHECK_RECOVERED = "health_check_recovered"
    RESOURCE_WARNING = "resource_warning"
    RESOURCE_CRITICAL = "resource_critical"
    
    # Security events
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SECURITY_BREACH = "security_breach"
    
    # Backup and maintenance
    BACKUP_STARTED = "backup_started"
    BACKUP_COMPLETED = "backup_completed"
    BACKUP_FAILED = "backup_failed"
    MAINTENANCE_STARTED = "maintenance_started"
    MAINTENANCE_COMPLETED = "maintenance_completed"
    
    # Custom events
    CUSTOM = "custom"


class NotificationPriority(Enum):
    """Priority levels for notifications."""
    
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class NotificationChannel(Enum):
    """Available notification channels."""
    
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"
    TEAMS = "teams"
    SMS = "sms"
    PUSHOVER = "pushover"


@dataclass
class NotificationMetadata:
    """Additional metadata for notifications."""
    
    service_id: Optional[str] = None
    service_name: Optional[str] = None
    container_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    error_code: Optional[str] = None
    stack_trace: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


class Notification(BaseModel):
    """A notification to be sent through one or more channels."""
    
    id: str = Field(description="Unique notification ID")
    type: NotificationType = Field(description="Type of notification")
    priority: NotificationPriority = Field(default=NotificationPriority.NORMAL)
    title: str = Field(description="Notification title")
    message: str = Field(description="Notification message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Targeting
    channels: List[NotificationChannel] = Field(default_factory=list)
    recipients: List[str] = Field(default_factory=list)
    groups: List[str] = Field(default_factory=list)
    
    # Content
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Optional[NotificationMetadata] = None
    
    # Formatting
    template: Optional[str] = None
    variables: Dict[str, Any] = Field(default_factory=dict)
    
    # Delivery options
    immediate: bool = Field(default=False, description="Send immediately")
    retry_count: int = Field(default=0, description="Number of retry attempts")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    delay_seconds: int = Field(default=0, description="Delay before sending")
    
    # Tracking
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    @validator('channels', pre=True)
    def validate_channels(cls, v):
        """Validate notification channels."""
        if isinstance(v, str):
            return [NotificationChannel(v)]
        elif isinstance(v, list):
            return [NotificationChannel(channel) if isinstance(channel, str) else channel for channel in v]
        return v
    
    @validator('priority', pre=True)
    def validate_priority(cls, v):
        """Validate notification priority."""
        if isinstance(v, str):
            return NotificationPriority(v.lower())
        return v
    
    @validator('type', pre=True)
    def validate_type(cls, v):
        """Validate notification type."""
        if isinstance(v, str):
            return NotificationType(v.lower())
        return v


class NotificationResult(BaseModel):
    """Result of a notification sending attempt."""
    
    notification_id: str
    channel: NotificationChannel
    success: bool
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    response_data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    retry_count: int = 0


class NotificationRule(BaseModel):
    """Rule for when to send notifications."""
    
    id: str
    name: str
    description: Optional[str] = None
    enabled: bool = True
    
    # Conditions
    event_types: List[NotificationType] = Field(default_factory=list)
    priority_levels: List[NotificationPriority] = Field(default_factory=list)
    service_patterns: List[str] = Field(default_factory=list)
    time_conditions: Optional[Dict[str, Any]] = None
    
    # Actions
    channels: List[NotificationChannel] = Field(default_factory=list)
    recipients: List[str] = Field(default_factory=list)
    template: Optional[str] = None
    
    # Throttling
    rate_limit: Optional[int] = None  # Max notifications per hour
    cooldown_minutes: Optional[int] = None  # Minutes between similar notifications
    
    # Filtering
    exclude_services: List[str] = Field(default_factory=list)
    include_services: List[str] = Field(default_factory=list)
    severity_threshold: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class NotificationPreferences(BaseModel):
    """User notification preferences."""
    
    user_id: str
    email_enabled: bool = True
    webhook_enabled: bool = False
    slack_enabled: bool = False
    discord_enabled: bool = False
    
    # Email preferences
    email_address: Optional[str] = None
    email_digest: bool = False
    email_immediate: bool = True
    
    # Webhook preferences
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    
    # Chat preferences
    slack_webhook: Optional[str] = None
    discord_webhook: Optional[str] = None
    
    # Notification types to receive
    enabled_types: List[NotificationType] = Field(default_factory=list)
    disabled_types: List[NotificationType] = Field(default_factory=list)
    
    # Priority filtering
    min_priority: NotificationPriority = NotificationPriority.NORMAL
    
    # Time preferences
    quiet_hours_start: Optional[str] = None  # HH:MM format
    quiet_hours_end: Optional[str] = None    # HH:MM format
    timezone: str = "UTC"
    
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class NotificationQueue(BaseModel):
    """Queued notification for batch processing."""
    
    notification: Notification
    scheduled_at: datetime
    priority_score: int = 0
    attempts: int = 0
    last_attempt: Optional[datetime] = None
    next_attempt: Optional[datetime] = None
    status: str = "pending"  # pending, processing, sent, failed, cancelled


class NotificationStats(BaseModel):
    """Notification delivery statistics."""
    
    total_sent: int = 0
    total_delivered: int = 0
    total_failed: int = 0
    total_pending: int = 0
    
    # By channel
    email_sent: int = 0
    webhook_sent: int = 0
    slack_sent: int = 0
    discord_sent: int = 0
    
    # By priority
    critical_sent: int = 0
    high_sent: int = 0
    normal_sent: int = 0
    low_sent: int = 0
    
    # Response times
    avg_delivery_time: float = 0.0
    max_delivery_time: float = 0.0
    min_delivery_time: float = 0.0
    
    # Error rates
    error_rate: float = 0.0
    retry_rate: float = 0.0
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)
