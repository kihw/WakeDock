"""
Monitoring et métriques pour le système de cache intelligent.

Collecte et expose les métriques de performance du cache pour
optimisation et alerting.
"""

import time
import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


@dataclass
class CacheMetrics:
    """Métriques de performance du cache"""
    hit_rate: float = 0.0
    miss_rate: float = 0.0
    total_requests: int = 0
    avg_response_time: float = 0.0
    p95_response_time: float = 0.0
    cache_size_mb: float = 0.0
    eviction_count: int = 0
    refresh_ahead_hits: int = 0
    compression_saved_mb: float = 0.0
    error_count: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CacheOperation:
    """Enregistrement d'une opération cache"""
    operation_type: str  # get, set, delete, invalidate
    cache_type: str
    key: str
    hit: bool
    response_time_ms: float
    data_size_bytes: int
    timestamp: datetime = field(default_factory=datetime.utcnow)


class CacheMonitor:
    """Monitoring du cache avec métriques temps réel"""
    
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
        
        # Buffer pour métriques temps réel
        self.operations_buffer = deque(maxlen=10000)  # Dernières 10k ops
        self.metrics_history = deque(maxlen=1440)    # 24h si collecte/minute
        
        # Compteurs par type de cache
        self.cache_type_stats = defaultdict(lambda: {
            'hits': 0,
            'misses': 0,
            'total_response_time': 0.0,
            'operations': 0,
            'errors': 0
        })
        
        # Seuils d'alerte
        self.alert_thresholds = {
            'hit_rate_warning': 70.0,      # < 70%
            'hit_rate_critical': 50.0,     # < 50%
            'response_time_warning': 100.0, # > 100ms
            'response_time_critical': 500.0, # > 500ms
            'error_rate_warning': 5.0,     # > 5%
            'error_rate_critical': 10.0    # > 10%
        }
        
        # Tâche de collecte
        self._collection_task = None
        self._is_monitoring = False
    
    async def start_monitoring(self, collection_interval: int = 60):
        """Démarrer monitoring automatique"""
        if self._is_monitoring:
            return
        
        self._is_monitoring = True
        self._collection_task = asyncio.create_task(
            self._collect_metrics_loop(collection_interval)
        )
        logger.info("Cache monitoring started")
    
    async def stop_monitoring(self):
        """Arrêter monitoring"""
        self._is_monitoring = False
        
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Cache monitoring stopped")
    
    async def _collect_metrics_loop(self, interval: int):
        """Boucle de collecte des métriques"""
        while self._is_monitoring:
            try:
                metrics = await self.collect_current_metrics()
                self.metrics_history.append(metrics)
                
                # Vérifier alertes
                await self._check_alerts(metrics)
                
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(interval)
    
    def record_operation(
        self, 
        operation_type: str,
        cache_type: str,
        key: str,
        hit: bool,
        response_time_ms: float,
        data_size_bytes: int = 0,
        error: bool = False
    ):
        """Enregistrer une opération cache"""
        
        operation = CacheOperation(
            operation_type=operation_type,
            cache_type=cache_type,
            key=key,
            hit=hit,
            response_time_ms=response_time_ms,
            data_size_bytes=data_size_bytes
        )
        
        self.operations_buffer.append(operation)
        
        # Mettre à jour stats par type
        stats = self.cache_type_stats[cache_type]
        stats['operations'] += 1
        stats['total_response_time'] += response_time_ms
        
        if hit:
            stats['hits'] += 1
        else:
            stats['misses'] += 1
        
        if error:
            stats['errors'] += 1
    
    async def collect_current_metrics(self) -> CacheMetrics:
        """Collecter métriques actuelles"""
        
        # Stats cache manager
        try:
            # Check if get_global_stats method exists and is async
            if hasattr(self.cache_manager, 'get_global_stats'):
                get_stats_method = getattr(self.cache_manager, 'get_global_stats')
                if asyncio.iscoroutinefunction(get_stats_method):
                    global_stats = await self.cache_manager.get_global_stats()
                else:
                    # If not async, call it directly
                    global_stats = self.cache_manager.get_global_stats()
            else:
                # Fallback to empty stats if method doesn't exist
                global_stats = {}
        except Exception as e:
            logger.error(f"Error getting global stats: {e}")
            # Fallback to empty stats
            global_stats = {}
        
        # Calculer métriques depuis buffer
        metrics = self._calculate_metrics_from_buffer()
        
        # Enrichir avec stats globales
        metrics.total_requests = global_stats.get('total_requests', 0)
        metrics.cache_size_mb = self._parse_memory_size(
            global_stats.get('redis_memory_used', '0B')
        )
        
        return metrics
    
    def _calculate_metrics_from_buffer(self, window_minutes: int = 5) -> CacheMetrics:
        """Calculer métriques depuis le buffer d'opérations"""
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent_ops = [
            op for op in self.operations_buffer 
            if op.timestamp >= cutoff_time
        ]
        
        if not recent_ops:
            return CacheMetrics()
        
        # Calculs de base
        total_ops = len(recent_ops)
        hits = sum(1 for op in recent_ops if op.hit)
        misses = total_ops - hits
        
        hit_rate = (hits / total_ops * 100) if total_ops > 0 else 0
        miss_rate = (misses / total_ops * 100) if total_ops > 0 else 0
        
        # Response times
        response_times = [op.response_time_ms for op in recent_ops]
        avg_response_time = sum(response_times) / len(response_times)
        
        # P95 calculation
        sorted_times = sorted(response_times)
        p95_index = int(0.95 * len(sorted_times))
        p95_response_time = sorted_times[p95_index] if sorted_times else 0
        
        # Refresh ahead hits
        refresh_ahead_hits = sum(
            1 for op in recent_ops 
            if 'refresh_ahead' in op.key
        )
        
        # Compression savings
        compression_saved = sum(
            op.data_size_bytes for op in recent_ops 
            if 'compressed' in op.key
        ) / (1024 * 1024)  # MB
        
        return CacheMetrics(
            hit_rate=round(hit_rate, 2),
            miss_rate=round(miss_rate, 2),
            total_requests=total_ops,
            avg_response_time=round(avg_response_time, 2),
            p95_response_time=round(p95_response_time, 2),
            refresh_ahead_hits=refresh_ahead_hits,
            compression_saved_mb=round(compression_saved, 2)
        )
    
    async def get_cache_type_breakdown(self) -> Dict[str, Dict]:
        """Breakdown des métriques par type de cache"""
        
        breakdown = {}
        
        for cache_type, stats in self.cache_type_stats.items():
            total_ops = stats['operations']
            if total_ops == 0:
                continue
            
            hit_rate = (stats['hits'] / total_ops * 100)
            avg_response_time = stats['total_response_time'] / total_ops
            error_rate = (stats['errors'] / total_ops * 100)
            
            breakdown[cache_type] = {
                'hit_rate': round(hit_rate, 2),
                'avg_response_time': round(avg_response_time, 2),
                'error_rate': round(error_rate, 2),
                'total_operations': total_ops,
                'hits': stats['hits'],
                'misses': stats['misses'],
                'errors': stats['errors']
            }
        
        return breakdown
    
    async def get_trend_analysis(self, hours: int = 24) -> Dict[str, Any]:
        """Analyse des tendances sur période"""
        
        if len(self.metrics_history) < 2:
            return {"status": "insufficient_data"}
        
        # Prendre métriques des dernières heures
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self.metrics_history 
            if m.timestamp >= cutoff_time
        ]
        
        if len(recent_metrics) < 2:
            return {"status": "insufficient_data"}
        
        # Calculer tendances
        hit_rates = [m.hit_rate for m in recent_metrics]
        response_times = [m.avg_response_time for m in recent_metrics]
        
        hit_rate_trend = self._calculate_trend(hit_rates)
        response_time_trend = self._calculate_trend(response_times)
        
        # Performance actuelle vs historique
        current = recent_metrics[-1]
        historical_avg_hit_rate = sum(hit_rates[:-1]) / len(hit_rates[:-1])
        historical_avg_response_time = sum(response_times[:-1]) / len(response_times[:-1])
        
        return {
            "status": "ok",
            "period_hours": hours,
            "current_performance": {
                "hit_rate": current.hit_rate,
                "avg_response_time": current.avg_response_time
            },
            "historical_average": {
                "hit_rate": round(historical_avg_hit_rate, 2),
                "avg_response_time": round(historical_avg_response_time, 2)
            },
            "trends": {
                "hit_rate": hit_rate_trend,
                "response_time": response_time_trend
            },
            "recommendations": self._generate_recommendations(current, recent_metrics)
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculer tendance (improving, stable, degrading)"""
        if len(values) < 3:
            return "stable"
        
        # Simple linear trend
        recent_avg = sum(values[-3:]) / 3
        older_avg = sum(values[:-3]) / len(values[:-3]) if len(values) > 3 else recent_avg
        
        diff_percent = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0
        
        if diff_percent > 5:
            return "improving"
        elif diff_percent < -5:
            return "degrading"
        else:
            return "stable"
    
    def _generate_recommendations(
        self, 
        current: CacheMetrics, 
        history: List[CacheMetrics]
    ) -> List[str]:
        """Générer recommandations d'optimisation"""
        
        recommendations = []
        
        if current.hit_rate < 70:
            recommendations.append(
                f"Hit rate is low ({current.hit_rate}%). Consider increasing TTL or cache size."
            )
        
        if current.avg_response_time > 100:
            recommendations.append(
                f"Average response time is high ({current.avg_response_time}ms). "
                "Check cache backend performance."
            )
        
        if current.cache_size_mb > 200:
            recommendations.append(
                f"Cache size is large ({current.cache_size_mb}MB). "
                "Consider implementing LRU eviction or reducing TTL."
            )
        
        # Tendance dégradation
        if len(history) >= 5:
            recent_hit_rates = [m.hit_rate for m in history[-5:]]
            if all(recent_hit_rates[i] > recent_hit_rates[i+1] for i in range(len(recent_hit_rates)-1)):
                recommendations.append(
                    "Hit rate is consistently decreasing. Review cache strategy."
                )
        
        return recommendations
    
    async def _check_alerts(self, metrics: CacheMetrics):
        """Vérifier seuils d'alerte"""
        
        alerts = []
        
        # Hit rate alerts
        if metrics.hit_rate < self.alert_thresholds['hit_rate_critical']:
            alerts.append({
                "level": "critical",
                "metric": "hit_rate",
                "value": metrics.hit_rate,
                "threshold": self.alert_thresholds['hit_rate_critical'],
                "message": f"Cache hit rate critically low: {metrics.hit_rate}%"
            })
        elif metrics.hit_rate < self.alert_thresholds['hit_rate_warning']:
            alerts.append({
                "level": "warning", 
                "metric": "hit_rate",
                "value": metrics.hit_rate,
                "threshold": self.alert_thresholds['hit_rate_warning'],
                "message": f"Cache hit rate low: {metrics.hit_rate}%"
            })
        
        # Response time alerts
        if metrics.avg_response_time > self.alert_thresholds['response_time_critical']:
            alerts.append({
                "level": "critical",
                "metric": "response_time",
                "value": metrics.avg_response_time,
                "threshold": self.alert_thresholds['response_time_critical'],
                "message": f"Cache response time critically high: {metrics.avg_response_time}ms"
            })
        elif metrics.avg_response_time > self.alert_thresholds['response_time_warning']:
            alerts.append({
                "level": "warning",
                "metric": "response_time", 
                "value": metrics.avg_response_time,
                "threshold": self.alert_thresholds['response_time_warning'],
                "message": f"Cache response time high: {metrics.avg_response_time}ms"
            })
        
        # Notifier alertes si configuré
        if alerts:
            await self._send_alerts(alerts)
    
    async def _send_alerts(self, alerts: List[Dict]):
        """Envoyer alertes (à intégrer avec système de notification)"""
        for alert in alerts:
            logger.warning(f"Cache Alert [{alert['level']}]: {alert['message']}")
            # TODO: Intégrer avec système de notification WakeDock
    
    def _parse_memory_size(self, size_str: str) -> float:
        """Parser taille mémoire Redis (format: 1.5MB)"""
        try:
            if 'MB' in size_str:
                return float(size_str.replace('MB', ''))
            elif 'KB' in size_str:
                return float(size_str.replace('KB', '')) / 1024
            elif 'GB' in size_str:
                return float(size_str.replace('GB', '')) * 1024
            else:
                return 0.0
        except:
            return 0.0
    
    async def export_metrics(self, format: str = "prometheus") -> str:
        """Exporter métriques dans format standard"""
        
        current_metrics = await self.collect_current_metrics()
        cache_breakdown = await self.get_cache_type_breakdown()
        
        if format == "prometheus":
            return self._format_prometheus_metrics(current_metrics, cache_breakdown)
        elif format == "json":
            import json
            return json.dumps({
                "current_metrics": current_metrics.__dict__,
                "cache_breakdown": cache_breakdown,
                "timestamp": datetime.utcnow().isoformat()
            }, default=str, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _format_prometheus_metrics(
        self, 
        metrics: CacheMetrics, 
        breakdown: Dict[str, Dict]
    ) -> str:
        """Formater métriques pour Prometheus"""
        
        lines = [
            "# HELP wakedock_cache_hit_rate Cache hit rate percentage",
            "# TYPE wakedock_cache_hit_rate gauge",
            f"wakedock_cache_hit_rate {metrics.hit_rate}",
            "",
            "# HELP wakedock_cache_response_time_avg Average response time in milliseconds",
            "# TYPE wakedock_cache_response_time_avg gauge", 
            f"wakedock_cache_response_time_avg {metrics.avg_response_time}",
            "",
            "# HELP wakedock_cache_response_time_p95 95th percentile response time in milliseconds",
            "# TYPE wakedock_cache_response_time_p95 gauge",
            f"wakedock_cache_response_time_p95 {metrics.p95_response_time}",
            "",
            "# HELP wakedock_cache_total_requests Total cache requests",
            "# TYPE wakedock_cache_total_requests counter",
            f"wakedock_cache_total_requests {metrics.total_requests}",
            ""
        ]
        
        # Métriques par type de cache
        for cache_type, stats in breakdown.items():
            lines.extend([
                f"# Cache type: {cache_type}",
                f"wakedock_cache_hit_rate{{cache_type=\"{cache_type}\"}} {stats['hit_rate']}",
                f"wakedock_cache_operations_total{{cache_type=\"{cache_type}\"}} {stats['total_operations']}",
                f"wakedock_cache_errors_total{{cache_type=\"{cache_type}\"}} {stats['errors']}",
                ""
            ])
        
        return "\n".join(lines)