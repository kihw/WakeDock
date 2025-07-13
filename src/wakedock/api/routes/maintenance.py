"""
Maintenance API endpoints for backup, restore, cleanup and configuration management
"""

from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

from wakedock.api.dependencies import get_orchestrator
from wakedock.core.orchestrator import DockerOrchestrator

router = APIRouter()


class BackupType(str, Enum):
    """Types of backup supported"""
    FULL = "full"
    DATABASE = "database"
    CONFIG = "config"
    VOLUMES = "volumes"


class BackupRequest(BaseModel):
    """Request model for creating a backup"""
    type: BackupType = Field(..., description="Type of backup to create")
    include_volumes: bool = Field(True, description="Include Docker volumes in backup")
    include_config: bool = Field(True, description="Include configuration files")
    include_database: bool = Field(True, description="Include database in backup")
    compression: bool = Field(True, description="Compress backup archive")
    retention_days: int = Field(7, ge=1, le=365, description="Days to retain backup")


class BackupInfo(BaseModel):
    """Information about a backup"""
    id: str
    name: str
    type: BackupType
    size: int
    created_at: datetime
    status: str
    file_path: str
    metadata: Dict[str, Any]


class RestoreOptions(BaseModel):
    """Options for restore operation"""
    backup_id: str = Field(..., description="Backup ID to restore from")
    force: bool = Field(False, description="Force restore without confirmation")
    database_only: bool = Field(False, description="Restore only database")
    config_only: bool = Field(False, description="Restore only configuration")
    no_restart: bool = Field(False, description="Don't restart services after restore")


class CleanupRequest(BaseModel):
    """Request for cleanup operations"""
    docker_resources: bool = Field(True, description="Clean Docker unused resources")
    log_files: bool = Field(True, description="Clean old log files")
    temp_files: bool = Field(True, description="Clean temporary files")
    max_age_days: int = Field(7, ge=1, le=90, description="Maximum age for files to keep")


class CleanupReport(BaseModel):
    """Report of cleanup operations"""
    docker_cleanup: Dict[str, Any]
    log_cleanup: Dict[str, Any]
    temp_cleanup: Dict[str, Any]
    space_freed: int
    summary: str


@router.post("/backup", response_model=BackupInfo, status_code=status.HTTP_201_CREATED)
async def create_backup(
    backup_request: BackupRequest,
    orchestrator: DockerOrchestrator = Depends(get_orchestrator)
):
    """Create a new backup"""
    try:
        # Import here to avoid circular imports
        from wakedock.maintenance.backup_service import BackupService
        
        backup_service = BackupService(orchestrator)
        backup_info = await backup_service.create_backup(
            backup_type=backup_request.type.value,
            include_volumes=backup_request.include_volumes,
            include_config=backup_request.include_config,
            include_database=backup_request.include_database,
            compression=backup_request.compression
        )
        
        return backup_info
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create backup: {str(e)}"
        )


@router.get("/backups", response_model=List[BackupInfo])
async def list_backups():
    """List all available backups"""
    try:
        from wakedock.maintenance.backup_service import BackupService
        
        backup_service = BackupService()
        backups = await backup_service.list_backups()
        return backups
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list backups: {str(e)}"
        )


@router.post("/restore")
async def restore_backup(
    backup_file: UploadFile = File(...),
    options: str = Form(...),  # JSON string of RestoreOptions
    orchestrator: DockerOrchestrator = Depends(get_orchestrator)
):
    """Restore from backup file"""
    try:
        import json
        from wakedock.maintenance.backup_service import BackupService
        
        # Parse options
        restore_options = RestoreOptions.parse_raw(options)
        
        backup_service = BackupService(orchestrator)
        result = await backup_service.restore_backup(
            backup_file=backup_file,
            options=restore_options.dict()
        )
        
        return {
            "success": True,
            "message": "Restore completed successfully",
            "details": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore backup: {str(e)}"
        )


@router.delete("/backups/{backup_id}")
async def delete_backup(backup_id: str):
    """Delete a specific backup"""
    try:
        from wakedock.maintenance.backup_service import BackupService
        
        backup_service = BackupService()
        await backup_service.delete_backup(backup_id)
        
        return {"success": True, "message": f"Backup {backup_id} deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete backup: {str(e)}"
        )


@router.post("/cleanup", response_model=CleanupReport)
async def cleanup_system(
    cleanup_request: CleanupRequest,
    orchestrator: DockerOrchestrator = Depends(get_orchestrator)
):
    """Clean up system resources"""
    try:
        from wakedock.maintenance.cleanup_service import CleanupService
        
        cleanup_service = CleanupService(orchestrator)
        report = await cleanup_service.cleanup_system(
            docker_resources=cleanup_request.docker_resources,
            log_files=cleanup_request.log_files,
            temp_files=cleanup_request.temp_files,
            max_age_days=cleanup_request.max_age_days
        )
        
        return report
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup system: {str(e)}"
        )


@router.get("/dependencies")
async def check_dependencies():
    """Check system dependencies status"""
    try:
        from wakedock.maintenance.dependencies_service import DependenciesService
        
        deps_service = DependenciesService()
        status_info = await deps_service.check_dependencies()
        
        return status_info
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check dependencies: {str(e)}"
        )


@router.post("/dependencies/update")
async def update_dependencies(component: Optional[str] = None):
    """Update system dependencies"""
    try:
        from wakedock.maintenance.dependencies_service import DependenciesService
        
        deps_service = DependenciesService()
        result = await deps_service.update_dependencies(component)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update dependencies: {str(e)}"
        )


@router.get("/config/validate")
async def validate_configuration():
    """Validate system configuration"""
    try:
        from wakedock.maintenance.config_service import ConfigService
        
        config_service = ConfigService()
        validation_result = await config_service.validate_full_config()
        
        return validation_result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate configuration: {str(e)}"
        )


@router.post("/config/fix")
async def fix_configuration(auto_fix: bool = True):
    """Fix configuration issues"""
    try:
        from wakedock.maintenance.config_service import ConfigService
        
        config_service = ConfigService()
        fix_result = await config_service.fix_config_issues(auto_fix=auto_fix)
        
        return fix_result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fix configuration: {str(e)}"
        )
