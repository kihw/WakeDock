"""
Analytics Reporter

Generates comprehensive reports from analytics data including:
- Performance reports
- Usage statistics  
- Service health reports
- Custom dashboards
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

from .types import (
    Report, QueryRequest, TimeResolution, AggregationType,
    ChartConfig, UsageStats, PerformanceMetrics
)
from .storage import get_analytics_storage

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates specific types of reports"""
    
    def __init__(self):
        self.storage = get_analytics_storage()
        
    async def generate_system_performance_report(self, start_time: datetime, 
                                               end_time: datetime) -> Report:
        """Generate system performance report"""
        report_id = str(uuid.uuid4())
        
        # Query system metrics
        system_request = QueryRequest(
            metric_names=[
                "system.cpu.usage",
                "system.memory.usage",
                "system.disk.usage",
                "system.network.bytes_sent",
                "system.network.bytes_recv"
            ],
            start_time=start_time,
            end_time=end_time,
            resolution=TimeResolution.HOUR,
            aggregation=AggregationType.AVG
        )
        
        system_data = await self.storage.query_metrics(system_request)
        
        # Calculate summary statistics
        summary = {}
        for ts in system_data.data:
            metric_values = [point.value for point in ts.points]
            if metric_values:
                summary[ts.metric_name] = {
                    "avg": sum(metric_values) / len(metric_values),
                    "min": min(metric_values),
                    "max": max(metric_values),
                    "current": metric_values[-1] if metric_values else 0
                }
        
        # Create charts configuration
        charts = [
            {
                "chart_type": "line",
                "title": "CPU Usage Over Time",
                "data": [
                    {
                        "timestamp": point.timestamp.isoformat(),
                        "value": point.value
                    }
                    for ts in system_data.data if ts.metric_name == "system.cpu.usage"
                    for point in ts.points
                ]
            },
            {
                "chart_type": "line",
                "title": "Memory Usage Over Time",
                "data": [
                    {
                        "timestamp": point.timestamp.isoformat(),
                        "value": point.value
                    }
                    for ts in system_data.data if ts.metric_name == "system.memory.usage"
                    for point in ts.points
                ]
            }
        ]
        
        return Report(
            report_id=report_id,
            title="System Performance Report",
            description=f"System performance analysis from {start_time} to {end_time}",
            report_type="system_performance",
            period_start=start_time,
            period_end=end_time,
            data={"metrics": [ts.dict() for ts in system_data.data]},
            charts=charts,
            summary=summary
        )
        
    async def generate_service_usage_report(self, start_time: datetime,
                                          end_time: datetime,
                                          service_id: Optional[str] = None) -> Report:
        """Generate service usage report"""
        report_id = str(uuid.uuid4())
        
        # Query service metrics
        metric_names = [
            "service.cpu.usage",
            "service.memory.usage", 
            "service.requests.count",
            "service.response_time.avg"
        ]
        
        labels = {}
        if service_id:
            labels["service_id"] = service_id
            
        service_request = QueryRequest(
            metric_names=metric_names,
            start_time=start_time,
            end_time=end_time,
            resolution=TimeResolution.HOUR,
            aggregation=AggregationType.AVG,
            labels=labels
        )
        
        service_data = await self.storage.query_metrics(service_request)
        
        # Group by service
        services_data = {}
        for ts in service_data.data:
            for point in ts.points:
                svc_id = point.labels.get("service_id", "unknown")
                if svc_id not in services_data:
                    services_data[svc_id] = {
                        "service_name": point.labels.get("service_name", "Unknown"),
                        "metrics": {}
                    }
                
                if ts.metric_name not in services_data[svc_id]["metrics"]:
                    services_data[svc_id]["metrics"][ts.metric_name] = []
                    
                services_data[svc_id]["metrics"][ts.metric_name].append({
                    "timestamp": point.timestamp.isoformat(),
                    "value": point.value
                })
        
        # Calculate usage statistics per service
        usage_stats = {}
        for svc_id, data in services_data.items():
            requests_data = data["metrics"].get("service.requests.count", [])
            response_time_data = data["metrics"].get("service.response_time.avg", [])
            
            total_requests = sum(point["value"] for point in requests_data)
            avg_response_time = (
                sum(point["value"] for point in response_time_data) / len(response_time_data)
                if response_time_data else 0
            )
            
            usage_stats[svc_id] = {
                "service_name": data["service_name"],
                "total_requests": total_requests,
                "avg_response_time": avg_response_time,
                "data_points": len(requests_data)
            }
        
        return Report(
            report_id=report_id,
            title="Service Usage Report",
            description=f"Service usage analysis from {start_time} to {end_time}",
            report_type="service_usage",
            period_start=start_time,
            period_end=end_time,
            data={"services": services_data},
            charts=[],  # Charts would be generated on frontend
            summary=usage_stats
        )
        
    async def generate_api_analytics_report(self, start_time: datetime,
                                          end_time: datetime) -> Report:
        """Generate API analytics report"""
        report_id = str(uuid.uuid4())
        
        # Query API events
        api_events = await self.storage.query_events(
            event_type="api_call",
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )
        
        # Analyze API usage
        endpoint_stats = {}
        status_codes = {}
        hourly_requests = {}
        
        for event in api_events:
            data = event.data
            endpoint = data.get("endpoint", "unknown")
            status_code = data.get("status_code", 0)
            response_time = data.get("response_time", 0)
            
            # Endpoint statistics
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = {
                    "total_requests": 0,
                    "total_response_time": 0,
                    "error_count": 0,
                    "methods": set()
                }
            
            endpoint_stats[endpoint]["total_requests"] += 1
            endpoint_stats[endpoint]["total_response_time"] += response_time
            endpoint_stats[endpoint]["methods"].add(data.get("method", "GET"))
            
            if status_code >= 400:
                endpoint_stats[endpoint]["error_count"] += 1
                
            # Status code distribution
            status_codes[status_code] = status_codes.get(status_code, 0) + 1
            
            # Hourly request distribution
            hour = event.timestamp.replace(minute=0, second=0, microsecond=0)
            hourly_requests[hour] = hourly_requests.get(hour, 0) + 1
        
        # Calculate averages and error rates
        for endpoint, stats in endpoint_stats.items():
            if stats["total_requests"] > 0:
                stats["avg_response_time"] = stats["total_response_time"] / stats["total_requests"]
                stats["error_rate"] = (stats["error_count"] / stats["total_requests"]) * 100
            else:
                stats["avg_response_time"] = 0
                stats["error_rate"] = 0
                
            stats["methods"] = list(stats["methods"])
        
        summary = {
            "total_api_calls": len(api_events),
            "unique_endpoints": len(endpoint_stats),
            "avg_response_time": (
                sum(s["avg_response_time"] for s in endpoint_stats.values()) / len(endpoint_stats)
                if endpoint_stats else 0
            ),
            "error_rate": (
                sum(s["error_count"] for s in endpoint_stats.values()) / len(api_events) * 100
                if api_events else 0
            )
        }
        
        return Report(
            report_id=report_id,
            title="API Analytics Report",
            description=f"API usage analysis from {start_time} to {end_time}",
            report_type="api_analytics",
            period_start=start_time,
            period_end=end_time,
            data={
                "endpoint_stats": endpoint_stats,
                "status_codes": status_codes,
                "hourly_requests": {k.isoformat(): v for k, v in hourly_requests.items()}
            },
            charts=[],
            summary=summary
        )


