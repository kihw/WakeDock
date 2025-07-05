"""
WebSocket Types and Models

Types partagés pour les modules WebSocket.
"""

from datetime import datetime
from typing import Dict, List, Set, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field

class EventType(Enum):
    """Types d'événements WebSocket"""
    # System events
    SYSTEM_METRICS = "system:metrics"
    SYSTEM_STATUS = "system:status"
    
    # Service events
    SERVICE_CREATED = "service:created"
    SERVICE_UPDATED = "service:updated"
    SERVICE_DELETED = "service:deleted"
    SERVICE_STARTED = "service:started"
    SERVICE_STOPPED = "service:stopped"
    SERVICE_LOGS = "service:logs"
    SERVICE_METRICS = "service:metrics"
    
    # Docker events
    DOCKER_EVENT = "docker:event"
    DOCKER_CONTAINER_START = "docker:container:start"
    DOCKER_CONTAINER_STOP = "docker:container:stop"
    DOCKER_CONTAINER_DIE = "docker:container:die"
    DOCKER_IMAGE_PULL = "docker:image:pull"
    
    # Authentication events
    AUTH_LOGIN = "auth:login"
    AUTH_LOGOUT = "auth:logout"
    AUTH_SESSION_EXPIRED = "auth:session_expired"
    
    # Notification events
    NOTIFICATION = "notification"
    ALERT = "alert"
    
    # General events
    PING = "ping"
    PONG = "pong"
    ERROR = "error"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"


class ConnectionStatus(Enum):
    """Statuts de connexion WebSocket"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class WebSocketMessage(BaseModel):
    """Message WebSocket standardisé"""
    type: str = Field(..., description="Message type")
    data: Any = Field(..., description="Message data")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    sequence: Optional[int] = Field(default=None, description="Message sequence number")
    source: Optional[str] = Field(default="wakedock", description="Message source")


class SubscriptionRequest(BaseModel):
    """Requête d'abonnement à des événements"""
    event_type: str = Field(..., description="Event type to subscribe to")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Event filters")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Subscription options")


class WebSocketError(BaseModel):
    """Erreur WebSocket"""
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Error details")


class ConnectionInfo(BaseModel):
    """Informations de connexion WebSocket"""
    connection_id: str
    user_id: Optional[int]
    username: Optional[str] = None
    connected_at: datetime
    last_activity: datetime
    subscriptions: Set[str] = Field(default_factory=set)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: ConnectionStatus = ConnectionStatus.CONNECTED


class ServiceEvent(BaseModel):
    """Événement de service"""
    service_id: str
    service_name: str
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SystemMetrics(BaseModel):
    """Métriques système"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    active_containers: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class LogEntry(BaseModel):
    """Entrée de log"""
    service_id: str
    level: str
    message: str
    timestamp: datetime
    source: str = "container"


class NotificationMessage(BaseModel):
    """Message de notification"""
    id: str
    title: str
    message: str
    level: str = "info"  # info, warning, error, success
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[int] = None
    data: Optional[Dict[str, Any]] = None


class AuthEvent(BaseModel):
    """Événement d'authentification"""
    user_id: int
    username: str
    event_type: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Type unions pour les différents types de données
MessageData = Union[
    ServiceEvent,
    SystemMetrics,
    LogEntry,
    NotificationMessage,
    AuthEvent,
    Dict[str, Any]
]