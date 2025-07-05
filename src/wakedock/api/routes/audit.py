"""
Audit Log API Routes

API endpoints for managing and querying audit logs:
- View audit logs with filtering
- Export audit logs
- Search audit events
- Audit statistics and reports
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_
import csv
import io
import json

from wakedock.database.database import get_db_session
from wakedock.database.models import User
from wakedock.api.auth.dependencies import get_current_active_user
from wakedock.security.audit import AuditLog, AuditEventType, AuditSeverity, get_audit_service
from wakedock.security.rbac import Permission, RequirePermission

router = APIRouter()


class AuditLogResponse(BaseModel):
    """Response model for audit log entries"""
    id: int
    event_type: str
    severity: str
    user_id: Optional[int]
    username: Optional[str]
    user_role: Optional[str]
    ip_address: Optional[str]
    endpoint: Optional[str]
    method: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    action: str
    description: str
    metadata: Optional[dict]
    success: bool
    error_message: Optional[str]
    timestamp: datetime
    
    class Config:
        from_attributes = True


class AuditLogFilter(BaseModel):
    """Filter parameters for audit log queries"""
    event_type: Optional[str] = None
    severity: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    resource_type: Optional[str] = None
    success: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)


class AuditStatsResponse(BaseModel):
    """Response model for audit statistics"""
    total_events: int
    events_last_24h: int
    events_last_7d: int
    events_by_type: dict
    events_by_severity: dict
    events_by_user: dict
    failed_events: int
    security_violations: int


@router.get("/logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    severity: Optional[str] = Query(None, description="Filter by severity level"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    username: Optional[str] = Query(None, description="Filter by username"),
    ip_address: Optional[str] = Query(None, description="Filter by IP address"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    success: Optional[bool] = Query(None, description="Filter by success status"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    limit: int = Query(100, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(RequirePermission(Permission.AUDIT_READ))
):
    """
    Retrieve audit logs with optional filtering.
    
    Requires AUDIT_READ permission.
    """
    try:
        query = db.query(AuditLog).order_by(desc(AuditLog.timestamp))
        
        # Apply filters
        if event_type:
            query = query.filter(AuditLog.event_type == event_type)
        
        if severity:
            query = query.filter(AuditLog.severity == severity)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        if username:
            query = query.filter(AuditLog.username.ilike(f"%{username}%"))
        
        if ip_address:
            query = query.filter(AuditLog.ip_address == ip_address)
        
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        
        if success is not None:
            query = query.filter(AuditLog.success == success)
        
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        # Apply pagination
        total = query.count()
        logs = query.offset(offset).limit(limit).all()
        
        # Log the audit query for security tracking
        audit_service = get_audit_service()
        await audit_service.log_event(
            event_type=AuditEventType.AUDIT_READ,
            severity=AuditSeverity.LOW,
            user_id=current_user.id,
            username=current_user.username,
            action="query_audit_logs",
            description=f"User {current_user.username} queried audit logs (returned {len(logs)} records)",
            metadata={
                "filters": {
                    "event_type": event_type,
                    "severity": severity,
                    "user_id": user_id,
                    "username": username,
                    "ip_address": ip_address,
                    "resource_type": resource_type,
                    "success": success,
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "pagination": {"limit": limit, "offset": offset},
                "total_results": total
            }
        )
        
        return logs
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit logs: {str(e)}"
        )


@router.get("/logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(RequirePermission(Permission.AUDIT_READ))
):
    """
    Retrieve a specific audit log entry by ID.
    
    Requires AUDIT_READ permission.
    """
    log_entry = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    
    if not log_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log entry not found"
        )
    
    # Log the access for security tracking
    audit_service = get_audit_service()
    await audit_service.log_event(
        event_type=AuditEventType.AUDIT_READ,
        severity=AuditSeverity.LOW,
        user_id=current_user.id,
        username=current_user.username,
        action="view_audit_log",
        description=f"User {current_user.username} viewed audit log entry {log_id}",
        metadata={"audit_log_id": log_id}
    )
    
    return log_entry


@router.get("/stats", response_model=AuditStatsResponse)
async def get_audit_statistics(
    days: int = Query(30, ge=1, le=365, description="Number of days to include in statistics"),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(RequirePermission(Permission.AUDIT_READ))
):
    """
    Get audit log statistics and summaries.
    
    Requires AUDIT_READ permission.
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        last_24h = end_date - timedelta(hours=24)
        last_7d = end_date - timedelta(days=7)
        
        # Total events
        total_events = db.query(AuditLog).count()
        
        # Events in specific time periods
        events_last_24h = db.query(AuditLog).filter(
            AuditLog.timestamp >= last_24h
        ).count()
        
        events_last_7d = db.query(AuditLog).filter(
            AuditLog.timestamp >= last_7d
        ).count()
        
        # Events by type (for the specified period)
        events_by_type = dict(
            db.query(AuditLog.event_type, func.count(AuditLog.id))
            .filter(AuditLog.timestamp >= start_date)
            .group_by(AuditLog.event_type)
            .all()
        )
        
        # Events by severity
        events_by_severity = dict(
            db.query(AuditLog.severity, func.count(AuditLog.id))
            .filter(AuditLog.timestamp >= start_date)
            .group_by(AuditLog.severity)
            .all()
        )
        
        # Events by user (top 10)
        events_by_user = dict(
            db.query(AuditLog.username, func.count(AuditLog.id))
            .filter(
                and_(
                    AuditLog.timestamp >= start_date,
                    AuditLog.username.isnot(None)
                )
            )
            .group_by(AuditLog.username)
            .order_by(desc(func.count(AuditLog.id)))
            .limit(10)
            .all()
        )
        
        # Failed events
        failed_events = db.query(AuditLog).filter(
            and_(
                AuditLog.timestamp >= start_date,
                AuditLog.success == False
            )
        ).count()
        
        # Security violations
        security_violations = db.query(AuditLog).filter(
            and_(
                AuditLog.timestamp >= start_date,
                AuditLog.event_type == AuditEventType.SECURITY_VIOLATION.value
            )
        ).count()
        
        stats = AuditStatsResponse(
            total_events=total_events,
            events_last_24h=events_last_24h,
            events_last_7d=events_last_7d,
            events_by_type=events_by_type,
            events_by_severity=events_by_severity,
            events_by_user=events_by_user,
            failed_events=failed_events,
            security_violations=security_violations
        )
        
        # Log the statistics query
        audit_service = get_audit_service()
        await audit_service.log_event(
            event_type=AuditEventType.AUDIT_READ,
            severity=AuditSeverity.LOW,
            user_id=current_user.id,
            username=current_user.username,
            action="view_audit_stats",
            description=f"User {current_user.username} viewed audit statistics",
            metadata={"period_days": days}
        )
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit statistics: {str(e)}"
        )


