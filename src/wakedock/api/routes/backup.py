"""
Backup & Recovery API Routes

Provides REST endpoints for backup and disaster recovery operations:
- Backup creation and management
- Recovery plan execution
- Backup monitoring and validation
- Scheduled job management
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import json
import io

from wakedock.backup import (
    get_backup_automation, get_disaster_recovery, get_backup_monitoring,
    get_backup_scheduler, BackupType, BackupRequest, RestoreRequest,
    BackupJob, BackupConfig
)
from wakedock.api.auth.dependencies import get_current_user
from wakedock.database.models import UserRole

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", summary="Backup Service Health")
async def backup_health():
    """Check backup service health"""
    monitoring = get_backup_monitoring()
    
    if not monitoring:
        raise HTTPException(
            status_code=503,
            detail="Backup monitoring service not available"
        )
    
    try:
        health_check = await monitoring.get_health_check()
        
        if not health_check.healthy:
            return JSONResponse(
                status_code=503,
                content=health_check.dict()
            )
        
        return health_check.dict()
        
    except Exception as e:
        logger.error(f"Backup health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to check backup service health"
        )


@router.post("/create", summary="Create Backup")
async def create_backup(
    request: BackupRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Create a new backup"""
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.USER]:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions for backup operations"
        )
    
    automation = get_backup_automation()
    if not automation:
        raise HTTPException(
            status_code=503,
            detail="Backup automation service not available"
        )
    
    try:
        # Add user information to tags
        request.tags.update({
            "created_by": str(current_user.id),
            "user_email": current_user.email
        })
        
        response = await automation.create_backup(request)
        return response.dict()
        
    except Exception as e:
        logger.error(f"Backup creation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create backup: {str(e)}"
        )


@router.get("/status/{backup_id}", summary="Get Backup Status")
async def get_backup_status(
    backup_id: str,
    current_user = Depends(get_current_user)
):
    """Get backup status"""
    automation = get_backup_automation()
    if not automation:
        raise HTTPException(
            status_code=503,
            detail="Backup automation service not available"
        )
    
    backup_metadata = automation.get_backup_status(backup_id)
    if not backup_metadata:
        raise HTTPException(
            status_code=404,
            detail="Backup not found"
        )
    
    # Check if user can view this backup
    if (current_user.role != UserRole.ADMIN and 
        backup_metadata.tags.get("created_by") != str(current_user.id)):
        raise HTTPException(
            status_code=403,
            detail="Access denied to this backup"
        )
    
    return {
        "backup_id": backup_metadata.backup_id,
        "backup_type": backup_metadata.backup_type.value,
        "status": backup_metadata.status.value,
        "created_at": backup_metadata.created_at.isoformat(),
        "completed_at": backup_metadata.completed_at.isoformat() if backup_metadata.completed_at else None,
        "duration_seconds": backup_metadata.duration_seconds,
        "size_bytes": backup_metadata.size_bytes,
        "compressed_size_bytes": backup_metadata.compressed_size_bytes,
        "compression_ratio": backup_metadata.compression_ratio,
        "checksum": backup_metadata.checksum,
        "error_message": backup_metadata.error_message,
        "tags": backup_metadata.tags
    }