class AnalyticsReporter:
    """Main analytics reporting service"""
    
    def __init__(self):
        self.generator = ReportGenerator()
        self.reports_cache: Dict[str, Report] = {}
        
    async def generate_report(self, report_type: str, start_time: datetime,
                            end_time: datetime, user_id: str,
                            **kwargs) -> Report:
        """Generate a report of the specified type"""
        try:
            if report_type == "system_performance":
                report = await self.generator.generate_system_performance_report(
                    start_time, end_time
                )
            elif report_type == "service_usage":
                service_id = kwargs.get("service_id")
                report = await self.generator.generate_service_usage_report(
                    start_time, end_time, service_id
                )
            elif report_type == "api_analytics":
                report = await self.generator.generate_api_analytics_report(
                    start_time, end_time
                )
            else:
                raise ValueError(f"Unknown report type: {report_type}")
            
            # Cache the report
            self.reports_cache[report.report_id] = report
            
            logger.info(f"Generated {report_type} report {report.report_id} for user {user_id}")
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate {report_type} report: {e}")
            raise
            
    async def get_report(self, report_id: str) -> Optional[Report]:
        """Get a cached report"""
        return self.reports_cache.get(report_id)
        
    async def list_reports(self, user_id: Optional[str] = None) -> List[Report]:
        """List available reports"""
        # In a full implementation, this would query a database
        # For now, return cached reports
        reports = list(self.reports_cache.values())
        
        # Sort by generation time, newest first
        reports.sort(key=lambda r: r.generated_at, reverse=True)
        
        return reports
        
    async def delete_report(self, report_id: str) -> bool:
        """Delete a report"""
        if report_id in self.reports_cache:
            del self.reports_cache[report_id]
            return True
        return False
        
    async def export_report(self, report_id: str, format: str = "json") -> Optional[bytes]:
        """Export report in specified format"""
        report = self.reports_cache.get(report_id)
        if not report:
            return None
            
        if format == "json":
            return json.dumps(report.dict(), indent=2, default=str).encode()
        elif format == "csv":
            # Simplified CSV export for metrics data
            import io
            import csv
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write report metadata
            writer.writerow(["Report ID", report.report_id])
            writer.writerow(["Title", report.title])
            writer.writerow(["Generated", report.generated_at.isoformat()])
            writer.writerow([])  # Empty row
            
            # Write summary data
            writer.writerow(["Summary"])
            for key, value in report.summary.items():
                writer.writerow([key, value])
            
            return output.getvalue().encode()
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Global reporter instance
_analytics_reporter: Optional[AnalyticsReporter] = None


def get_analytics_reporter() -> Optional[AnalyticsReporter]:
    """Get global analytics reporter instance"""
    return _analytics_reporter


def init_analytics_reporter() -> AnalyticsReporter:
    """Initialize global analytics reporter"""
    global _analytics_reporter
    _analytics_reporter = AnalyticsReporter()
    return _analytics_reporter