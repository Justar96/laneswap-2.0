"""
Health check router for the LaneSwap API.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request 
from pydantic import ValidationError

from ...laneswap import LaneSwap
from ...core.exceptions import ServiceNotFoundError, LaneSwapError 
from ...models.heartbeat import (
    HeartbeatStatus,
    MultiServiceStatus,
    ServiceHeartbeat,
    ServiceRegistration,
    ServiceRegistrationResponse,
    ServiceStatus,
)

router = APIRouter()
logger = logging.getLogger("laneswap.api.heartbeat")


def get_laneswap(request: Request) -> LaneSwap:
    """Dependency to get the LaneSwap instance from application state."""
    laneswap_instance = getattr(request.app.state, 'laneswap', None)
    if laneswap_instance is None:
        logger.critical("LaneSwap instance not found in application state.")
        raise HTTPException(
            status_code=500,
            detail="Internal server error: LaneSwap system not initialized correctly."
        )
    return laneswap_instance


@router.post(
    "/services",
    response_model=ServiceRegistrationResponse,
    summary="Register a new service"
)
async def register_service(
    service: ServiceRegistration,
    laneswap: LaneSwap = Depends(get_laneswap) 
):
    """Register a new service for heartbeat monitoring."""
    try:
        logger.debug("Registering service: %s", service.model_dump(exclude_none=True))
        registration_details = await laneswap.register(
            service_name=service.service_name,
            service_id=service.service_id,
            metadata=service.metadata
        )
        logger.info("Service registered successfully with ID: %s", registration_details.service_id)
        return {"service_id": registration_details.service_id}
    except (ValueError, LaneSwapError) as e: 
        logger.warning(f"Failed to register service '{service.service_name}': {e}")
        status_code = 400 if isinstance(e, ValueError) else 500
        raise HTTPException(status_code=status_code, detail=f"Failed to register service: {e}")
    except Exception as e:
        logger.error("Unexpected error registering service: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during registration.")


@router.post(
    "/services/{service_id}/heartbeat",
    response_model=Dict[str, Any],
    summary="Send a heartbeat for a service"
)
async def send_heartbeat(
    service_id: str = Path(..., description="Service identifier"),
    heartbeat: ServiceHeartbeat = ServiceHeartbeat(),
    laneswap: LaneSwap = Depends(get_laneswap) 
):
    """
    Send a heartbeat update for a registered service.

    Args:
        service_id: Service identifier
        heartbeat: Heartbeat information

    Returns:
        Confirmation message or Updated service status
    """
    try:
        success = await laneswap.send_heartbeat(
            service_id=service_id,
            status=heartbeat.status,
            message=heartbeat.message,
            metadata=heartbeat.metadata
        )

        return {"message": "Heartbeat received successfully", "service_id": service_id, "status": heartbeat.status}

    except ServiceNotFoundError as e:
        logger.warning(f"Heartbeat received for unknown service ID '{service_id}': {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Error processing heartbeat for service '%s': %s", service_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process heartbeat: {e}")


@router.get(
    "/services/{service_id}",
    response_model=ServiceStatus,
    summary="Get service status"
)
async def get_service_status(
    service_id: str = Path(..., description="Service identifier"),
    laneswap: LaneSwap = Depends(get_laneswap) 
):
    """
    Get the current status of a registered service.

    Args:
        service_id: Service identifier

    Returns:
        Service status information
    """
    try:
        service = await laneswap.get_service(service_id)
        if service is None:
             raise ServiceNotFoundError(f"Service with ID '{service_id}' not found.")

        if isinstance(service.get("last_heartbeat_time"), datetime):
            service["last_heartbeat_time"] = service["last_heartbeat_time"].isoformat()
        if isinstance(service.get("registration_time"), datetime):
             service["registration_time"] = service["registration_time"].isoformat()

        try:
            return ServiceStatus(**service)
        except ValidationError as ve:
             logger.error(f"Validation error creating ServiceStatus response for {service_id}: {ve}")
             raise HTTPException(status_code=500, detail="Internal data format error.")

    except ServiceNotFoundError as e:
        logger.info(f"Service status requested for unknown ID '{service_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Error getting service status for '%s': %s", service_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get service status: {e}")


@router.get(
    "/services",
    response_model=MultiServiceStatus, 
    summary="Get all services status"
)
async def get_all_services(
    laneswap: LaneSwap = Depends(get_laneswap) 
):
    """
    Get status information for all registered services.

    Returns:
        MultiServiceStatus: Object containing services data and summary statistics
    """
    try:
        services_dict = await laneswap.get_all_services()

        service_status_list: List[ServiceStatus] = []
        status_counts = {status.value: 0 for status in HeartbeatStatus}
        total_services = 0

        for service_id, service_data in services_dict.items():
            total_services += 1
            current_status = service_data.get("status", HeartbeatStatus.UNKNOWN)
            if isinstance(current_status, HeartbeatStatus):
                 status_value = current_status.value
            else: 
                 try:
                     status_value = HeartbeatStatus(current_status).value
                 except ValueError:
                     status_value = HeartbeatStatus.UNKNOWN.value
                     logger.warning(f"Service {service_id} has invalid status '{current_status}', treating as UNKNOWN.")
            status_counts[status_value] = status_counts.get(status_value, 0) + 1

            if isinstance(service_data.get("last_heartbeat_time"), datetime):
                service_data["last_heartbeat_time"] = service_data["last_heartbeat_time"].isoformat()
            if isinstance(service_data.get("registration_time"), datetime):
                service_data["registration_time"] = service_data["registration_time"].isoformat()

            try:
                service_status_list.append(ServiceStatus(**service_data))
            except ValidationError as ve:
                logger.error(f"Validation error creating ServiceStatus for service {service_id} in get_all_services: {ve}")
                continue

        return MultiServiceStatus(
            services=service_status_list,
            summary={
                "total": total_services,
                "status_counts": status_counts
            }
        )

    except Exception as e:
        logger.error("Error getting all services: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get services: {e}")