@router.get("/list", summary="List Backups")
async def list_backups(
    backup_type: Optional[BackupType] = Query(None, description="Filter by backup type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    days: int = Query(30, ge=1, le=365, description="Days of history to include"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum backups to return"),
    current_user = Depends(get_current_user)
):
    """List backups with filtering"""
    automation = get_backup_automation()
    if not automation:
        raise HTTPException(
            status_code=503,
            detail="Backup automation service not available"
        )
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Filter backups
    filtered_backups = []
    for backup in automation.backup_history:
        # Date filter
        if backup.created_at < cutoff:
            continue
        
        # Type filter
        if backup_type and backup.backup_type != backup_type:
            continue
        
        # Status filter
        if status and backup.status.value != status:
            continue
        
        # Permission filter
        if (current_user.role != UserRole.ADMIN and 
            backup.tags.get("created_by") != str(current_user.id)):
            continue
        
        filtered_backups.append({
            "backup_id": backup.backup_id,
            "backup_type": backup.backup_type.value,
            "status": backup.status.value,
            "created_at": backup.created_at.isoformat(),
            "completed_at": backup.completed_at.isoformat() if backup.completed_at else None,
            "duration_seconds": backup.duration_seconds,
            "size_bytes": backup.size_bytes,
            "compression_ratio": backup.compression_ratio,
            "tags": backup.tags
        })
    
    # Sort by creation time (newest first) and limit
    filtered_backups.sort(key=lambda x: x["created_at"], reverse=True)
    filtered_backups = filtered_backups[:limit]
    
    return {
        "backups": filtered_backups,
        "total_count": len(filtered_backups),
        "period_days": days
    }


@router.get("/stats", summary="Backup Statistics")
async def get_backup_stats(
    current_user = Depends(get_current_user)
):
    """Get backup statistics"""
    automation = get_backup_automation()
    if not automation:
        raise HTTPException(
            status_code=503,
            detail="Backup automation service not available"
        )
    
    stats = automation.get_backup_stats()
    
    return {
        "total_backups": stats.total_backups,
        "successful_backups": stats.successful_backups,
        "failed_backups": stats.failed_backups,
        "total_size_bytes": stats.total_size_bytes,
        "compressed_size_bytes": stats.compressed_size_bytes,
        "oldest_backup": stats.oldest_backup.isoformat() if stats.oldest_backup else None,
        "newest_backup": stats.newest_backup.isoformat() if stats.newest_backup else None,
        "average_backup_time": stats.average_backup_time,
        "average_compression_ratio": stats.average_compression_ratio,
        "storage_usage_percent": stats.storage_usage_percent
    }


@router.post("/validate/{backup_id}", summary="Validate Backup")
async def validate_backup(
    backup_id: str,
    current_user = Depends(get_current_user)
):
    """Validate backup integrity"""
    # Only admins can validate backups
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required for backup validation"
        )
    
    monitoring = get_backup_monitoring()
    if not monitoring:
        raise HTTPException(
            status_code=503,
            detail="Backup monitoring service not available"
        )
    
    try:
        validation_result = await monitoring.validate_backup(backup_id)
        return validation_result
        
    except Exception as e:
        logger.error(f"Backup validation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Backup validation failed: {str(e)}"
        )


# Recovery endpoints
@router.get("/recovery/plans", summary="List Recovery Plans")
async def list_recovery_plans(
    current_user = Depends(get_current_user)
):
    """List available recovery plans"""
    # Only admins can access recovery plans
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required for recovery operations"
        )
    
    recovery = get_disaster_recovery()
    if not recovery:
        raise HTTPException(
            status_code=503,
            detail="Disaster recovery service not available"
        )
    
    plans = recovery.get_recovery_plans()
    
    return {
        "plans": [
            {
                "plan_id": plan.plan_id,
                "name": plan.name,
                "description": plan.description,
                "backup_types": [bt.value for bt in plan.backup_types],
                "estimated_rto": plan.estimated_rto,
                "estimated_rpo": plan.estimated_rpo,
                "priority": plan.priority,
                "total_steps": len(plan.recovery_steps)
            }
            for plan in plans
        ]
    }


@router.post("/recovery/execute/{plan_id}", summary="Execute Recovery Plan")
async def execute_recovery_plan(
    plan_id: str,
    backup_selection: Optional[Dict[str, str]] = None,
    current_user = Depends(get_current_user)
):
    """Execute a recovery plan"""
    # Only admins can execute recovery
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required for recovery operations"
        )
    
    recovery = get_disaster_recovery()
    if not recovery:
        raise HTTPException(
            status_code=503,
            detail="Disaster recovery service not available"
        )
    
    try:
        # Convert backup selection if provided
        backup_selection_typed = None
        if backup_selection:
            backup_selection_typed = {
                BackupType(key): value for key, value in backup_selection.items()
            }
        
        execution = await recovery.execute_recovery_plan(plan_id, backup_selection_typed)
        
        return {
            "execution_id": execution.execution_id,
            "plan_id": execution.plan_id,
            "status": execution.status,
            "started_at": execution.started_at.isoformat(),
            "total_steps": execution.total_steps,
            "estimated_duration": recovery.recovery_plans[plan_id].estimated_rto * 60  # Convert to seconds
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Recovery execution failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Recovery execution failed: {str(e)}"
        )


