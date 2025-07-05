"""
Analytics Types and Data Models

Defines the core data structures for analytics and reporting.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel, Field


class MetricType(str, Enum):
    """Types of metrics collected"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class AggregationType(str, Enum):
    """Aggregation methods for time-series data"""
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    MEDIAN = "median"
    P95 = "p95"
    P99 = "p99"


class TimeResolution(str, Enum):
    """Time resolution for data aggregation"""
    MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    HOUR = "1h"
    DAY = "1d"
    WEEK = "1w"
    MONTH = "1M"


@dataclass
class MetricPoint:
    """Single metric data point"""
    name: str
    value: Union[int, float]
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE


@dataclass
class TimeSeriesData:
    """Time-series data collection"""
    metric_name: str
    points: List[MetricPoint]
    resolution: TimeResolution
    start_time: datetime
    end_time: datetime
    labels: Dict[str, str] = field(default_factory=dict)


class AnalyticsEvent(BaseModel):
    """Analytics event model"""
    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Type of event")
    source: str = Field(..., description="Event source")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)
    labels: Dict[str, str] = Field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class ServiceMetrics(BaseModel):
    """Service-specific metrics"""
    service_id: str
    service_name: str
    cpu_usage: float
    memory_usage: float
    network_io: Dict[str, float]
    disk_io: Dict[str, float]
    request_count: int
    error_count: int
    response_time_avg: float
    uptime: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SystemMetrics(BaseModel):
    """System-wide metrics"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    active_services: int
    total_requests: int
    error_rate: float
    avg_response_time: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Report(BaseModel):
    """Analytics report model"""
    report_id: str
    title: str
    description: Optional[str] = None
    report_type: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    period_start: datetime
    period_end: datetime
    data: Dict[str, Any]
    charts: List[Dict[str, Any]] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)


class ChartConfig(BaseModel):
    """Chart configuration for reports"""
    chart_type: str = Field(..., description="Type of chart (line, bar, pie, etc.)")
    title: str
    x_axis: str
    y_axis: str
    data_source: str
    filters: Dict[str, Any] = Field(default_factory=dict)
    options: Dict[str, Any] = Field(default_factory=dict)


class AlertRule(BaseModel):
    """Analytics-based alert rule"""
    rule_id: str
    name: str
    description: Optional[str] = None
    metric_name: str
    condition: str  # e.g., ">"
    threshold: float
    duration: timedelta
    labels: Dict[str, str] = Field(default_factory=dict)
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class QueryRequest(BaseModel):
    """Analytics query request"""
    metric_names: List[str]
    start_time: datetime
    end_time: datetime
    resolution: TimeResolution = TimeResolution.MINUTE
    aggregation: AggregationType = AggregationType.AVG
    labels: Dict[str, str] = Field(default_factory=dict)
    limit: Optional[int] = None


class QueryResult(BaseModel):
    """Analytics query result"""
    query: QueryRequest
    data: List[TimeSeriesData]
    total_points: int
    execution_time_ms: float
    cached: bool = False


@dataclass
class AnalyticsConfig:
    """Analytics configuration"""
    enabled: bool = True
    retention_days: int = 30
    collection_interval: int = 60  # seconds
    storage_backend: str = "postgres"  # postgres, influxdb, prometheus
    batch_size: int = 1000
    compression: bool = True
    parallel_processing: bool = True
    cache_results: bool = True
    cache_ttl: int = 300  # seconds


class UsageStats(BaseModel):
    """Service usage statistics"""
    service_id: str
    total_requests: int
    unique_users: int
    avg_session_duration: float
    peak_concurrent_users: int
    most_used_features: List[str]
    error_rate: float
    availability: float
    period_start: datetime
    period_end: datetime


class PerformanceMetrics(BaseModel):
    """Performance metrics summary"""
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    throughput: float  # requests per second
    error_rate: float
    cpu_utilization: float
    memory_utilization: float
    disk_utilization: float
    network_utilization: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)