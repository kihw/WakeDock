"""
Analytics Data Aggregator

Handles data aggregation and pre-computation of analytics metrics:
- Time-series data aggregation
- Statistical calculations
- Trend analysis
- Performance optimization through pre-aggregated data
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import statistics

from .types import (
    MetricPoint, TimeSeriesData, AggregationType, TimeResolution,
    QueryRequest, SystemMetrics, ServiceMetrics
)
from .storage import get_analytics_storage

logger = logging.getLogger(__name__)


class MetricsAggregator:
    """Aggregates metric data at different time resolutions"""
    
    def __init__(self):
        self.storage = get_analytics_storage()
        
    async def aggregate_metrics(self, metric_name: str, start_time: datetime,
                              end_time: datetime, source_resolution: TimeResolution,
                              target_resolution: TimeResolution,
                              aggregation: AggregationType) -> List[MetricPoint]:
        """Aggregate metrics from one resolution to another"""
        
        # Query raw data at source resolution
        request = QueryRequest(
            metric_names=[metric_name],
            start_time=start_time,
            end_time=end_time,
            resolution=source_resolution,
            aggregation=AggregationType.AVG  # Use AVG for raw data
        )
        
        result = await self.storage.query_metrics(request)
        if not result.data:
            return []
            
        points = result.data[0].points
        if not points:
            return []
            
        # Group points by target time buckets
        buckets = self._group_by_time_bucket(points, target_resolution)
        
        # Aggregate each bucket
        aggregated_points = []
        for bucket_time, bucket_points in buckets.items():
            if not bucket_points:
                continue
                
            values = [p.value for p in bucket_points]
            aggregated_value = self._apply_aggregation(values, aggregation)
            
            # Merge labels from all points in bucket
            merged_labels = {}
            for point in bucket_points:
                merged_labels.update(point.labels)
                
            aggregated_point = MetricPoint(
                name=metric_name,
                value=aggregated_value,
                timestamp=bucket_time,
                labels=merged_labels
            )
            aggregated_points.append(aggregated_point)
            
        return sorted(aggregated_points, key=lambda p: p.timestamp)
        
    def _group_by_time_bucket(self, points: List[MetricPoint], 
                             resolution: TimeResolution) -> Dict[datetime, List[MetricPoint]]:
        """Group points into time buckets based on resolution"""
        buckets = defaultdict(list)
        
        for point in points:
            bucket_time = self._get_bucket_start(point.timestamp, resolution)
            buckets[bucket_time].append(point)
            
        return buckets
        
    def _get_bucket_start(self, timestamp: datetime, resolution: TimeResolution) -> datetime:
        """Get the start time of the bucket for a given timestamp"""
        if resolution == TimeResolution.MINUTE:
            return timestamp.replace(second=0, microsecond=0)
        elif resolution == TimeResolution.FIVE_MINUTES:
            minute = (timestamp.minute // 5) * 5
            return timestamp.replace(minute=minute, second=0, microsecond=0)
        elif resolution == TimeResolution.FIFTEEN_MINUTES:
            minute = (timestamp.minute // 15) * 15
            return timestamp.replace(minute=minute, second=0, microsecond=0)
        elif resolution == TimeResolution.HOUR:
            return timestamp.replace(minute=0, second=0, microsecond=0)
        elif resolution == TimeResolution.DAY:
            return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        elif resolution == TimeResolution.WEEK:
            days_since_monday = timestamp.weekday()
            monday = timestamp - timedelta(days=days_since_monday)
            return monday.replace(hour=0, minute=0, second=0, microsecond=0)
        elif resolution == TimeResolution.MONTH:
            return timestamp.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            return timestamp
            
    def _apply_aggregation(self, values: List[float], aggregation: AggregationType) -> float:
        """Apply aggregation function to a list of values"""
        if not values:
            return 0.0
            
        if aggregation == AggregationType.SUM:
            return sum(values)
        elif aggregation == AggregationType.AVG:
            return sum(values) / len(values)
        elif aggregation == AggregationType.MIN:
            return min(values)
        elif aggregation == AggregationType.MAX:
            return max(values)
        elif aggregation == AggregationType.COUNT:
            return float(len(values))
        elif aggregation == AggregationType.MEDIAN:
            return statistics.median(values)
        elif aggregation == AggregationType.P95:
            return self._percentile(values, 0.95)
        elif aggregation == AggregationType.P99:
            return self._percentile(values, 0.99)
        else:
            return sum(values) / len(values)  # Default to average
            
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        if index >= len(sorted_values):
            index = len(sorted_values) - 1
        return sorted_values[index]


class DataAggregator:
    """Main data aggregation service"""
    
    def __init__(self):
        self.metrics_aggregator = MetricsAggregator()
        self.storage = get_analytics_storage()
        self._running = False
        self._aggregation_task = None
        
    async def start_background_aggregation(self):
        """Start background aggregation tasks"""
        if self._running:
            return
            
        self._running = True
        self._aggregation_task = asyncio.create_task(self._aggregation_loop())
        logger.info("Background aggregation started")
        
    async def stop_background_aggregation(self):
        """Stop background aggregation"""
        self._running = False
        if self._aggregation_task:
            self._aggregation_task.cancel()
            try:
                await self._aggregation_task
            except asyncio.CancelledError:
                pass
        logger.info("Background aggregation stopped")
        
    async def _aggregation_loop(self):
        """Background loop for periodic aggregation"""
        while self._running:
            try:
                # Run aggregation every hour
                await self._run_periodic_aggregation()
                await asyncio.sleep(3600)  # 1 hour
                
            except Exception as e:
                logger.error(f"Error in aggregation loop: {e}")
                await asyncio.sleep(300)  # 5 minutes on error
                
    async def _run_periodic_aggregation(self):
        """Run periodic aggregation of metrics"""
        now = datetime.utcnow()
        
        # Aggregate last 24 hours of minute data to hourly
        start_time = now - timedelta(hours=24)
        
        metric_names = [
            "system.cpu.usage",
            "system.memory.usage",
            "system.disk.usage",
            "service.cpu.usage",
            "service.memory.usage",
            "service.requests.count"
        ]
        
        for metric_name in metric_names:
            try:
                await self._aggregate_metric_to_hourly(metric_name, start_time, now)
            except Exception as e:
                logger.error(f"Failed to aggregate {metric_name}: {e}")
                
        # Aggregate last 7 days of hourly data to daily
        start_time = now - timedelta(days=7)
        
        for metric_name in metric_names:
            try:
                await self._aggregate_metric_to_daily(metric_name, start_time, now)
            except Exception as e:
                logger.error(f"Failed to aggregate {metric_name} to daily: {e}")
                
    async def _aggregate_metric_to_hourly(self, metric_name: str, 
                                        start_time: datetime, end_time: datetime):
        """Aggregate minute data to hourly"""
        aggregated_points = await self.metrics_aggregator.aggregate_metrics(
            metric_name=metric_name,
            start_time=start_time,
            end_time=end_time,
            source_resolution=TimeResolution.MINUTE,
            target_resolution=TimeResolution.HOUR,
            aggregation=AggregationType.AVG
        )
        
        if aggregated_points:
            await self.storage.time_series.store_metrics(aggregated_points)
            logger.debug(f"Aggregated {len(aggregated_points)} hourly points for {metric_name}")
            
    async def _aggregate_metric_to_daily(self, metric_name: str,
                                       start_time: datetime, end_time: datetime):
        """Aggregate hourly data to daily"""
        aggregated_points = await self.metrics_aggregator.aggregate_metrics(
            metric_name=metric_name,
            start_time=start_time,
            end_time=end_time,
            source_resolution=TimeResolution.HOUR,
            target_resolution=TimeResolution.DAY,
            aggregation=AggregationType.AVG
        )
        
        if aggregated_points:
            await self.storage.time_series.store_metrics(aggregated_points)
            logger.debug(f"Aggregated {len(aggregated_points)} daily points for {metric_name}")
            
    async def calculate_trend(self, metric_name: str, hours: int = 24) -> Dict[str, Any]:
        """Calculate trend analysis for a metric"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        request = QueryRequest(
            metric_names=[metric_name],
            start_time=start_time,
            end_time=end_time,
            resolution=TimeResolution.HOUR,
            aggregation=AggregationType.AVG
        )
        
        result = await self.storage.query_metrics(request)
        if not result.data or not result.data[0].points:
            return {"trend": "insufficient_data", "change_percent": 0.0}
            
        points = result.data[0].points
        values = [p.value for p in points]
        
        if len(values) < 2:
            return {"trend": "insufficient_data", "change_percent": 0.0}
            
        # Calculate linear trend
        x_values = list(range(len(values)))
        trend_slope = self._calculate_linear_regression_slope(x_values, values)
        
        # Calculate percentage change
        first_value = values[0]
        last_value = values[-1]
        change_percent = ((last_value - first_value) / first_value * 100) if first_value != 0 else 0
        
        # Determine trend direction
        if abs(change_percent) < 1:
            trend = "stable"
        elif change_percent > 0:
            trend = "increasing"
        else:
            trend = "decreasing"
            
        return {
            "trend": trend,
            "change_percent": change_percent,
            "slope": trend_slope,
            "current_value": last_value,
            "min_value": min(values),
            "max_value": max(values),
            "avg_value": sum(values) / len(values)
        }
        
    def _calculate_linear_regression_slope(self, x_values: List[float], 
                                         y_values: List[float]) -> float:
        """Calculate slope of linear regression line"""
        n = len(x_values)
        if n < 2:
            return 0.0
            
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)
        
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return 0.0
            
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope
        
    async def get_service_summary(self, service_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get aggregated summary for a service"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        metric_names = [
            "service.cpu.usage",
            "service.memory.usage",
            "service.requests.count",
            "service.response_time.avg"
        ]
        
        request = QueryRequest(
            metric_names=metric_names,
            start_time=start_time,
            end_time=end_time,
            resolution=TimeResolution.HOUR,
            aggregation=AggregationType.AVG,
            labels={"service_id": service_id}
        )
        
        result = await self.storage.query_metrics(request)
        
        summary = {}
        for ts in result.data:
            if ts.points:
                values = [p.value for p in ts.points]
                summary[ts.metric_name] = {
                    "current": values[-1] if values else 0,
                    "average": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "trend": await self.calculate_trend(ts.metric_name, hours)
                }
        
        return summary
        
    async def get_system_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get aggregated system summary"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        metric_names = [
            "system.cpu.usage",
            "system.memory.usage",
            "system.disk.usage",
            "system.services.active"
        ]
        
        request = QueryRequest(
            metric_names=metric_names,
            start_time=start_time,
            end_time=end_time,
            resolution=TimeResolution.HOUR,
            aggregation=AggregationType.AVG
        )
        
        result = await self.storage.query_metrics(request)
        
        summary = {}
        for ts in result.data:
            if ts.points:
                values = [p.value for p in ts.points]
                summary[ts.metric_name] = {
                    "current": values[-1] if values else 0,
                    "average": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "trend": await self.calculate_trend(ts.metric_name, hours)
                }
        
        return summary


# Global aggregator instance
_data_aggregator: Optional[DataAggregator] = None


def get_data_aggregator() -> Optional[DataAggregator]:
    """Get global data aggregator instance"""
    return _data_aggregator


def init_data_aggregator() -> DataAggregator:
    """Initialize global data aggregator"""
    global _data_aggregator
    _data_aggregator = DataAggregator()
    return _data_aggregator