@router.get("/recovery/status/{execution_id}", summary="Get Recovery Status")
async def get_recovery_status(
    execution_id: str,
    current_user = Depends(get_current_user)
):
    """Get recovery execution status"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required for recovery operations"
        )
    
    recovery = get_disaster_recovery()
    if not recovery:
        raise HTTPException(
            status_code=503,
            detail="Disaster recovery service not available"
        )
    
    execution = recovery.get_recovery_execution(execution_id)
    if not execution:
        raise HTTPException(
            status_code=404,
            detail="Recovery execution not found"
        )
    
    return {
        "execution_id": execution.execution_id,
        "plan_id": execution.plan_id,
        "status": execution.status,
        "started_at": execution.started_at.isoformat(),
        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
        "steps_completed": execution.steps_completed,
        "total_steps": execution.total_steps,
        "current_step": execution.current_step,
        "error_message": execution.error_message,
        "logs": execution.logs[-20:] if execution.logs else []  # Last 20 log entries
    }


@router.post("/recovery/test/{plan_id}", summary="Test Recovery Plan")
async def test_recovery_plan(
    plan_id: str,
    current_user = Depends(get_current_user)
):
    """Test recovery plan readiness"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required for recovery operations"
        )
    
    recovery = get_disaster_recovery()
    if not recovery:
        raise HTTPException(
            status_code=503,
            detail="Disaster recovery service not available"
        )
    
    try:
        test_result = await recovery.test_recovery_plan(plan_id)
        
        if "error" in test_result:
            raise HTTPException(status_code=404, detail=test_result["error"])
        
        return test_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recovery plan test failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Recovery plan test failed: {str(e)}"
        )


# Scheduled backup endpoints
@router.get("/schedule/jobs", summary="List Scheduled Jobs")
async def list_scheduled_jobs(
    current_user = Depends(get_current_user)
):
    """List scheduled backup jobs"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required for schedule management"
        )
    
    scheduler = get_backup_scheduler()
    if not scheduler:
        raise HTTPException(
            status_code=503,
            detail="Backup scheduler service not available"
        )
    
    jobs = scheduler.get_all_jobs()
    
    return {
        "jobs": [
            {
                "job_id": job.job_id,
                "backup_type": job.backup_type.value,
                "schedule": job.schedule,
                "enabled": job.enabled,
                "last_run": job.last_run.isoformat() if job.last_run else None,
                "next_run": job.next_run.isoformat() if job.next_run else None,
                "run_count": job.run_count,
                "failure_count": job.failure_count,
                "consecutive_failures": job.consecutive_failures,
                "max_retries": job.max_retries
            }
            for job in jobs
        ]
    }


@router.get("/schedule/status", summary="Scheduler Status")
async def get_scheduler_status(
    current_user = Depends(get_current_user)
):
    """Get backup scheduler status"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required for schedule management"
        )
    
    scheduler = get_backup_scheduler()
    if not scheduler:
        raise HTTPException(
            status_code=503,
            detail="Backup scheduler service not available"
        )
    
    return scheduler.get_job_status()


