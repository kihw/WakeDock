"""
Monitoring et audit pour HashiCorp Vault dans WakeDock.

Surveille la santé, les performances et les événements de sécurité
de l'intégration Vault.
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
import statistics

from .client import VaultClient
from .config import VaultConfig

logger = logging.getLogger(__name__)


class AlertLevel(str, Enum):
    """Niveaux d'alerte"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EventType(str, Enum):
    """Types d'événements"""
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    SECRET_ACCESS = "secret_access"
    SECRET_CREATE = "secret_create"
    SECRET_UPDATE = "secret_update"
    SECRET_DELETE = "secret_delete"
    SECRET_ROTATION = "secret_rotation"
    HEALTH_CHECK = "health_check"
    CONNECTION_ERROR = "connection_error"
    PERMISSION_DENIED = "permission_denied"


@dataclass
class VaultEvent:
    """Événement Vault"""
    event_type: EventType
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    user: Optional[str] = None
    path: Optional[str] = None
    source_ip: Optional[str] = None
    alert_level: AlertLevel = AlertLevel.INFO
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir en dictionnaire"""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "user": self.user,
            "path": self.path,
            "source_ip": self.source_ip,
            "alert_level": self.alert_level.value
        }


@dataclass
class HealthMetrics:
    """Métriques de santé Vault"""
    is_healthy: bool
    vault_status: Dict[str, Any]
    response_time: float
    last_check: datetime
    consecutive_failures: int = 0
    uptime_percentage: float = 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir en dictionnaire"""
        return {
            "is_healthy": self.is_healthy,
            "vault_status": self.vault_status,
            "response_time_ms": round(self.response_time * 1000, 2),
            "last_check": self.last_check.isoformat(),
            "consecutive_failures": self.consecutive_failures,
            "uptime_percentage": round(self.uptime_percentage, 2)
        }


@dataclass
class PerformanceMetrics:
    """Métriques de performance"""
    requests_per_second: float = 0.0
    avg_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    success_rate: float = 100.0
    cache_hit_rate: float = 0.0
    active_connections: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir en dictionnaire"""
        return {
            "requests_per_second": round(self.requests_per_second, 2),
            "avg_response_time_ms": round(self.avg_response_time * 1000, 2),
            "p95_response_time_ms": round(self.p95_response_time * 1000, 2),
            "p99_response_time_ms": round(self.p99_response_time * 1000, 2),
            "success_rate": round(self.success_rate, 2),
            "cache_hit_rate": round(self.cache_hit_rate, 2),
            "active_connections": self.active_connections
        }


@dataclass
class SecurityMetrics:
    """Métriques de sécurité"""
    failed_auth_attempts: int = 0
    permission_denials: int = 0
    suspicious_access_patterns: int = 0
    token_renewals: int = 0
    secrets_accessed: int = 0
    secrets_modified: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir en dictionnaire"""
        return {
            "failed_auth_attempts": self.failed_auth_attempts,
            "permission_denials": self.permission_denials,
            "suspicious_access_patterns": self.suspicious_access_patterns,
            "token_renewals": self.token_renewals,
            "secrets_accessed": self.secrets_accessed,
            "secrets_modified": self.secrets_modified
        }


