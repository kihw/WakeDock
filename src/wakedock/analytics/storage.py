"""
Analytics Data Storage

Handles storage and retrieval of analytics data using various backends:
- PostgreSQL for structured data
- Time-series optimized storage
- Efficient querying and aggregation
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from contextlib import asynccontextmanager

import asyncpg
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from .types import (
    AnalyticsEvent, MetricPoint, TimeSeriesData, QueryRequest, QueryResult,
    SystemMetrics, ServiceMetrics, AggregationType, TimeResolution
)
from ..database import get_db_session, get_async_db_session_context
from ..database.database import DatabaseManager, get_db_manager
from ..config import get_settings

logger = logging.getLogger(__name__)


class TimeSeriesStorage:
    """Time-series data storage with PostgreSQL"""
    
    def __init__(self, engine):
        self.engine = engine
        self._initialized = False
        
    async def initialize(self):
        """Initialize storage schema"""
        if self._initialized:
            return
            
        try:
            async with self.engine.begin() as conn:
                # Create time-series tables
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS analytics_metrics (
                        id SERIAL PRIMARY KEY,
                        metric_name VARCHAR(255) NOT NULL,
                        metric_type VARCHAR(50) NOT NULL,
                        value DOUBLE PRECISION NOT NULL,
                        timestamp TIMESTAMPTZ NOT NULL,
                        labels JSONB DEFAULT '{}',
                        source VARCHAR(255),
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """))
                
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS analytics_events (
                        id SERIAL PRIMARY KEY,
                        event_id VARCHAR(255) UNIQUE NOT NULL,
                        event_type VARCHAR(255) NOT NULL,
                        source VARCHAR(255) NOT NULL,
                        timestamp TIMESTAMPTZ NOT NULL,
                        data JSONB DEFAULT '{}',
                        labels JSONB DEFAULT '{}',
                        user_id VARCHAR(255),
                        session_id VARCHAR(255),
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """))
                
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS analytics_aggregates (
                        id SERIAL PRIMARY KEY,
                        metric_name VARCHAR(255) NOT NULL,
                        aggregation_type VARCHAR(50) NOT NULL,
                        resolution VARCHAR(10) NOT NULL,
                        time_bucket TIMESTAMPTZ NOT NULL,
                        value DOUBLE PRECISION NOT NULL,
                        sample_count INTEGER DEFAULT 1,
                        labels JSONB DEFAULT '{}',
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        UNIQUE(metric_name, aggregation_type, resolution, time_bucket, labels)
                    );
                """))
                
                # Create indexes for performance
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_metrics_name_time 
                    ON analytics_metrics(metric_name, timestamp DESC);
                """))
                
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_metrics_labels 
                    ON analytics_metrics USING GIN(labels);
                """))
                
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_events_type_time 
                    ON analytics_events(event_type, timestamp DESC);
                """))
                
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_events_user 
                    ON analytics_events(user_id, timestamp DESC);
                """))
                
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_aggregates_lookup 
                    ON analytics_aggregates(metric_name, resolution, time_bucket DESC);
                """))
                
            self._initialized = True
            logger.info("Analytics storage initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize analytics storage: {e}")
            raise
            
    async def store_metrics(self, metrics: List[MetricPoint]):
        """Store metric points"""
        if not metrics:
            return
            
        try:
            async with self.engine.begin() as conn:
                for metric in metrics:
                    await conn.execute(text("""
                        INSERT INTO analytics_metrics 
                        (metric_name, metric_type, value, timestamp, labels, source)
                        VALUES (:metric_name, :metric_type, :value, :timestamp, :labels, :source)
                    """), {
                        "metric_name": metric.name,
                        "metric_type": metric.metric_type.value,
                        "value": metric.value,
                        "timestamp": metric.timestamp,
                        "labels": json.dumps(metric.labels),
                        "source": metric.labels.get("source", "unknown")
                    })
                    
        except Exception as e:
            logger.error(f"Failed to store metrics: {e}")
            raise
            
    async def store_events(self, events: List[AnalyticsEvent]):
        """Store analytics events"""
        if not events:
            return
            
        try:
            async with self.engine.begin() as conn:
                for event in events:
                    await conn.execute(text("""
                        INSERT INTO analytics_events 
                        (event_id, event_type, source, timestamp, data, labels, user_id, session_id)
                        VALUES (:event_id, :event_type, :source, :timestamp, :data, :labels, :user_id, :session_id)
                        ON CONFLICT (event_id) DO NOTHING
                    """), {
                        "event_id": event.event_id,
                        "event_type": event.event_type,
                        "source": event.source,
                        "timestamp": event.timestamp,
                        "data": json.dumps(event.data),
                        "labels": json.dumps(event.labels),
                        "user_id": event.user_id,
                        "session_id": event.session_id
                    })
                    
        except Exception as e:
            logger.error(f"Failed to store events: {e}")
            raise
            
    async def query_metrics(self, request: QueryRequest) -> QueryResult:
        """Query metrics with aggregation"""
        start_time = datetime.now()
        
        try:
            # Build query
            conditions = ["timestamp BETWEEN :start_time AND :end_time"]
            params = {
                "start_time": request.start_time,
                "end_time": request.end_time
            }
            
            if request.metric_names:
                conditions.append("metric_name = ANY(:metric_names)")
                params["metric_names"] = request.metric_names
                
            if request.labels:
                for key, value in request.labels.items():
                    conditions.append(f"labels->:label_key_{key} = :label_value_{key}")
                    params[f"label_key_{key}"] = key
                    params[f"label_value_{key}"] = value
                    
            where_clause = " AND ".join(conditions)
            
            # Time bucket calculation
            bucket_size = self._get_bucket_size(request.resolution)
            
            query = f"""
                SELECT 
                    metric_name,
                    date_trunc('{bucket_size}', timestamp) as time_bucket,
                    {self._get_aggregation_function(request.aggregation)}(value) as value,
                    labels
                FROM analytics_metrics 
                WHERE {where_clause}
                GROUP BY metric_name, time_bucket, labels
                ORDER BY metric_name, time_bucket
            """
            
            if request.limit:
                query += f" LIMIT {request.limit}"
                
            async with self.engine.begin() as conn:
                result = await conn.execute(text(query), params)
                rows = result.fetchall()
                
            # Convert to TimeSeriesData
            metrics_data = {}
            for row in rows:
                metric_name = row.metric_name
                if metric_name not in metrics_data:
                    metrics_data[metric_name] = []
                    
                point = MetricPoint(
                    name=metric_name,
                    value=float(row.value),
                    timestamp=row.time_bucket,
                    labels=json.loads(row.labels) if row.labels else {}
                )
                metrics_data[metric_name].append(point)
                
            time_series = []
            for metric_name, points in metrics_data.items():
                ts = TimeSeriesData(
                    metric_name=metric_name,
                    points=points,
                    resolution=request.resolution,
                    start_time=request.start_time,
                    end_time=request.end_time
                )
                time_series.append(ts)
                
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return QueryResult(
                query=request,
                data=time_series,
                total_points=sum(len(ts.points) for ts in time_series),
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            logger.error(f"Failed to query metrics: {e}")
            raise
            
    async def query_events(self, event_type: Optional[str] = None,
                          start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None,
                          user_id: Optional[str] = None,
                          limit: int = 1000) -> List[AnalyticsEvent]:
        """Query analytics events"""
        try:
            conditions = []
            params = {}
            
            if event_type:
                conditions.append("event_type = :event_type")
                params["event_type"] = event_type
                
            if start_time:
                conditions.append("timestamp >= :start_time")
                params["start_time"] = start_time
                
            if end_time:
                conditions.append("timestamp <= :end_time")
                params["end_time"] = end_time
                
            if user_id:
                conditions.append("user_id = :user_id")
                params["user_id"] = user_id
                
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            query = f"""
                SELECT event_id, event_type, source, timestamp, data, labels, user_id, session_id
                FROM analytics_events 
                {where_clause}
                ORDER BY timestamp DESC
                LIMIT {limit}
            """
            
            async with self.engine.begin() as conn:
                result = await conn.execute(text(query), params)
                rows = result.fetchall()
                
            events = []
            for row in rows:
                event = AnalyticsEvent(
                    event_id=row.event_id,
                    event_type=row.event_type,
                    source=row.source,
                    timestamp=row.timestamp,
                    data=json.loads(row.data) if row.data else {},
                    labels=json.loads(row.labels) if row.labels else {},
                    user_id=row.user_id,
                    session_id=row.session_id
                )
                events.append(event)
                
            return events
            
        except Exception as e:
            logger.error(f"Failed to query events: {e}")
            raise
            
    async def cleanup_old_data(self, retention_days: int):
        """Clean up old analytics data"""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        try:
            async with self.engine.begin() as conn:
                # Clean up old metrics
                result = await conn.execute(text("""
                    DELETE FROM analytics_metrics WHERE timestamp < :cutoff_date
                """), {"cutoff_date": cutoff_date})
                
                metrics_deleted = result.rowcount
                
                # Clean up old events
                result = await conn.execute(text("""
                    DELETE FROM analytics_events WHERE timestamp < :cutoff_date
                """), {"cutoff_date": cutoff_date})
                
                events_deleted = result.rowcount
                
                # Clean up old aggregates
                result = await conn.execute(text("""
                    DELETE FROM analytics_aggregates WHERE time_bucket < :cutoff_date
                """), {"cutoff_date": cutoff_date})
                
                aggregates_deleted = result.rowcount
                
                logger.info(f"Cleaned up analytics data: {metrics_deleted} metrics, "
                          f"{events_deleted} events, {aggregates_deleted} aggregates")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            raise
            
    def _get_bucket_size(self, resolution: TimeResolution) -> str:
        """Get PostgreSQL date_trunc bucket size"""
        mapping = {
            TimeResolution.MINUTE: "minute",
            TimeResolution.FIVE_MINUTES: "minute",  # Will handle in aggregation
            TimeResolution.FIFTEEN_MINUTES: "minute",
            TimeResolution.HOUR: "hour",
            TimeResolution.DAY: "day",
            TimeResolution.WEEK: "week",
            TimeResolution.MONTH: "month"
        }
        return mapping.get(resolution, "minute")
        
    def _get_aggregation_function(self, aggregation: AggregationType) -> str:
        """Get SQL aggregation function"""
        mapping = {
            AggregationType.SUM: "SUM",
            AggregationType.AVG: "AVG",
            AggregationType.MIN: "MIN",
            AggregationType.MAX: "MAX",
            AggregationType.COUNT: "COUNT",
            AggregationType.MEDIAN: "PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY",
            AggregationType.P95: "PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY",
            AggregationType.P99: "PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY"
        }
        func = mapping.get(aggregation, "AVG")
        
        if aggregation in [AggregationType.MEDIAN, AggregationType.P95, AggregationType.P99]:
            return f"{func} value)"
        return func


class AnalyticsStorage:
    """High-level analytics storage interface"""
    
    def __init__(self):
        # Use the existing database session for analytics data
        self._initialized = False
        
    async def initialize(self):
        """Initialize all storage backends"""
        if self._initialized:
            return
            
        # Create analytics tables using the existing database session
        try:
            with get_db_manager().get_session() as session:
                # Create analytics tables if they don't exist
                session.execute(text("""
                CREATE TABLE IF NOT EXISTS analytics_metrics (
                    id SERIAL PRIMARY KEY,
                    metric_name VARCHAR(255) NOT NULL,
                    value DOUBLE PRECISION NOT NULL,
                    labels JSONB DEFAULT '{}',
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    metric_type VARCHAR(50) DEFAULT 'gauge'
                );
            """))
            
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS analytics_events (
                    id SERIAL PRIMARY KEY,
                    event_id VARCHAR(255) UNIQUE NOT NULL,
                    event_type VARCHAR(100) NOT NULL,
                    source VARCHAR(100) NOT NULL,
                    data JSONB DEFAULT '{}',
                    labels JSONB DEFAULT '{}',
                    user_id VARCHAR(255),
                    session_id VARCHAR(255),
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """))
            
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_analytics_metrics_name_timestamp 
                ON analytics_metrics(metric_name, timestamp);
            """))
            
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_analytics_events_type_timestamp 
                ON analytics_events(event_type, timestamp);
            """))
                
            session.commit()
            
            self._initialized = True
            logger.info("Analytics storage initialized")
        except Exception as e:
            logger.error(f"Failed to initialize analytics storage: {e}")
            raise
        
    async def store_system_metrics(self, metrics: SystemMetrics):
        """Store system metrics as time-series data"""
        timestamp = metrics.timestamp
        metric_points = [
            MetricPoint("system.cpu.usage", metrics.cpu_usage, timestamp),
            MetricPoint("system.memory.usage", metrics.memory_usage, timestamp),
            MetricPoint("system.disk.usage", metrics.disk_usage, timestamp),
            MetricPoint("system.services.active", metrics.active_services, timestamp),
            MetricPoint("system.requests.total", metrics.total_requests, timestamp),
            MetricPoint("system.errors.rate", metrics.error_rate, timestamp),
            MetricPoint("system.response_time.avg", metrics.avg_response_time, timestamp),
        ]
        
        # Add network I/O metrics
        for key, value in metrics.network_io.items():
            metric_points.append(
                MetricPoint(f"system.network.{key}", value, timestamp)
            )
            
        await self.time_series.store_metrics(metric_points)
        
    async def store_service_metrics(self, metrics: ServiceMetrics):
        """Store service metrics as time-series data"""
        timestamp = metrics.timestamp
        labels = {"service_id": metrics.service_id, "service_name": metrics.service_name}
        
        metric_points = [
            MetricPoint("service.cpu.usage", metrics.cpu_usage, timestamp, labels),
            MetricPoint("service.memory.usage", metrics.memory_usage, timestamp, labels),
            MetricPoint("service.requests.count", metrics.request_count, timestamp, labels),
            MetricPoint("service.errors.count", metrics.error_count, timestamp, labels),
            MetricPoint("service.response_time.avg", metrics.response_time_avg, timestamp, labels),
            MetricPoint("service.uptime", metrics.uptime, timestamp, labels),
        ]
        
        # Add network and disk I/O metrics
        for key, value in metrics.network_io.items():
            metric_points.append(
                MetricPoint(f"service.network.{key}", value, timestamp, labels)
            )
            
        for key, value in metrics.disk_io.items():
            metric_points.append(
                MetricPoint(f"service.disk.{key}", value, timestamp, labels)
            )
            
        await self.time_series.store_metrics(metric_points)
        
    async def store_events(self, events: List[AnalyticsEvent]):
        """Store analytics events"""
        await self.time_series.store_events(events)
        
    async def query_metrics(self, request: QueryRequest) -> QueryResult:
        """Query metrics data"""
        return await self.time_series.query_metrics(request)
        
    async def query_events(self, **kwargs) -> List[AnalyticsEvent]:
        """Query events data"""
        return await self.time_series.query_events(**kwargs)
        
    async def cleanup_old_data(self, retention_days: int):
        """Clean up old data"""
        await self.time_series.cleanup_old_data(retention_days)


# Global storage instance
_analytics_storage: Optional[AnalyticsStorage] = None


def get_analytics_storage() -> Optional[AnalyticsStorage]:
    """Get global analytics storage instance"""
    return _analytics_storage


async def init_analytics_storage() -> AnalyticsStorage:
    """Initialize global analytics storage"""
    global _analytics_storage
    _analytics_storage = AnalyticsStorage()
    await _analytics_storage.initialize()
    return _analytics_storage