@router.post("/schedule/trigger/{job_id}", summary="Trigger Scheduled Job")
async def trigger_scheduled_job(
    job_id: str,
    current_user = Depends(get_current_user)
):
    """Manually trigger a scheduled job"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required for schedule management"
        )
    
    scheduler = get_backup_scheduler()
    if not scheduler:
        raise HTTPException(
            status_code=503,
            detail="Backup scheduler service not available"
        )
    
    success = await scheduler.trigger_job(job_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Scheduled job not found"
        )
    
    return {"message": f"Job {job_id} triggered successfully"}


@router.put("/schedule/jobs/{job_id}", summary="Update Scheduled Job")
async def update_scheduled_job(
    job_id: str,
    updates: Dict[str, Any],
    current_user = Depends(get_current_user)
):
    """Update a scheduled job"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required for schedule management"
        )
    
    scheduler = get_backup_scheduler()
    if not scheduler:
        raise HTTPException(
            status_code=503,
            detail="Backup scheduler service not available"
        )
    
    success = scheduler.update_job(job_id, updates)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Scheduled job not found"
        )
    
    return {"message": f"Job {job_id} updated successfully"}


@router.get("/schedule/history/{job_id}", summary="Job Execution History")
async def get_job_history(
    job_id: str,
    days: int = Query(30, ge=1, le=365, description="Days of history to include"),
    current_user = Depends(get_current_user)
):
    """Get job execution history"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required for schedule management"
        )
    
    scheduler = get_backup_scheduler()
    if not scheduler:
        raise HTTPException(
            status_code=503,
            detail="Backup scheduler service not available"
        )
    
    history = scheduler.get_job_history(job_id, days)
    
    return {
        "job_id": job_id,
        "period_days": days,
        "executions": history
    }


# Monitoring and alerting endpoints
@router.get("/alerts", summary="Get Backup Alerts")
async def get_backup_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    unresolved_only: bool = Query(False, description="Show only unresolved alerts"),
    current_user = Depends(get_current_user)
):
    """Get backup system alerts"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required for alert management"
        )
    
    monitoring = get_backup_monitoring()
    if not monitoring:
        raise HTTPException(
            status_code=503,
            detail="Backup monitoring service not available"
        )
    
    alerts = monitoring.get_alerts(severity, alert_type, unresolved_only)
    
    return {
        "alerts": [
            {
                "alert_id": alert.alert_id,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "title": alert.title,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "acknowledged": alert.acknowledged,
                "resolved": alert.resolved,
                "backup_id": alert.backup_id,
                "job_id": alert.job_id
            }
            for alert in alerts
        ]
    }


@router.post("/alerts/{alert_id}/acknowledge", summary="Acknowledge Alert")
async def acknowledge_alert(
    alert_id: str,
    current_user = Depends(get_current_user)
):
    """Acknowledge a backup alert"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required for alert management"
        )
    
    monitoring = get_backup_monitoring()
    if not monitoring:
        raise HTTPException(
            status_code=503,
            detail="Backup monitoring service not available"
        )
    
    success = monitoring.acknowledge_alert(alert_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Alert not found"
        )
    
    return {"message": f"Alert {alert_id} acknowledged"}


@router.post("/alerts/{alert_id}/resolve", summary="Resolve Alert")
async def resolve_alert(
    alert_id: str,
    current_user = Depends(get_current_user)
):
    """Resolve a backup alert"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required for alert management"
        )
    
    monitoring = get_backup_monitoring()
    if not monitoring:
        raise HTTPException(
            status_code=503,
            detail="Backup monitoring service not available"
        )
    
    success = monitoring.resolve_alert(alert_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Alert not found"
        )
    
    return {"message": f"Alert {alert_id} resolved"}


@router.get("/reports/{report_type}", summary="Generate Backup Report")
async def generate_backup_report(
    report_type: str,
    period_start: Optional[datetime] = Query(None, description="Report period start"),
    period_end: Optional[datetime] = Query(None, description="Report period end"),
    current_user = Depends(get_current_user)
):
    """Generate backup system report"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required for report generation"
        )
    
    monitoring = get_backup_monitoring()
    if not monitoring:
        raise HTTPException(
            status_code=503,
            detail="Backup monitoring service not available"
        )
    
    try:
        report = await monitoring.generate_report(report_type, period_start, period_end)
        return report.dict()
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(e)}"
        )