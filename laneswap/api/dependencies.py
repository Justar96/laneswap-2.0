"""Dependency injection for the LaneSwap API."""

from fastapi import Depends, HTTPException, status
from typing import Optional

from ..core.heartbeat import HeartbeatManager, get_manager


async def get_heartbeat_manager() -> HeartbeatManager:
    """Dependency to get the heartbeat manager instance."""
    manager = get_manager()
    if not manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Heartbeat manager not initialized"
        )
    return manager


async def validate_service_exists(
    service_id: str,
    manager: HeartbeatManager = Depends(get_heartbeat_manager)
) -> str:
    """Validate that a service exists and return its ID."""
    service = await manager.get_service(service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service with ID {service_id} not found"
        )
    return service_id 