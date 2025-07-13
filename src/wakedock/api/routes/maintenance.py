"""
Maintenance API endpoints for backup, restore, cleanup and configuration management
"""

from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

from wakedock.api.dependencies import (
    get_backup_service, get_dependencies_service, 
    get_cleanup_service, get_config_service
)
from wakedock.maintenance import BackupService, DependenciesService, CleanupService, ConfigService

router = APIRouter()


class BackupType(str, Enum):
    """Types of backup supported"""
    FULL = "full"
    DATABASE = "database"
    CONFIG = "config"
    VOLUMES = "volumes"


class CleanupType(str, Enum):
    """Types of cleanup operations"""
    DOCKER = "docker_resources"
    LOGS = "logs"
    TEMP_FILES = "temp_files"


class DependencyCategory(str, Enum):
    """Dependency categories for checking/updating"""
    ALL = "all"
    PYTHON = "python"
    NODE = "node"
    DOCKER = "docker"
    SYSTEM = "system"


class BackupRequest(BaseModel):
    """Request model for creating backups"""
    backup_type: BackupType = Field(default=BackupType.FULL, description="Type of backup to create")
    include_volumes: bool = Field(default=True, description="Include Docker volumes in backup")
    include_config: bool = Field(default=True, description="Include configuration files in backup")
    include_database: bool = Field(default=True, description="Include database in backup")
    compression: bool = Field(default=True, description="Enable compression for backup")


class RestoreRequest(BaseModel):
    """Request model for restoring from backup"""
    database_only: bool = Field(default=False, description="Restore only database")
    config_only: bool = Field(default=False, description="Restore only configuration")


class CleanupRequest(BaseModel):
    """Request model for cleanup operations"""
    cleanup_type: CleanupType = Field(description="Type of cleanup to perform")
    force: bool = Field(default=False, description="Force cleanup of resources in use")
    options: Dict[str, Any] = Field(default_factory=dict, description="Additional cleanup options")


class DockerCleanupRequest(BaseModel):
    """Request model for Docker cleanup operations"""
    containers: bool = Field(default=True, description="Clean stopped containers")
    images: bool = Field(default=True, description="Clean unused images")
    volumes: bool = Field(default=False, description="Clean unused volumes")
    networks: bool = Field(default=True, description="Clean unused networks")
    build_cache: bool = Field(default=True, description="Clean build cache")
    force: bool = Field(default=False, description="Force cleanup")


class DependenciesUpdateRequest(BaseModel):
    """Request model for updating dependencies"""
    category: DependencyCategory = Field(default=DependencyCategory.ALL, description="Category of dependencies to update")


class BackupInfo(BaseModel):
    """Response model for backup information"""
    id: str
    name: str
    backup_type: str
    size: int
    created_at: datetime
    status: str
    metadata: Dict[str, Any]


class RestoreResult(BaseModel):
    """Response model for restore operations"""
    success: bool
    message: str
    restored_components: Dict[str, str]
    timestamp: str


class CleanupReport(BaseModel):
    """Response model for cleanup operations"""
    cleanup_type: str
    total_space_reclaimed: str
    details: Dict[str, Any]
    errors: List[str]
    timestamp: str


class DependencyStatus(BaseModel):
    """Response model for dependency status"""
    timestamp: str
    overall_status: str
    categories: Dict[str, Any]
    issues: List[str]


class MaintenanceStatus(BaseModel):
    """Overall maintenance status response"""
    status: str = Field(description="Overall maintenance status")
    timestamp: datetime = Field(description="Status check timestamp")
    services: Dict[str, Any] = Field(description="Status of each maintenance service")
    active_operations: List[str] = Field(description="Currently running maintenance operations")
    last_maintenance: Optional[datetime] = Field(description="Last maintenance operation timestamp")
    recommendations: List[str] = Field(description="Maintenance recommendations")


# Backup Endpoints

