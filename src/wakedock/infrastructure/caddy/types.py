"""
Caddy Types and Data Classes

Types partagés pour les modules Caddy.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from enum import Enum


class CaddyStatus(Enum):
    """Statuts Caddy disponibles"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class RouteStatus(Enum):
    """Statuts des routes"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


@dataclass
class ConfigValidation:
    """Résultat de validation de configuration"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


@dataclass
class BackupResult:
    """Résultat de backup de configuration"""
    backup_id: str
    backup_path: str
    timestamp: str
    success: bool
    error: Optional[str] = None


@dataclass
class RestoreResult:
    """Résultat de restauration de configuration"""
    success: bool
    backup_id: str
    error: Optional[str] = None


@dataclass
class ReloadResult:
    """Résultat de rechargement Caddy"""
    success: bool
    duration_ms: float
    error: Optional[str] = None


@dataclass
class Route:
    """Représentation d'une route Caddy"""
    id: str
    host: str
    upstream: str
    port: int
    path: str = "/"
    tls: bool = True
    headers: Dict[str, str] = None
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}


@dataclass
class RouteResult:
    """Résultat d'opération sur route"""
    success: bool
    route_id: str
    error: Optional[str] = None


@dataclass
class DomainValidation:
    """Validation de domaine"""
    is_valid: bool
    domain: str
    errors: List[str]
    warnings: List[str]


@dataclass
class CaddyMetrics:
    """Métriques Caddy"""
    active_routes: int
    requests_per_minute: float
    response_time_avg: float
    error_rate: float
    uptime_seconds: float
    memory_usage: float
    cpu_usage: float


@dataclass
class HealthStatus:
    """Statut de santé Caddy"""
    status: CaddyStatus
    version: str
    uptime: float
    active_routes: int
    errors: List[str]
    warnings: List[str]


@dataclass
class DiagnosticReport:
    """Rapport de diagnostic"""
    timestamp: str
    status: CaddyStatus
    checks_passed: int
    checks_total: int
    issues: List[Dict[str, Any]]
    recommendations: List[str]