class VaultMonitor:
    """Moniteur principal pour Vault"""
    
    def __init__(self, vault_client: VaultClient, config: VaultConfig):
        self.vault = vault_client
        self.config = config
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        # Stockage des métriques et événements
        self._events: List[VaultEvent] = []
        self._response_times: List[float] = []
        self._health_history: List[HealthMetrics] = []
        
        # Métriques actuelles
        self._health_metrics = HealthMetrics(
            is_healthy=False,
            vault_status={},
            response_time=0.0,
            last_check=datetime.now()
        )
        self._performance_metrics = PerformanceMetrics()
        self._security_metrics = SecurityMetrics()
        
        # Callbacks d'alerte
        self._alert_callbacks: List[Callable] = []
        
        # Configuration du monitoring
        self._max_events = 10000
        self._max_response_times = 1000
        self._max_health_history = 100
        self._health_check_interval = config.settings.health_check_interval
        
        # Seuils d'alerte
        self._alert_thresholds = {
            "response_time": 5.0,  # 5 secondes
            "failure_rate": 10.0,  # 10%
            "consecutive_failures": 3,
            "failed_auth_rate": 5,  # 5 échecs par minute
            "permission_denial_rate": 10  # 10 dénis par minute
        }
    
    async def start_monitoring(self):
        """Démarrer le monitoring"""
        if self._running:
            return
        
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        
        logger.info("Vault monitoring started")
        await self._log_event(EventType.HEALTH_CHECK, {"action": "monitoring_started"})
    
    async def stop_monitoring(self):
        """Arrêter le monitoring"""
        if not self._running:
            return
        
        self._running = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Vault monitoring stopped")
        await self._log_event(EventType.HEALTH_CHECK, {"action": "monitoring_stopped"})
    
    async def _monitor_loop(self):
        """Boucle principale de monitoring"""
        while self._running:
            try:
                # Health check
                await self._perform_health_check()
                
                # Calculer métriques de performance
                await self._calculate_performance_metrics()
                
                # Vérifier les seuils d'alerte
                await self._check_alert_thresholds()
                
                # Nettoyage périodique
                await self._cleanup_old_data()
                
                # Attendre avant prochain cycle
                await asyncio.sleep(self._health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)  # Attendre avant retry
    
    async def _perform_health_check(self):
        """Effectuer un health check"""
        start_time = time.time()
        
        try:
            # Health check Vault
            health_response = await self.vault.health_check()
            response_time = time.time() - start_time
            
            # Enregistrer temps de réponse
            self._response_times.append(response_time)
            if len(self._response_times) > self._max_response_times:
                self._response_times.pop(0)
            
            # Mettre à jour métriques de santé
            is_healthy = health_response.get("healthy", False)
            
            if is_healthy:
                self._health_metrics.consecutive_failures = 0
            else:
                self._health_metrics.consecutive_failures += 1
            
            self._health_metrics.is_healthy = is_healthy
            self._health_metrics.vault_status = health_response.get("vault_status", {})
            self._health_metrics.response_time = response_time
            self._health_metrics.last_check = datetime.now()
            
            # Calculer uptime
            self._calculate_uptime()
            
            # Ajouter à l'historique
            self._health_history.append(self._health_metrics)
            if len(self._health_history) > self._max_health_history:
                self._health_history.pop(0)
            
            # Log événement
            event_type = EventType.HEALTH_CHECK
            alert_level = AlertLevel.INFO if is_healthy else AlertLevel.ERROR
            
            await self._log_event(event_type, {
                "healthy": is_healthy,
                "response_time": response_time,
                "consecutive_failures": self._health_metrics.consecutive_failures
            }, alert_level=alert_level)
            
        except Exception as e:
            response_time = time.time() - start_time
            self._health_metrics.consecutive_failures += 1
            self._health_metrics.is_healthy = False
            self._health_metrics.response_time = response_time
            self._health_metrics.last_check = datetime.now()
            
            await self._log_event(EventType.CONNECTION_ERROR, {
                "error": str(e),
                "response_time": response_time
            }, alert_level=AlertLevel.ERROR)
    
    def _calculate_uptime(self):
        """Calculer le pourcentage d'uptime"""
        if len(self._health_history) < 2:
            return
        
        total_checks = len(self._health_history)
        healthy_checks = sum(1 for h in self._health_history if h.is_healthy)
        
        self._health_metrics.uptime_percentage = (healthy_checks / total_checks) * 100
    
    async def _calculate_performance_metrics(self):
        """Calculer les métriques de performance"""
        # Métriques du client Vault
        client_metrics = self.vault.get_metrics()
        
        # Requests per second (sur dernière minute)
        current_time = datetime.now()
        recent_events = [
            e for e in self._events
            if (current_time - e.timestamp).total_seconds() <= 60
        ]
        self._performance_metrics.requests_per_second = len(recent_events) / 60.0
        
        # Temps de réponse
        if self._response_times:
            self._performance_metrics.avg_response_time = statistics.mean(self._response_times)
            
            if len(self._response_times) >= 20:  # Minimum pour percentiles
                sorted_times = sorted(self._response_times)
                p95_index = int(0.95 * len(sorted_times))
                p99_index = int(0.99 * len(sorted_times))
                
                self._performance_metrics.p95_response_time = sorted_times[p95_index]
                self._performance_metrics.p99_response_time = sorted_times[p99_index]
        
        # Taux de succès
        total_requests = client_metrics.get("requests_total", 0)
        success_requests = client_metrics.get("requests_success", 0)
        
        if total_requests > 0:
            self._performance_metrics.success_rate = (success_requests / total_requests) * 100
        
        # Cache hit rate (si SecretManager est intégré)
        # À implémenter selon l'intégration avec SecretManager
    
    async def _check_alert_thresholds(self):
        """Vérifier les seuils d'alerte"""
        # Vérifier temps de réponse
        if self._performance_metrics.avg_response_time > self._alert_thresholds["response_time"]:
            await self._trigger_alert(
                AlertLevel.WARNING,
                "High Response Time",
                f"Average response time: {self._performance_metrics.avg_response_time:.2f}s"
            )
        
        # Vérifier échecs consécutifs
        if self._health_metrics.consecutive_failures >= self._alert_thresholds["consecutive_failures"]:
            await self._trigger_alert(
                AlertLevel.CRITICAL,
                "Consecutive Health Check Failures",
                f"Failed {self._health_metrics.consecutive_failures} consecutive health checks"
            )
        
        # Vérifier taux de succès
        if self._performance_metrics.success_rate < (100 - self._alert_thresholds["failure_rate"]):
            await self._trigger_alert(
                AlertLevel.ERROR,
                "High Failure Rate",
                f"Success rate: {self._performance_metrics.success_rate:.2f}%"
            )
        
        # Vérifier tentatives d'authentification échouées
        current_time = datetime.now()
        recent_auth_failures = [
            e for e in self._events
            if e.event_type == EventType.AUTH_FAILURE 
            and (current_time - e.timestamp).total_seconds() <= 60
        ]
        
        if len(recent_auth_failures) > self._alert_thresholds["failed_auth_rate"]:
            await self._trigger_alert(
                AlertLevel.WARNING,
                "High Authentication Failure Rate",
                f"{len(recent_auth_failures)} failed auth attempts in last minute"
            )
    
    async def _trigger_alert(self, level: AlertLevel, title: str, message: str):
        """Déclencher une alerte"""
        alert_data = {
            "level": level.value,
            "title": title,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "source": "vault_monitor"
        }
        
        # Log l'alerte
        logger.log(
            logging.WARNING if level == AlertLevel.WARNING else logging.ERROR,
            f"Vault Alert [{level.value.upper()}]: {title} - {message}"
        )
        
        # Appeler callbacks d'alerte
        for callback in self._alert_callbacks:
            try:
                await callback(alert_data)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
        
        # Enregistrer comme événement
        await self._log_event(EventType.HEALTH_CHECK, alert_data, alert_level=level)
    
    async def _cleanup_old_data(self):
        """Nettoyer les anciennes données"""
        # Nettoyer événements anciens (garder 7 jours)
        cutoff_time = datetime.now() - timedelta(days=7)
        self._events = [e for e in self._events if e.timestamp > cutoff_time]
        
        # Limiter nombre d'événements
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events:]
    
    async def _log_event(
        self,
        event_type: EventType,
        details: Dict[str, Any],
        user: Optional[str] = None,
        path: Optional[str] = None,
        source_ip: Optional[str] = None,
        alert_level: AlertLevel = AlertLevel.INFO
    ):
        """Enregistrer un événement"""
        event = VaultEvent(
            event_type=event_type,
            timestamp=datetime.now(),
            details=details,
            user=user,
            path=path,
            source_ip=source_ip,
            alert_level=alert_level
        )
        
        self._events.append(event)
        
        # Mettre à jour métriques de sécurité
        if event_type == EventType.AUTH_FAILURE:
            self._security_metrics.failed_auth_attempts += 1
        elif event_type == EventType.PERMISSION_DENIED:
            self._security_metrics.permission_denials += 1
        elif event_type == EventType.SECRET_ACCESS:
            self._security_metrics.secrets_accessed += 1
        elif event_type in [EventType.SECRET_CREATE, EventType.SECRET_UPDATE, EventType.SECRET_DELETE]:
            self._security_metrics.secrets_modified += 1
        
        # Log si niveau élevé
        if alert_level in [AlertLevel.ERROR, AlertLevel.CRITICAL]:
            logger.log(
                logging.ERROR if alert_level == AlertLevel.ERROR else logging.CRITICAL,
                f"Vault Event [{event_type.value}]: {details}"
            )
    
    # === API publique ===
    
    def add_alert_callback(self, callback: Callable):
        """Ajouter un callback d'alerte"""
        self._alert_callbacks.append(callback)
    
    def remove_alert_callback(self, callback: Callable):
        """Supprimer un callback d'alerte"""
        if callback in self._alert_callbacks:
            self._alert_callbacks.remove(callback)
    
    async def log_secret_access(self, path: str, user: Optional[str] = None, source_ip: Optional[str] = None):
        """Enregistrer l'accès à un secret"""
        await self._log_event(EventType.SECRET_ACCESS, {"path": path}, user=user, path=path, source_ip=source_ip)
    
    async def log_secret_operation(
        self,
        operation: str,
        path: str,
        user: Optional[str] = None,
        source_ip: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Enregistrer une opération sur un secret"""
        event_type_map = {
            "create": EventType.SECRET_CREATE,
            "update": EventType.SECRET_UPDATE,
            "delete": EventType.SECRET_DELETE,
            "rotate": EventType.SECRET_ROTATION
        }
        
        event_type = event_type_map.get(operation, EventType.SECRET_ACCESS)
        event_details = {"operation": operation, "path": path}
        if details:
            event_details.update(details)
        
        await self._log_event(event_type, event_details, user=user, path=path, source_ip=source_ip)
    
    async def log_auth_event(self, success: bool, user: Optional[str] = None, source_ip: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """Enregistrer un événement d'authentification"""
        event_type = EventType.AUTH_SUCCESS if success else EventType.AUTH_FAILURE
        alert_level = AlertLevel.INFO if success else AlertLevel.WARNING
        
        event_details = {"success": success}
        if details:
            event_details.update(details)
        
        await self._log_event(event_type, event_details, user=user, source_ip=source_ip, alert_level=alert_level)
    
    def get_health_metrics(self) -> Dict[str, Any]:
        """Récupérer les métriques de santé"""
        return self._health_metrics.to_dict()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Récupérer les métriques de performance"""
        return self._performance_metrics.to_dict()
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Récupérer les métriques de sécurité"""
        return self._security_metrics.to_dict()
    
    def get_events(
        self,
        event_type: Optional[EventType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Récupérer les événements"""
        events = self._events
        
        # Filtrer par type
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        # Filtrer par période
        if start_time:
            events = [e for e in events if e.timestamp >= start_time]
        if end_time:
            events = [e for e in events if e.timestamp <= end_time]
        
        # Trier par timestamp (plus récent d'abord)
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)
        
        # Limiter résultats
        events = events[:limit]
        
        return [e.to_dict() for e in events]
    
    def get_health_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Récupérer l'historique de santé"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        history = [
            h for h in self._health_history
            if h.last_check >= cutoff_time
        ]
        
        return [h.to_dict() for h in history]
    
    def get_summary_report(self) -> Dict[str, Any]:
        """Générer un rapport de synthèse"""
        # Calculer statistiques sur les événements
        total_events = len(self._events)
        error_events = len([e for e in self._events if e.alert_level in [AlertLevel.ERROR, AlertLevel.CRITICAL]])
        
        # Dernière heure
        last_hour = datetime.now() - timedelta(hours=1)
        recent_events = [e for e in self._events if e.timestamp >= last_hour]
        
        return {
            "summary": {
                "vault_healthy": self._health_metrics.is_healthy,
                "uptime_percentage": self._health_metrics.uptime_percentage,
                "avg_response_time_ms": round(self._performance_metrics.avg_response_time * 1000, 2),
                "success_rate": self._performance_metrics.success_rate
            },
            "activity": {
                "total_events": total_events,
                "error_events": error_events,
                "events_last_hour": len(recent_events),
                "secrets_accessed_last_hour": len([e for e in recent_events if e.event_type == EventType.SECRET_ACCESS])
            },
            "health": self.get_health_metrics(),
            "performance": self.get_performance_metrics(),
            "security": self.get_security_metrics(),
            "generated_at": datetime.now().isoformat()
        }
    
    async def export_metrics_prometheus(self) -> str:
        """Exporter métriques au format Prometheus"""
        metrics = []
        
        # Métriques de santé
        metrics.append(f'vault_healthy {{}} {1 if self._health_metrics.is_healthy else 0}')
        metrics.append(f'vault_uptime_percentage {{}} {self._health_metrics.uptime_percentage}')
        metrics.append(f'vault_response_time_seconds {{}} {self._health_metrics.response_time}')
        metrics.append(f'vault_consecutive_failures {{}} {self._health_metrics.consecutive_failures}')
        
        # Métriques de performance
        metrics.append(f'vault_requests_per_second {{}} {self._performance_metrics.requests_per_second}')
        metrics.append(f'vault_avg_response_time_seconds {{}} {self._performance_metrics.avg_response_time}')
        metrics.append(f'vault_success_rate_percentage {{}} {self._performance_metrics.success_rate}')
        
        # Métriques de sécurité
        metrics.append(f'vault_failed_auth_attempts_total {{}} {self._security_metrics.failed_auth_attempts}')
        metrics.append(f'vault_permission_denials_total {{}} {self._security_metrics.permission_denials}')
        metrics.append(f'vault_secrets_accessed_total {{}} {self._security_metrics.secrets_accessed}')
        metrics.append(f'vault_secrets_modified_total {{}} {self._security_metrics.secrets_modified}')
        
        # Métriques d'événements par type
        event_counts = {}
        for event in self._events:
            event_type = event.event_type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        for event_type, count in event_counts.items():
            metrics.append(f'vault_events_total {{type="{event_type}"}} {count}')
        
        return '\n'.join(metrics)