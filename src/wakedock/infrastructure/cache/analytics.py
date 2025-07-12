"""
Advanced Cache Analytics and Monitoring

Real-time cache performance analytics with:
- Cache efficiency analysis and recommendations
- Memory usage optimization insights  
- Access pattern visualization data
- Performance trend analysis
- Automated alerting for cache issues
- ML-based anomaly detection
"""

import asyncio
import logging
import time
import json
import statistics
import math
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class CacheAlert:
    """Cache monitoring alert"""
    id: str
    severity: AlertSeverity
    title: str
    description: str
    timestamp: datetime
    metrics: Dict[str, Any]
    resolved: bool = False
    resolution_time: Optional[datetime] = None


@dataclass
class PerformanceMetric:
    """Performance metric data point"""
    timestamp: float
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class CacheAnalytics:
    """Advanced cache analytics and monitoring"""
    
    def __init__(self, redis_client, cache_manager, performance_optimizer=None):
        self.redis = redis_client
        self.cache_manager = cache_manager
        self.performance_optimizer = performance_optimizer
        
        # Metrics storage
        self.metrics_history = {
            "hit_rate": deque(maxlen=1440),  # 24 hours of minute data
            "memory_usage": deque(maxlen=1440),
            "operations_per_second": deque(maxlen=1440),
            "response_time": deque(maxlen=1440),
            "error_rate": deque(maxlen=1440),
            "cache_size": deque(maxlen=1440),
            "eviction_rate": deque(maxlen=1440)
        }
        
        # Alert management
        self.alerts = {}
        self.alert_thresholds = {
            "hit_rate_critical": 0.5,  # Below 50%
            "hit_rate_warning": 0.7,   # Below 70%
            "memory_usage_critical": 0.9,  # Above 90%
            "memory_usage_warning": 0.8,   # Above 80%
            "error_rate_critical": 0.05,   # Above 5%
            "error_rate_warning": 0.02,    # Above 2%
            "response_time_critical": 1000,  # Above 1000ms
            "response_time_warning": 500    # Above 500ms
        }
        
        # Anomaly detection
        self.anomaly_detector = AnomalyDetector()
        
        # Monitoring state
        self._monitoring_active = False
        self._monitoring_task = None
        self._last_collection = time.time()
    
    async def start_monitoring(self, collection_interval: int = 60):
        """Start real-time monitoring"""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._monitoring_task = asyncio.create_task(
            self._monitoring_loop(collection_interval)
        )
        logger.info(f"Cache analytics monitoring started (interval: {collection_interval}s)")
    
    async def stop_monitoring(self):
        """Stop monitoring"""
        self._monitoring_active = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Cache analytics monitoring stopped")
    
    async def _monitoring_loop(self, interval: int):
        """Main monitoring loop"""
        while self._monitoring_active:
            try:
                await self._collect_metrics()
                await self._analyze_metrics()
                await self._check_alerts()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(30)  # Short retry delay
    
    async def _collect_metrics(self):
        """Collect current cache metrics"""
        timestamp = time.time()
        
        try:
            # Redis metrics
            redis_info = self.redis.info()
            memory_info = self.redis.info('memory')
            stats_info = self.redis.info('stats')
            
            # Calculate derived metrics
            hit_rate = self._calculate_hit_rate(stats_info)
            memory_usage = self._calculate_memory_usage(memory_info)
            ops_per_sec = redis_info.get('instantaneous_ops_per_sec', 0)
            
            # Measure response time
            response_time = await self._measure_response_time()
            
            # Calculate error rate
            error_rate = self._calculate_error_rate()
            
            # Cache size
            cache_size = len(self.redis.keys("*"))  # In production use dbsize()
            
            # Eviction rate
            eviction_rate = self._calculate_eviction_rate(memory_info)
            
            # Store metrics
            self.metrics_history["hit_rate"].append(
                PerformanceMetric(timestamp, hit_rate)
            )
            self.metrics_history["memory_usage"].append(
                PerformanceMetric(timestamp, memory_usage)
            )
            self.metrics_history["operations_per_second"].append(
                PerformanceMetric(timestamp, ops_per_sec)
            )
            self.metrics_history["response_time"].append(
                PerformanceMetric(timestamp, response_time)
            )
            self.metrics_history["error_rate"].append(
                PerformanceMetric(timestamp, error_rate)
            )
            self.metrics_history["cache_size"].append(
                PerformanceMetric(timestamp, cache_size)
            )
            self.metrics_history["eviction_rate"].append(
                PerformanceMetric(timestamp, eviction_rate)
            )
            
            self._last_collection = timestamp
            
        except Exception as e:
            logger.error(f"Metrics collection failed: {e}")
    
    def _calculate_hit_rate(self, stats_info: Dict) -> float:
        """Calculate cache hit rate"""
        hits = stats_info.get('keyspace_hits', 0)
        misses = stats_info.get('keyspace_misses', 0)
        total = hits + misses
        return hits / total if total > 0 else 0.0
    
    def _calculate_memory_usage(self, memory_info: Dict) -> float:
        """Calculate memory usage percentage"""
        used = memory_info.get('used_memory', 0)
        max_memory = memory_info.get('maxmemory', 0)
        if max_memory > 0:
            return used / max_memory
        else:
            # If no max memory set, use system memory as reference
            return min(used / (4 * 1024 * 1024 * 1024), 1.0)  # Assume 4GB max
    
    async def _measure_response_time(self) -> float:
        """Measure cache response time"""
        start = time.time()
        try:
            await self.redis.ping()
            return (time.time() - start) * 1000  # Convert to milliseconds
        except Exception:
            return 9999.0  # High value for errors
    
    def _calculate_error_rate(self) -> float:
        """Calculate error rate (simplified)"""
        # This would need to track actual errors over time
        # For now, return a placeholder
        return 0.0
    
    def _calculate_eviction_rate(self, memory_info: Dict) -> float:
        """Calculate eviction rate"""
        evicted = memory_info.get('evicted_keys', 0)
        # This would need to track evictions over time intervals
        return evicted / 60.0  # Evictions per minute (simplified)
    
    async def _analyze_metrics(self):
        """Analyze collected metrics for trends and anomalies"""
        try:
            # Run anomaly detection on recent metrics
            for metric_name, history in self.metrics_history.items():
                if len(history) >= 10:  # Need minimum data points
                    recent_values = [m.value for m in list(history)[-10:]]
                    anomaly_score = self.anomaly_detector.detect_anomaly(
                        metric_name, recent_values
                    )
                    
                    if anomaly_score > 0.8:  # High anomaly score
                        await self._create_anomaly_alert(metric_name, anomaly_score, recent_values[-1])
        
        except Exception as e:
            logger.error(f"Metrics analysis failed: {e}")
    
    async def _check_alerts(self):
        """Check for alert conditions"""
        try:
            current_metrics = await self._get_current_metrics()
            
            # Check hit rate alerts
            hit_rate = current_metrics.get("hit_rate", 1.0)
            if hit_rate < self.alert_thresholds["hit_rate_critical"]:
                await self._create_alert(
                    "hit_rate_critical",
                    AlertSeverity.CRITICAL,
                    "Critical Cache Hit Rate",
                    f"Cache hit rate is critically low: {hit_rate:.1%}",
                    {"hit_rate": hit_rate}
                )
            elif hit_rate < self.alert_thresholds["hit_rate_warning"]:
                await self._create_alert(
                    "hit_rate_warning", 
                    AlertSeverity.WARNING,
                    "Low Cache Hit Rate",
                    f"Cache hit rate is below optimal: {hit_rate:.1%}",
                    {"hit_rate": hit_rate}
                )
            
            # Check memory usage alerts
            memory_usage = current_metrics.get("memory_usage", 0.0)
            if memory_usage > self.alert_thresholds["memory_usage_critical"]:
                await self._create_alert(
                    "memory_usage_critical",
                    AlertSeverity.CRITICAL,
                    "Critical Memory Usage",
                    f"Cache memory usage is critically high: {memory_usage:.1%}",
                    {"memory_usage": memory_usage}
                )
            elif memory_usage > self.alert_thresholds["memory_usage_warning"]:
                await self._create_alert(
                    "memory_usage_warning",
                    AlertSeverity.WARNING,
                    "High Memory Usage", 
                    f"Cache memory usage is high: {memory_usage:.1%}",
                    {"memory_usage": memory_usage}
                )
            
            # Check response time alerts
            response_time = current_metrics.get("response_time", 0.0)
            if response_time > self.alert_thresholds["response_time_critical"]:
                await self._create_alert(
                    "response_time_critical",
                    AlertSeverity.CRITICAL,
                    "Critical Response Time",
                    f"Cache response time is critically high: {response_time:.1f}ms",
                    {"response_time": response_time}
                )
            elif response_time > self.alert_thresholds["response_time_warning"]:
                await self._create_alert(
                    "response_time_warning",
                    AlertSeverity.WARNING,
                    "High Response Time",
                    f"Cache response time is high: {response_time:.1f}ms", 
                    {"response_time": response_time}
                )
        
        except Exception as e:
            logger.error(f"Alert checking failed: {e}")
    
    async def _create_alert(self, alert_id: str, severity: AlertSeverity, 
                          title: str, description: str, metrics: Dict[str, Any]):
        """Create or update an alert"""
        
        # Check if alert already exists and is unresolved
        if alert_id in self.alerts and not self.alerts[alert_id].resolved:
            # Update existing alert
            self.alerts[alert_id].timestamp = datetime.now()
            self.alerts[alert_id].metrics = metrics
        else:
            # Create new alert
            alert = CacheAlert(
                id=alert_id,
                severity=severity,
                title=title,
                description=description,
                timestamp=datetime.now(),
                metrics=metrics
            )
            self.alerts[alert_id] = alert
            
            logger.warning(f"Cache alert created: {title} - {description}")
    
    async def _create_anomaly_alert(self, metric_name: str, anomaly_score: float, current_value: float):
        """Create alert for detected anomaly"""
        alert_id = f"anomaly_{metric_name}"
        await self._create_alert(
            alert_id,
            AlertSeverity.WARNING,
            f"Anomaly Detected: {metric_name.replace('_', ' ').title()}",
            f"Anomalous behavior detected in {metric_name} (score: {anomaly_score:.2f}, value: {current_value})",
            {"metric": metric_name, "anomaly_score": anomaly_score, "value": current_value}
        )
    
    async def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        if alert_id in self.alerts:
            self.alerts[alert_id].resolved = True
            self.alerts[alert_id].resolution_time = datetime.now()
            logger.info(f"Alert resolved: {alert_id}")
    
    async def _get_current_metrics(self) -> Dict[str, Any]:
        """Get current metric values"""
        current = {}
        for metric_name, history in self.metrics_history.items():
            if history:
                current[metric_name] = history[-1].value
        return current
    
    async def get_performance_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive performance dashboard data"""
        try:
            current_metrics = await self._get_current_metrics()
            trends = await self._calculate_trends()
            recommendations = await self._generate_recommendations()
            
            # Active alerts
            active_alerts = [
                {
                    "id": alert.id,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "description": alert.description,
                    "timestamp": alert.timestamp.isoformat(),
                    "metrics": alert.metrics
                }
                for alert in self.alerts.values() 
                if not alert.resolved
            ]
            
            # Historical data for charts
            chart_data = {}
            for metric_name, history in self.metrics_history.items():
                if len(history) > 0:
                    # Last 24 data points for charts
                    recent_history = list(history)[-24:]
                    chart_data[metric_name] = [
                        {
                            "timestamp": m.timestamp,
                            "value": m.value
                        }
                        for m in recent_history
                    ]
            
            return {
                "current_metrics": current_metrics,
                "trends": trends,
                "recommendations": recommendations,
                "active_alerts": active_alerts,
                "chart_data": chart_data,
                "monitoring_status": {
                    "active": self._monitoring_active,
                    "last_collection": self._last_collection,
                    "data_points": {k: len(v) for k, v in self.metrics_history.items()}
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to generate performance dashboard: {e}")
            return {"error": str(e)}
    
    async def _calculate_trends(self) -> Dict[str, Dict[str, Any]]:
        """Calculate performance trends"""
        trends = {}
        
        for metric_name, history in self.metrics_history.items():
            if len(history) >= 10:
                values = [m.value for m in history]
                
                # Calculate trend direction and magnitude
                recent_avg = statistics.mean(values[-5:]) if len(values) >= 5 else values[-1]
                older_avg = statistics.mean(values[-10:-5]) if len(values) >= 10 else recent_avg
                
                if older_avg != 0:
                    change_percent = ((recent_avg - older_avg) / older_avg) * 100
                else:
                    change_percent = 0
                
                # Determine trend direction
                if abs(change_percent) < 5:
                    direction = "stable"
                elif change_percent > 0:
                    direction = "increasing"
                else:
                    direction = "decreasing"
                
                # Calculate variance for volatility
                variance = statistics.variance(values[-10:]) if len(values) >= 10 else 0
                volatility = "high" if variance > statistics.mean(values) * 0.1 else "low"
                
                trends[metric_name] = {
                    "direction": direction,
                    "change_percent": round(change_percent, 2),
                    "volatility": volatility,
                    "current_value": recent_avg,
                    "variance": variance
                }
        
        return trends
    
    async def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate performance optimization recommendations"""
        recommendations = []
        current_metrics = await self._get_current_metrics()
        
        # Hit rate recommendations
        hit_rate = current_metrics.get("hit_rate", 1.0)
        if hit_rate < 0.8:
            recommendations.append({
                "priority": "high",
                "category": "performance",
                "title": "Improve Cache Hit Rate",
                "description": f"Current hit rate is {hit_rate:.1%}. Consider increasing TTL values or implementing cache warmup strategies.",
                "actions": [
                    "Review and optimize TTL configurations",
                    "Implement predictive prefetching",
                    "Analyze miss patterns for optimization opportunities"
                ]
            })
        
        # Memory usage recommendations
        memory_usage = current_metrics.get("memory_usage", 0.0)
        if memory_usage > 0.8:
            recommendations.append({
                "priority": "high",
                "category": "memory",
                "title": "Optimize Memory Usage",
                "description": f"Memory usage is {memory_usage:.1%}. Consider enabling compression or adjusting eviction policies.",
                "actions": [
                    "Enable compression for large objects",
                    "Review and optimize data structures",
                    "Implement memory-efficient serialization"
                ]
            })
        
        # Response time recommendations
        response_time = current_metrics.get("response_time", 0.0)
        if response_time > 100:
            recommendations.append({
                "priority": "medium",
                "category": "latency",
                "title": "Reduce Response Time",
                "description": f"Average response time is {response_time:.1f}ms. Consider connection pooling optimizations.",
                "actions": [
                    "Optimize Redis connection pooling",
                    "Review network configuration",
                    "Consider Redis clustering for scaling"
                ]
            })
        
        # Cache size recommendations
        cache_size = current_metrics.get("cache_size", 0)
        if cache_size > 100000:
            recommendations.append({
                "priority": "medium",
                "category": "scalability",
                "title": "Optimize Cache Size",
                "description": f"Cache contains {cache_size:,} keys. Consider implementing key namespace management.",
                "actions": [
                    "Implement key expiration policies",
                    "Review and optimize key naming conventions",
                    "Consider cache partitioning strategies"
                ]
            })
        
        return recommendations
    
    async def export_analytics_report(self, format: str = "json", hours: int = 24) -> str:
        """Export analytics report"""
        try:
            # Calculate time range
            end_time = time.time()
            start_time = end_time - (hours * 3600)
            
            # Filter metrics by time range
            filtered_metrics = {}
            for metric_name, history in self.metrics_history.items():
                filtered_history = [
                    m for m in history 
                    if m.timestamp >= start_time
                ]
                if filtered_history:
                    filtered_metrics[metric_name] = {
                        "data_points": len(filtered_history),
                        "min_value": min(m.value for m in filtered_history),
                        "max_value": max(m.value for m in filtered_history),
                        "avg_value": statistics.mean(m.value for m in filtered_history),
                        "latest_value": filtered_history[-1].value
                    }
            
            # Generate report
            report = {
                "report_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "time_range_hours": hours,
                    "start_time": datetime.fromtimestamp(start_time).isoformat(),
                    "end_time": datetime.fromtimestamp(end_time).isoformat()
                },
                "metrics_summary": filtered_metrics,
                "current_alerts": [
                    {
                        "id": alert.id,
                        "severity": alert.severity.value,
                        "title": alert.title,
                        "timestamp": alert.timestamp.isoformat()
                    }
                    for alert in self.alerts.values()
                    if not alert.resolved
                ],
                "recommendations": await self._generate_recommendations()
            }
            
            if format == "json":
                return json.dumps(report, indent=2)
            else:
                # Simple text format
                lines = []
                lines.append(f"Cache Analytics Report - {hours}h period")
                lines.append("=" * 50)
                lines.append(f"Generated: {report['report_metadata']['generated_at']}")
                lines.append("")
                
                lines.append("Metrics Summary:")
                for metric, data in filtered_metrics.items():
                    lines.append(f"  {metric}: avg={data['avg_value']:.2f}, min={data['min_value']:.2f}, max={data['max_value']:.2f}")
                
                lines.append("")
                lines.append(f"Active Alerts: {len(report['current_alerts'])}")
                for alert in report['current_alerts']:
                    lines.append(f"  - {alert['severity'].upper()}: {alert['title']}")
                
                return "\n".join(lines)
        
        except Exception as e:
            logger.error(f"Failed to export analytics report: {e}")
            return json.dumps({"error": str(e)})


