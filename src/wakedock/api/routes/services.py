"""
Service management endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from wakedock.config import ServiceSettings, get_settings
from wakedock.core.orchestrator import DockerOrchestrator
from wakedock.api.dependencies import get_orchestrator

router = APIRouter()


class ServiceResponse(BaseModel):
    id: str
    name: str
    subdomain: str
    status: str
    docker_image: Optional[str] = None
    docker_compose: Optional[str] = None
    ports: List[str] = []
    created_at: datetime
    updated_at: datetime
    last_accessed: Optional[datetime] = None
    resource_usage: Optional[Dict[str, Any]] = None


class ServiceCreateRequest(BaseModel):
    name: str
    subdomain: str
    docker_image: Optional[str] = None
    docker_compose: Optional[str] = None
    ports: List[str] = []
    environment: Dict[str, str] = {}
    auto_shutdown: Optional[Dict[str, Any]] = None
    loading_page: Optional[Dict[str, Any]] = None


class ServiceUpdateRequest(BaseModel):
    name: Optional[str] = None
    subdomain: Optional[str] = None
    docker_image: Optional[str] = None
    docker_compose: Optional[str] = None
    ports: Optional[List[str]] = None
    environment: Optional[Dict[str, str]] = None
    auto_shutdown: Optional[Dict[str, Any]] = None
    loading_page: Optional[Dict[str, Any]] = None


@router.get("", response_model=List[ServiceResponse])
async def list_services(orchestrator: DockerOrchestrator = Depends(get_orchestrator)):
    """List all services"""
    try:
        services = await orchestrator.list_services()
        return services
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list services: {str(e)}"
        )


@router.post("", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    service_data: ServiceCreateRequest,
    orchestrator: DockerOrchestrator = Depends(get_orchestrator)
):
    """Create a new service"""
    try:
        service = await orchestrator.create_service(service_data.dict())
        return service
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create service: {str(e)}"
        )


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: str,
    orchestrator: DockerOrchestrator = Depends(get_orchestrator)
):
    """Get service details"""
    try:
        service = await orchestrator.get_service(service_id)
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
        return service
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service: {str(e)}"
        )


@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: str,
    service_data: ServiceUpdateRequest,
    orchestrator: DockerOrchestrator = Depends(get_orchestrator)
):
    """Update service configuration"""
    try:
        service = await orchestrator.update_service(service_id, service_data.dict(exclude_unset=True))
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
        return service
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update service: {str(e)}"
        )


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: str,
    orchestrator: DockerOrchestrator = Depends(get_orchestrator)
):
    """Delete a service"""
    try:
        success = await orchestrator.delete_service(service_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete service: {str(e)}"
        )


@router.post("/{service_id}/wake", response_model=Dict[str, str])
async def wake_service(
    service_id: str,
    orchestrator: DockerOrchestrator = Depends(get_orchestrator)
):
    """Force wake up a service"""
    try:
        success = await orchestrator.wake_service(service_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
        return {"message": "Service wake up initiated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to wake service: {str(e)}"
        )


@router.post("/{service_id}/sleep", response_model=Dict[str, str])
async def sleep_service(
    service_id: str,
    orchestrator: DockerOrchestrator = Depends(get_orchestrator)
):
    """Force sleep a service"""
    try:
        success = await orchestrator.sleep_service(service_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
        return {"message": "Service sleep initiated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sleep service: {str(e)}"
        )


@router.post("/{service_id}/restart", response_model=Dict[str, str])
async def restart_service(
    service_id: str,
    orchestrator: DockerOrchestrator = Depends(get_orchestrator)
):
    """Restart a service"""
    try:
        success = await orchestrator.restart_service(service_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found or failed to restart"
            )
        return {"message": "Service restart initiated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart service: {str(e)}"
        )


@router.get("/{service_id}/status")
async def get_service_status(
    service_id: str,
    orchestrator: DockerOrchestrator = Depends(get_orchestrator)
):
    """Get service status"""
    try:
        service = await orchestrator.get_service(service_id)
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
        
        is_running = await orchestrator.is_service_running(service_id)
        
        return {
            "service_id": service_id,
            "name": service["name"],
            "status": service["status"],
            "is_running": is_running,
            "last_accessed": service.get("last_accessed"),
            "updated_at": service.get("updated_at")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service status: {str(e)}"
        )


@router.get("/{service_id}/stats")
async def get_service_stats(
    service_id: str,
    orchestrator: DockerOrchestrator = Depends(get_orchestrator)
):
    """Get service resource usage statistics"""
    try:
        stats = await orchestrator.get_service_stats(service_id)
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found or not running"
            )
        return stats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service stats: {str(e)}"
        )


@router.get("/{service_id}/logs")
async def get_service_logs(
    service_id: str,
    tail: int = 100,
    since: Optional[str] = None,
    orchestrator: DockerOrchestrator = Depends(get_orchestrator)
):
    """Get service logs"""
    try:
        service = await orchestrator.get_service(service_id)
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
        
        container_id = service.get("container_id")
        if not container_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Service is not running"
            )
        
        logs = await orchestrator.get_container_logs(container_id, tail=tail, since=since)
        if logs is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Container not found or logs unavailable"
            )
        
        return {
            "service_id": service_id,
            "container_id": container_id,
            "logs": logs,
            "tail": tail,
            "since": since
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service logs: {str(e)}"
        )


# Container management endpoints
@router.get("/containers/", response_model=List[Dict[str, Any]])
async def list_containers(
    all_containers: bool = False,
    orchestrator: DockerOrchestrator = Depends(get_orchestrator)
):
    """List all Docker containers"""
    try:
        containers = await orchestrator.list_containers(all_containers=all_containers)
        return containers
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list containers: {str(e)}"
        )


@router.get("/containers/{container_id}", response_model=Dict[str, Any])
async def get_container_details(
    container_id: str,
    orchestrator: DockerOrchestrator = Depends(get_orchestrator)
):
    """Get detailed information about a container"""
    try:
        container = await orchestrator.get_container_details(container_id)
        if not container:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Container not found"
            )
        return container
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get container details: {str(e)}"
        )


@router.post("/containers/{container_id}/start", response_model=Dict[str, str])
async def start_container(
    container_id: str,
    orchestrator: DockerOrchestrator = Depends(get_orchestrator)
):
    """Start a container"""
    try:
        success = await orchestrator.start_container(container_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Container not found or failed to start"
            )
        return {"message": "Container start initiated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start container: {str(e)}"
        )


@router.post("/containers/{container_id}/stop", response_model=Dict[str, str])
async def stop_container(
    container_id: str,
    orchestrator: DockerOrchestrator = Depends(get_orchestrator)
):
    """Stop a container"""
    try:
        success = await orchestrator.stop_container(container_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Container not found or failed to stop"
            )
        return {"message": "Container stop initiated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop container: {str(e)}"
        )


@router.post("/containers/{container_id}/restart", response_model=Dict[str, str])
async def restart_container(
    container_id: str,
    orchestrator: DockerOrchestrator = Depends(get_orchestrator)
):
    """Restart a container"""
    try:
        success = await orchestrator.restart_container(container_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Container not found or failed to restart"
            )
        return {"message": "Container restart initiated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart container: {str(e)}"
        )


@router.delete("/containers/{container_id}", response_model=Dict[str, str])
async def remove_container(
    container_id: str,
    force: bool = False,
    orchestrator: DockerOrchestrator = Depends(get_orchestrator)
):
    """Remove a container"""
    try:
        success = await orchestrator.remove_container(container_id, force=force)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Container not found or failed to remove"
            )
        return {"message": "Container removal initiated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove container: {str(e)}"
        )


@router.get("/containers/{container_id}/logs")
async def get_container_logs(
    container_id: str,
    tail: int = 100,
    since: Optional[str] = None,
    orchestrator: DockerOrchestrator = Depends(get_orchestrator)
):
    """Get container logs"""
    try:
        logs = await orchestrator.get_container_logs(container_id, tail=tail, since=since)
        if logs is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Container not found or logs unavailable"
            )
        
        return {
            "container_id": container_id,
            "logs": logs,
            "tail": tail,
            "since": since
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get container logs: {str(e)}"
        )


@router.get("/containers/{container_id}/stats")
async def get_container_stats(
    container_id: str,
    orchestrator: DockerOrchestrator = Depends(get_orchestrator)
):
    """Get container resource usage statistics"""
    try:
        stats = await orchestrator.get_container_stats(container_id)
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Container not found or stats unavailable"
            )
        return stats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get container stats: {str(e)}"
        )


# Docker system endpoints
@router.get("/images/", response_model=List[Dict[str, Any]])
async def list_images(
    orchestrator: DockerOrchestrator = Depends(get_orchestrator)
):
    """List all Docker images"""
    try:
        images = await orchestrator.list_images()
        return images
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list images: {str(e)}"
        )


@router.post("/images/pull", response_model=Dict[str, str])
async def pull_image(
    image_name: str,
    tag: str = "latest",
    orchestrator: DockerOrchestrator = Depends(get_orchestrator)
):
    """Pull a Docker image"""
    try:
        success = await orchestrator.pull_image(image_name, tag)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to pull image"
            )
        return {"message": f"Image {image_name}:{tag} pull initiated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pull image: {str(e)}"
        )


@router.delete("/images/{image_id}", response_model=Dict[str, str])
async def remove_image(
    image_id: str,
    force: bool = False,
    orchestrator: DockerOrchestrator = Depends(get_orchestrator)
):
    """Remove a Docker image"""
    try:
        success = await orchestrator.remove_image(image_id, force=force)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found or failed to remove"
            )
        return {"message": "Image removal initiated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove image: {str(e)}"
        )


@router.get("/networks/", response_model=List[Dict[str, Any]])
async def list_networks(
    orchestrator: DockerOrchestrator = Depends(get_orchestrator)
):
    """List all Docker networks"""
    try:
        networks = await orchestrator.list_networks()
        return networks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list networks: {str(e)}"
        )


@router.get("/volumes/", response_model=List[Dict[str, Any]])
async def list_volumes(
    orchestrator: DockerOrchestrator = Depends(get_orchestrator)
):
    """List all Docker volumes"""
    try:
        volumes = await orchestrator.list_volumes()
        return volumes
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list volumes: {str(e)}"
        )


@router.get("/system/info")
async def get_docker_system_info(
    orchestrator: DockerOrchestrator = Depends(get_orchestrator)
):
    """Get Docker system information"""
    try:
        info = await orchestrator.get_docker_system_info()
        return info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Docker system info: {str(e)}"
        )
