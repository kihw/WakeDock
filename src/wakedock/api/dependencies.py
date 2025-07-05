"""
FastAPI dependency injection for WakeDock services
"""

from fastapi import Depends, HTTPException, status, Request
from typing import Optional
from sqlalchemy.orm import Session

from wakedock.core.orchestrator import DockerOrchestrator
from wakedock.core.monitoring import MonitoringService
from wakedock.infrastructure.cache.service import CacheService
from wakedock.database.database import get_db_session


def get_orchestrator(request: Request) -> DockerOrchestrator:
    """Dependency to get orchestrator instance from app state"""
    orchestrator = getattr(request.app.state, 'orchestrator', None)
    if orchestrator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Docker orchestrator service is not available"
        )
    return orchestrator


def get_monitoring_service(request: Request) -> MonitoringService:
    """Dependency to get monitoring service instance from app state"""
    monitoring_service = getattr(request.app.state, 'monitoring_service', None)
    if monitoring_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Monitoring service is not available"
        )
    return monitoring_service


def get_db() -> Session:
    """Dependency to get database session"""
    return Depends(get_db_session)


def get_optional_orchestrator(request: Request) -> Optional[DockerOrchestrator]:
    """Dependency to get orchestrator instance that may be None"""
    return getattr(request.app.state, 'orchestrator', None)


def get_optional_monitoring_service(request: Request) -> Optional[MonitoringService]:
    """Dependency to get monitoring service that may be None"""
    return getattr(request.app.state, 'monitoring_service', None)


def get_cache_service_dep(request: Request) -> CacheService:
    """Dependency to get cache service instance from app state"""
    cache_service = getattr(request.app.state, 'cache_service', None)
    if cache_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cache service is not available"
        )
    return cache_service


def get_optional_cache_service(request: Request) -> Optional[CacheService]:
    """Dependency to get cache service that may be None"""
    return getattr(request.app.state, 'cache_service', None)