class AnomalyDetector:
    """Simple anomaly detection for cache metrics"""
    
    def __init__(self):
        self.baseline_stats = {}
    
    def detect_anomaly(self, metric_name: str, values: List[float]) -> float:
        """Detect anomaly in metric values (returns score 0-1)"""
        if len(values) < 5:
            return 0.0
        
        try:
            # Calculate current baseline
            mean_val = statistics.mean(values)
            std_dev = statistics.stdev(values) if len(values) > 1 else 0
            
            # Update baseline stats
            if metric_name not in self.baseline_stats:
                self.baseline_stats[metric_name] = {
                    "mean": mean_val,
                    "std_dev": std_dev,
                    "samples": len(values)
                }
            else:
                # Exponential moving average
                alpha = 0.1
                baseline = self.baseline_stats[metric_name]
                baseline["mean"] = alpha * mean_val + (1 - alpha) * baseline["mean"]
                baseline["std_dev"] = alpha * std_dev + (1 - alpha) * baseline["std_dev"]
                baseline["samples"] += len(values)
            
            # Check current value against baseline
            current_value = values[-1]
            baseline = self.baseline_stats[metric_name]
            
            if baseline["std_dev"] > 0:
                # Z-score based anomaly detection
                z_score = abs(current_value - baseline["mean"]) / baseline["std_dev"]
                # Convert z-score to 0-1 score (z-score > 3 is very anomalous)
                anomaly_score = min(z_score / 3.0, 1.0)
            else:
                # If no variance, check for significant change
                if baseline["mean"] > 0:
                    change_ratio = abs(current_value - baseline["mean"]) / baseline["mean"]
                    anomaly_score = min(change_ratio, 1.0)
                else:
                    anomaly_score = 0.0
            
            return anomaly_score
        
        except Exception as e:
            logger.error(f"Anomaly detection failed for {metric_name}: {e}")
            return 0.0


# Factory function
def create_cache_analytics(redis_client, cache_manager, performance_optimizer=None) -> CacheAnalytics:
    """Create and configure cache analytics"""
    return CacheAnalytics(redis_client, cache_manager, performance_optimizer)