@router.get("/export/csv")
async def export_audit_logs_csv(
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(10000, le=50000),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(RequirePermission(Permission.AUDIT_EXPORT))
):
    """
    Export audit logs to CSV format.
    
    Requires AUDIT_EXPORT permission.
    """
    try:
        query = db.query(AuditLog).order_by(desc(AuditLog.timestamp))
        
        # Apply filters
        if event_type:
            query = query.filter(AuditLog.event_type == event_type)
        if severity:
            query = query.filter(AuditLog.severity == severity)
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        logs = query.limit(limit).all()
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Event Type', 'Severity', 'User ID', 'Username', 'User Role',
            'IP Address', 'Endpoint', 'Method', 'Resource Type', 'Resource ID',
            'Action', 'Description', 'Success', 'Error Message', 'Timestamp'
        ])
        
        # Write data
        for log in logs:
            writer.writerow([
                log.id, log.event_type, log.severity, log.user_id, log.username,
                log.user_role, log.ip_address, log.endpoint, log.method,
                log.resource_type, log.resource_id, log.action, log.description,
                log.success, log.error_message, log.timestamp.isoformat()
            ])
        
        output.seek(0)
        
        # Log the export
        audit_service = get_audit_service()
        await audit_service.log_event(
            event_type=AuditEventType.AUDIT_EXPORT,
            severity=AuditSeverity.MEDIUM,
            user_id=current_user.id,
            username=current_user.username,
            action="export_audit_logs_csv",
            description=f"User {current_user.username} exported {len(logs)} audit logs to CSV",
            metadata={
                "export_format": "csv",
                "record_count": len(logs),
                "filters": {
                    "event_type": event_type,
                    "severity": severity,
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                }
            }
        )
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"audit_logs_{timestamp}.csv"
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export audit logs: {str(e)}"
        )


@router.get("/export/json")
async def export_audit_logs_json(
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(10000, le=50000),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(RequirePermission(Permission.AUDIT_EXPORT))
):
    """
    Export audit logs to JSON format.
    
    Requires AUDIT_EXPORT permission.
    """
    try:
        query = db.query(AuditLog).order_by(desc(AuditLog.timestamp))
        
        # Apply filters
        if event_type:
            query = query.filter(AuditLog.event_type == event_type)
        if severity:
            query = query.filter(AuditLog.severity == severity)
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        logs = query.limit(limit).all()
        
        # Convert to JSON-serializable format
        export_data = {
            "export_info": {
                "exported_at": datetime.now().isoformat(),
                "exported_by": current_user.username,
                "record_count": len(logs),
                "filters": {
                    "event_type": event_type,
                    "severity": severity,
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                }
            },
            "audit_logs": [
                {
                    "id": log.id,
                    "event_type": log.event_type,
                    "severity": log.severity,
                    "user_id": log.user_id,
                    "username": log.username,
                    "user_role": log.user_role,
                    "ip_address": log.ip_address,
                    "endpoint": log.endpoint,
                    "method": log.method,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "action": log.action,
                    "description": log.description,
                    "metadata": log.metadata,
                    "success": log.success,
                    "error_message": log.error_message,
                    "timestamp": log.timestamp.isoformat()
                }
                for log in logs
            ]
        }
        
        # Log the export
        audit_service = get_audit_service()
        await audit_service.log_event(
            event_type=AuditEventType.AUDIT_EXPORT,
            severity=AuditSeverity.MEDIUM,
            user_id=current_user.id,
            username=current_user.username,
            action="export_audit_logs_json",
            description=f"User {current_user.username} exported {len(logs)} audit logs to JSON",
            metadata={
                "export_format": "json",
                "record_count": len(logs),
                "filters": export_data["export_info"]["filters"]
            }
        )
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"audit_logs_{timestamp}.json"
        
        json_content = json.dumps(export_data, indent=2, default=str)
        
        return StreamingResponse(
            io.BytesIO(json_content.encode('utf-8')),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export audit logs: {str(e)}"
        )


@router.get("/events/types")
async def get_audit_event_types(
    current_user: User = Depends(RequirePermission(Permission.AUDIT_READ))
):
    """
    Get list of all available audit event types.
    
    Requires AUDIT_READ permission.
    """
    return {
        "event_types": [event_type.value for event_type in AuditEventType],
        "severities": [severity.value for severity in AuditSeverity]
    }