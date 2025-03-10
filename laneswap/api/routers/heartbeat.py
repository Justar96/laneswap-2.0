from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, Path, Query
from pydantic import ValidationError

from ...core.heartbeat import HeartbeatManager, get_manager
from ...models.heartbeat import (
    ServiceRegistration,
    ServiceHeartbeat,
    ServiceStatus,
    MultiServiceStatus,
    HeartbeatStatus,
    ServiceRegistrationResponse
)

router = APIRouter()


async def get_heartbeat_manager() -> HeartbeatManager:
    """Dependency to get the heartbeat manager instance."""
    return get_manager()


@router.post(
    "/services",
    response_model=ServiceRegistrationResponse,
    summary="Register a new service"
)
async def register_service(
    service: ServiceRegistration,
    manager: HeartbeatManager = Depends(get_manager)
):
    """Register a new service for heartbeat monitoring."""
    try:
        service_id = await manager.register_service(
            service_name=service.service_name,
            service_id=service.service_id,
            metadata=service.metadata
        )
        return {"service_id": service_id}
    except Exception as e:
        logger.error(f"Error registering service: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to register service: {str(e)}")


@router.post(
    "/services/{service_id}/heartbeat",
    response_model=ServiceStatus,
    summary="Send a heartbeat for a service"
)
async def send_heartbeat(
    service_id: str = Path(..., description="Service identifier"),
    heartbeat: ServiceHeartbeat = ServiceHeartbeat(),
    manager: HeartbeatManager = Depends(get_heartbeat_manager)
):
    """
    Send a heartbeat update for a registered service.
    
    Args:
        service_id: Service identifier
        heartbeat: Heartbeat information
        
    Returns:
        Updated service status
    """
    try:
        result = await manager.send_heartbeat(
            service_id=service_id,
            status=heartbeat.status,
            message=heartbeat.message,
            metadata=heartbeat.metadata
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process heartbeat: {str(e)}")


@router.get(
    "/services/{service_id}",
    response_model=ServiceStatus,
    summary="Get service status"
)
async def get_service_status(
    service_id: str = Path(..., description="Service identifier"),
    manager: HeartbeatManager = Depends(get_heartbeat_manager)
):
    """
    Get the current status of a registered service.
    
    Args:
        service_id: Service identifier
        
    Returns:
        Service status information
    """
    try:
        result = await manager.get_service_status(service_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get service status: {str(e)}")


@router.get(
    "/services",
    response_model=Dict[str, Any],
    summary="Get all services status"
)
async def get_all_services(
    manager: HeartbeatManager = Depends(get_heartbeat_manager)
):
    """
    Get status information for all registered services.
    
    Returns:
        Dictionary with services data and summary statistics
    """
    try:
        services = await manager.get_all_services()
        
        # Count services by status
        status_counts = {}
        for status in HeartbeatStatus:
            status_counts[status.value] = 0
            
        for service in services.values():
            status = service.get("status", HeartbeatStatus.UNKNOWN)
            if isinstance(status, HeartbeatStatus):
                status = status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "services": services,
            "summary": {
                "total": len(services),
                "status_counts": status_counts
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get services: {str(e)}")