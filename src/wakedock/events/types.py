"""
Event types and data structures for WakeDock.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
import uuid


class EventType(Enum):
    """Types of events in WakeDock."""
    
    # Service events
    SERVICE_STARTING = "service.starting"
    SERVICE_STARTED = "service.started"
    SERVICE_STOPPING = "service.stopping"
    SERVICE_STOPPED = "service.stopped"
    SERVICE_FAILED = "service.failed"
    SERVICE_HEALTH_CHECK_PASSED = "service.health_check.passed"
    SERVICE_HEALTH_CHECK_FAILED = "service.health_check.failed"
    
    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"
    SYSTEM_HEALTH_CHECK = "system.health_check"
    
    # Resource events
    RESOURCE_HIGH_CPU = "resource.high_cpu"
    RESOURCE_HIGH_MEMORY = "resource.high_memory"
    RESOURCE_HIGH_DISK = "resource.high_disk"
    RESOURCE_LOW_DISK = "resource.low_disk"
    
    # Security events
    AUTH_LOGIN_SUCCESS = "auth.login.success"
    AUTH_LOGIN_FAILED = "auth.login.failed"
    AUTH_LOGOUT = "auth.logout"
    AUTH_TOKEN_EXPIRED = "auth.token.expired"
    
    # Configuration events
    CONFIG_UPDATED = "config.updated"
    CONFIG_VALIDATION_FAILED = "config.validation.failed"
    
    # Plugin events
    PLUGIN_LOADED = "plugin.loaded"
    PLUGIN_UNLOADED = "plugin.unloaded"
    PLUGIN_ERROR = "plugin.error"
    
    # Custom events
    CUSTOM = "custom"


class EventPriority(Enum):
    """Event priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Event:
    """Event data structure."""
    
    event_type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    priority: EventPriority = EventPriority.NORMAL
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "data": self.data,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority.value,
            "correlation_id": self.correlation_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary."""
        return cls(
            event_id=data.get("event_id", str(uuid.uuid4())),
            event_type=EventType(data["event_type"]),
            data=data.get("data", {}),
            source=data.get("source"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now(),
            priority=EventPriority(data.get("priority", EventPriority.NORMAL.value)),
            correlation_id=data.get("correlation_id")
        )


def create_service_event(
    event_type: EventType,
    service_id: str,
    service_name: str,
    additional_data: Optional[Dict[str, Any]] = None
) -> Event:
    """Create a service-related event."""
    data = {
        "service_id": service_id,
        "service_name": service_name
    }
    
    if additional_data:
        data.update(additional_data)
    
    return Event(
        event_type=event_type,
        data=data,
        source=f"service.{service_name}"
    )


def create_system_event(
    event_type: EventType,
    message: str,
    additional_data: Optional[Dict[str, Any]] = None
) -> Event:
    """Create a system-related event."""
    data = {"message": message}
    
    if additional_data:
        data.update(additional_data)
    
    return Event(
        event_type=event_type,
        data=data,
        source="system"
    )


def create_resource_event(
    event_type: EventType,
    resource_type: str,
    current_value: float,
    threshold: float,
    additional_data: Optional[Dict[str, Any]] = None
) -> Event:
    """Create a resource-related event."""
    data = {
        "resource_type": resource_type,
        "current_value": current_value,
        "threshold": threshold
    }
    
    if additional_data:
        data.update(additional_data)
    
    priority = EventPriority.HIGH if current_value > threshold else EventPriority.NORMAL
    
    return Event(
        event_type=event_type,
        data=data,
        source="monitoring",
        priority=priority
    )


def create_auth_event(
    event_type: EventType,
    user_id: str,
    username: str,
    ip_address: Optional[str] = None,
    additional_data: Optional[Dict[str, Any]] = None
) -> Event:
    """Create an authentication-related event."""
    data = {
        "user_id": user_id,
        "username": username
    }
    
    if ip_address:
        data["ip_address"] = ip_address
    
    if additional_data:
        data.update(additional_data)
    
    return Event(
        event_type=event_type,
        data=data,
        source="auth"
    )