@router.post("/backup", response_model=BackupInfo, status_code=status.HTTP_201_CREATED)
async def create_backup(
    backup_request: BackupRequest,
    backup_service: BackupService = Depends(get_backup_service)
):
    """Create a new system backup"""
    try:
        result = await backup_service.create_backup(
            backup_type=backup_request.backup_type.value,
            include_volumes=backup_request.include_volumes,
            include_config=backup_request.include_config,
            include_database=backup_request.include_database,
            compression=backup_request.compression
        )
        
        return BackupInfo(
            id=result["id"],
            name=result["name"],
            backup_type=result["type"],
            size=result["size"],
            created_at=result["created_at"],
            status=result["status"],
            metadata=result["metadata"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup creation failed: {str(e)}"
        )


@router.get("/backups", response_model=List[BackupInfo])
async def list_backups(
    backup_service: BackupService = Depends(get_backup_service)
):
    """List all available backups"""
    try:
        backups = await backup_service.list_backups()
        return [
            BackupInfo(
                id=backup["id"],
                name=backup["name"],
                backup_type=backup["type"],
                size=backup["size"],
                created_at=backup["created_at"],
                status=backup["status"],
                metadata=backup["metadata"]
            )
            for backup in backups
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list backups: {str(e)}"
        )


@router.delete("/backup/{backup_id}")
async def delete_backup(
    backup_id: str,
    backup_service: BackupService = Depends(get_backup_service)
):
    """Delete a specific backup"""
    try:
        await backup_service.delete_backup(backup_id)
        return {"message": f"Backup {backup_id} deleted successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete backup: {str(e)}"
        )


@router.post("/restore", response_model=RestoreResult)
async def restore_backup(
    backup_file: UploadFile = File(...),
    options: RestoreRequest = Depends(),
    backup_service: BackupService = Depends(get_backup_service)
):
    """Restore system from backup file"""
    try:
        options_dict = {
            "database_only": options.database_only,
            "config_only": options.config_only
        }
        
        result = await backup_service.restore_backup(backup_file, options_dict)
        
        return RestoreResult(
            success=True,
            message="Restore completed successfully",
            restored_components=result["restored_components"],
            timestamp=result["timestamp"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Restore failed: {str(e)}"
        )


# Cleanup Endpoints

@router.post("/cleanup", response_model=CleanupReport)
async def cleanup_system(
    cleanup_request: CleanupRequest,
    cleanup_service: CleanupService = Depends(get_cleanup_service)
):
    """Perform system cleanup operations"""
    try:
        if cleanup_request.cleanup_type == CleanupType.DOCKER:
            result = await cleanup_service.cleanup_docker_resources(cleanup_request.options)
        elif cleanup_request.cleanup_type == CleanupType.LOGS:
            result = await cleanup_service.cleanup_logs(cleanup_request.options)
        elif cleanup_request.cleanup_type == CleanupType.TEMP_FILES:
            result = await cleanup_service.cleanup_temp_files(cleanup_request.options)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown cleanup type: {cleanup_request.cleanup_type}"
            )
        
        return CleanupReport(
            cleanup_type=result["cleanup_type"],
            total_space_reclaimed=result["summary"]["total_space_reclaimed"],
            details=result["details"],
            errors=result["errors"],
            timestamp=result["timestamp"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cleanup failed: {str(e)}"
        )


@router.post("/cleanup/docker", response_model=CleanupReport)
async def cleanup_docker_resources(
    cleanup_options: DockerCleanupRequest,
    cleanup_service: CleanupService = Depends(get_cleanup_service)
):
    """Perform Docker-specific cleanup operations"""
    try:
        # Convert request to options dict
        options = {
            "containers": cleanup_options.containers,
            "images": cleanup_options.images,
            "volumes": cleanup_options.volumes,
            "networks": cleanup_options.networks,
            "build_cache": cleanup_options.build_cache,
            "force": cleanup_options.force
        }
        
        result = await cleanup_service.cleanup_docker_resources(options)
        
        return CleanupReport(
            cleanup_type=result["cleanup_type"],
            total_space_reclaimed=result["summary"]["total_space_reclaimed"],
            details=result["details"],
            errors=result["errors"],
            timestamp=result["timestamp"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Docker cleanup failed: {str(e)}"
        )


@router.get("/cleanup/recommendations")
async def get_cleanup_recommendations(
    cleanup_service: CleanupService = Depends(get_cleanup_service)
):
    """Get system cleanup recommendations"""
    try:
        recommendations = await cleanup_service.get_cleanup_recommendations()
        return recommendations
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cleanup recommendations: {str(e)}"
        )


# Dependencies Endpoints

@router.get("/dependencies/check", response_model=DependencyStatus)
async def check_dependencies(
    dependencies_service: DependenciesService = Depends(get_dependencies_service)
):
    """Check all system dependencies"""
    try:
        status_result = await dependencies_service.check_dependencies()
        
        return DependencyStatus(
            timestamp=status_result["timestamp"],
            overall_status=status_result["overall_status"],
            categories=status_result["categories"],
            issues=status_result["issues"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check dependencies: {str(e)}"
        )


@router.post("/dependencies/update")
async def update_dependencies(
    update_request: DependenciesUpdateRequest,
    dependencies_service: DependenciesService = Depends(get_dependencies_service)
):
    """Update system dependencies"""
    try:
        result = await dependencies_service.update_dependencies(
            category=update_request.category.value
        )
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update dependencies: {str(e)}"
        )


@router.get("/dependencies/status/{dependency_type}")
async def get_dependency_status(
    dependency_type: str,
    dependencies_service: DependenciesService = Depends(get_dependencies_service)
):
    """Get status of specific dependency type"""
    try:
        result = await dependencies_service.get_dependency_status(dependency_type)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dependency status: {str(e)}"
        )


# Configuration Endpoints

@router.post("/config/validate")
async def validate_configuration(
    config_type: str = "all",
    config_service: ConfigService = Depends(get_config_service)
):
    """Validate system configuration"""
    try:
        result = await config_service.validate_configuration(config_type)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Configuration validation failed: {str(e)}"
        )


