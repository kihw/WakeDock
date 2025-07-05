"""
Advanced Analytics Module for WakeDock

Provides comprehensive analytics and reporting capabilities including:
- Time-series data collection and storage
- Performance metrics aggregation  
- Service usage analytics
- Resource utilization reporting
- Trend analysis and forecasting
"""

from .collector import AnalyticsCollector, MetricsCollector
from .storage import TimeSeriesStorage, AnalyticsStorage
from .reporter import AnalyticsReporter, ReportGenerator
from .aggregator import DataAggregator, MetricsAggregator
from .types import AnalyticsEvent, MetricPoint, TimeSeriesData, Report

__all__ = [
    "AnalyticsCollector",
    "MetricsCollector", 
    "TimeSeriesStorage",
    "AnalyticsStorage",
    "AnalyticsReporter",
    "ReportGenerator",
    "DataAggregator",
    "MetricsAggregator",
    "AnalyticsEvent",
    "MetricPoint",
    "TimeSeriesData", 
    "Report"
]