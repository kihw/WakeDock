"""
Analytics API Routes

Provides REST endpoints for analytics data and reporting:
- Metrics querying and aggregation
- Event data retrieval  
- Report generation
- Dashboard data feeds
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import json
import io
import csv

from wakedock.analytics.types import (
    QueryRequest, QueryResult, TimeResolution, AggregationType,
    AnalyticsEvent, Report, ChartConfig
)
from wakedock.analytics.collector import get_analytics_collector
from wakedock.analytics.storage import get_analytics_storage
from wakedock.analytics.reporter import get_analytics_reporter
from wakedock.api.auth.dependencies import get_current_user
from wakedock.database.models import UserRole

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", summary="Analytics Service Health")
async def analytics_health():
    """Check analytics service health"""
    collector = get_analytics_collector()
    storage = get_analytics_storage()
    
    health_status = {
        "collector_active": collector is not None,
        "storage_initialized": storage is not None and storage._initialized,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if not (health_status["collector_active"] and health_status["storage_initialized"]):
        raise HTTPException(
            status_code=503,
            detail="Analytics service not fully initialized"
        )
    
    return health_status


@router.post("/query", summary="Query Analytics Data")
async def query_analytics(
    request: QueryRequest,
    current_user = Depends(get_current_user)
) -> QueryResult:
    """
    Query analytics metrics with aggregation and filtering.
    
    Supports:
    - Time-series data querying
    - Multiple aggregation functions
    - Label-based filtering
    - Custom time resolutions
    """
    storage = get_analytics_storage()
    if not storage:
        raise HTTPException(
            status_code=503,
            detail="Analytics storage not available"
        )
    
    try:
        result = await storage.query_metrics(request)
        return result
        
    except Exception as e:
        logger.error(f"Error querying analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to query analytics data"
        )


@router.get("/metrics/system", summary="System Metrics")
async def get_system_metrics(
    hours: int = Query(24, ge=1, le=168, description="Hours of data to retrieve"),
    resolution: TimeResolution = Query(TimeResolution.HOUR, description="Data resolution"),
    current_user = Depends(get_current_user)
) -> QueryResult:
    """Get system-wide metrics for the specified time period"""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    request = QueryRequest(
        metric_names=[
            "system.cpu.usage",
            "system.memory.usage", 
            "system.disk.usage",
            "system.services.active"
        ],
        start_time=start_time,
        end_time=end_time,
        resolution=resolution,
        aggregation=AggregationType.AVG
    )
    
    return await query_analytics(request, current_user)


@router.get("/metrics/services", summary="Service Metrics")
async def get_service_metrics(
    service_id: Optional[str] = Query(None, description="Specific service ID"),
    hours: int = Query(24, ge=1, le=168, description="Hours of data to retrieve"),
    resolution: TimeResolution = Query(TimeResolution.HOUR, description="Data resolution"),
    current_user = Depends(get_current_user)
) -> QueryResult:
    """Get service metrics for the specified time period"""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    metric_names = [
        "service.cpu.usage",
        "service.memory.usage",
        "service.requests.count",
        "service.response_time.avg"
    ]
    
    labels = {}
    if service_id:
        labels["service_id"] = service_id
    
    request = QueryRequest(
        metric_names=metric_names,
        start_time=start_time,
        end_time=end_time,
        resolution=resolution,
        aggregation=AggregationType.AVG,
        labels=labels
    )
    
    return await query_analytics(request, current_user)


@router.get("/events", summary="Analytics Events")
async def get_analytics_events(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    hours: int = Query(24, ge=1, le=168, description="Hours of data to retrieve"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum events to return"),
    current_user = Depends(get_current_user)
) -> List[AnalyticsEvent]:
    """Get analytics events with filtering"""
    storage = get_analytics_storage()
    if not storage:
        raise HTTPException(
            status_code=503,
            detail="Analytics storage not available"
        )
    
    # Only allow users to see their own events unless admin
    if current_user.role != UserRole.ADMIN and user_id != str(current_user.id):
        user_id = str(current_user.id)
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    try:
        events = await storage.query_events(
            event_type=event_type,
            start_time=start_time,
            end_time=end_time,
            user_id=user_id,
            limit=limit
        )
        return events
        
    except Exception as e:
        logger.error(f"Error querying events: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to query analytics events"
        )


@router.get("/dashboard", summary="Dashboard Data")
async def get_dashboard_data(
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get comprehensive dashboard analytics data"""
    try:
        # Get system metrics for last 24 hours
        system_request = QueryRequest(
            metric_names=["system.cpu.usage", "system.memory.usage", "system.disk.usage"],
            start_time=datetime.utcnow() - timedelta(hours=24),
            end_time=datetime.utcnow(),
            resolution=TimeResolution.HOUR,
            aggregation=AggregationType.AVG
        )
        
        storage = get_analytics_storage()
        collector = get_analytics_collector()
        
        if not storage or not collector:
            raise HTTPException(
                status_code=503,
                detail="Analytics services not available"
            )
        
        # Get recent system metrics
        system_metrics = await storage.query_metrics(system_request)
        
        # Get API metrics
        api_metrics = collector.get_api_metrics()
        
        # Get recent events
        recent_events = await storage.query_events(
            start_time=datetime.utcnow() - timedelta(hours=1),
            limit=50
        )
        
        # Calculate summary statistics
        summary = {
            "total_events_last_hour": len(recent_events),
            "total_api_endpoints": len(api_metrics),
            "total_metrics_points": sum(len(ts.points) for ts in system_metrics.data),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return {
            "summary": summary,
            "system_metrics": system_metrics.dict(),
            "api_metrics": api_metrics,
            "recent_events": [event.dict() for event in recent_events[:10]]  # Last 10 events
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve dashboard data"
        )


@router.get("/reports/list", summary="List Available Reports")
async def list_reports(
    current_user = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """List available analytics reports"""
    reporter = get_analytics_reporter()
    if not reporter:
        raise HTTPException(
            status_code=503,
            detail="Analytics reporter not available"
        )
    
    try:
        reports = await reporter.list_reports()
        return [report.dict() for report in reports]
        
    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to list reports"
        )


@router.post("/reports/generate", summary="Generate Analytics Report")
async def generate_report(
    report_type: str,
    period_hours: int = Query(24, ge=1, le=8760, description="Report period in hours"),
    background_tasks: BackgroundTasks = None,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Generate a new analytics report"""
    reporter = get_analytics_reporter()
    if not reporter:
        raise HTTPException(
            status_code=503,
            detail="Analytics reporter not available"
        )
    
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=period_hours)
        
        report = await reporter.generate_report(
            report_type=report_type,
            start_time=start_time,
            end_time=end_time,
            user_id=str(current_user.id)
        )
        
        return {
            "report_id": report.report_id,
            "status": "generated",
            "generated_at": report.generated_at.isoformat(),
            "period": {
                "start": report.period_start.isoformat(),
                "end": report.period_end.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate report"
        )


@router.get("/reports/{report_id}", summary="Get Analytics Report")
async def get_report(
    report_id: str,
    current_user = Depends(get_current_user)
) -> Report:
    """Get a specific analytics report"""
    reporter = get_analytics_reporter()
    if not reporter:
        raise HTTPException(
            status_code=503,
            detail="Analytics reporter not available"
        )
    
    try:
        report = await reporter.get_report(report_id)
        if not report:
            raise HTTPException(
                status_code=404,
                detail="Report not found"
            )
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve report"
        )


@router.get("/export/csv", summary="Export Analytics Data as CSV")
async def export_csv(
    metric_names: List[str] = Query(..., description="Metrics to export"),
    hours: int = Query(24, ge=1, le=168, description="Hours of data to export"),
    resolution: TimeResolution = Query(TimeResolution.HOUR, description="Data resolution"),
    current_user = Depends(get_current_user)
):
    """Export analytics data as CSV file"""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    request = QueryRequest(
        metric_names=metric_names,
        start_time=start_time,
        end_time=end_time,
        resolution=resolution,
        aggregation=AggregationType.AVG
    )
    
    storage = get_analytics_storage()
    if not storage:
        raise HTTPException(
            status_code=503,
            detail="Analytics storage not available"
        )
    
    try:
        result = await storage.query_metrics(request)
        
        # Convert to CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["timestamp", "metric_name", "value", "labels"])
        
        # Write data
        for ts in result.data:
            for point in ts.points:
                writer.writerow([
                    point.timestamp.isoformat(),
                    point.name,
                    point.value,
                    json.dumps(point.labels)
                ])
        
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=analytics_{int(datetime.now().timestamp())}.csv"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to export data"
        )


@router.get("/stats", summary="Analytics Statistics")
async def get_analytics_stats(
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get analytics service statistics"""
    collector = get_analytics_collector()
    storage = get_analytics_storage()
    
    if not collector or not storage:
        raise HTTPException(
            status_code=503,
            detail="Analytics services not available"
        )
    
    try:
        # Get collection stats
        api_metrics = collector.get_api_metrics()
        
        # Get storage stats (simplified)
        stats = {
            "collection": {
                "active": True,
                "api_endpoints_tracked": len(api_metrics),
                "total_api_calls": sum(m["total_calls"] for m in api_metrics.values()),
                "avg_response_time": sum(m["avg_response_time"] for m in api_metrics.values()) / len(api_metrics) if api_metrics else 0
            },
            "storage": {
                "initialized": storage._initialized,
                "backend": "postgresql"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting analytics stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve analytics statistics"
        )