@router.post("/config/backup")
async def backup_configuration(
    backup_name: Optional[str] = None,
    config_service: ConfigService = Depends(get_config_service)
):
    """Create a backup of configuration files"""
    try:
        result = await config_service.backup_configuration(backup_name)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Configuration backup failed: {str(e)}"
        )


@router.post("/config/restore/{backup_name}")
async def restore_configuration(
    backup_name: str,
    config_service: ConfigService = Depends(get_config_service)
):
    """Restore configuration from backup"""
    try:
        result = await config_service.restore_configuration(backup_name)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Configuration restore failed: {str(e)}"
        )


@router.get("/config/backups")
async def list_configuration_backups(
    config_service: ConfigService = Depends(get_config_service)
):
    """List all configuration backups"""
    try:
        result = await config_service.list_configuration_backups()
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list configuration backups: {str(e)}"
        )


@router.get("/status", response_model=MaintenanceStatus)
async def get_maintenance_status(
    backup_service: BackupService = Depends(get_backup_service),
    dependencies_service: DependenciesService = Depends(get_dependencies_service),
    cleanup_service: CleanupService = Depends(get_cleanup_service),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Get overall maintenance status including all services
    """
    try:
        # Get individual service statuses
        backup_status = await backup_service.get_status()
        deps_status = await dependencies_service.get_status()
        cleanup_status = await cleanup_service.get_status()
        config_status = await config_service.get_status()
        
        # Determine overall status
        all_statuses = [backup_status, deps_status, cleanup_status, config_status]
        overall_status = "healthy" if all(status == "healthy" for status in all_statuses) else "warning"
        
        # Get active operations (simplified)
        active_operations = []
        if backup_status == "running":
            active_operations.append("backup")
        if cleanup_status == "running":
            active_operations.append("cleanup")
        
        # Get recommendations
        recommendations = []
        if deps_status == "outdated":
            recommendations.append("Dependencies need updates")
        if cleanup_status == "needed":
            recommendations.append("System cleanup recommended")
        
        return MaintenanceStatus(
            status=overall_status,
            timestamp=datetime.utcnow(),
            services={
                "backup": backup_status,
                "dependencies": deps_status,
                "cleanup": cleanup_status,
                "config": config_status
            },
            active_operations=active_operations,
            last_maintenance=datetime.utcnow() if active_operations else None,
            recommendations=recommendations
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get maintenance status: {str(e)}"
        )
