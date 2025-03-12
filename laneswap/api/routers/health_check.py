"""
Health check router for the LaneSwap API.
"""

from datetime import datetime, UTC
from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/health",
    summary="Health check endpoint"
)
async def health_check():
    """
    Simple health check endpoint that returns the service status.
    
    Returns:
        dict: Health check response containing status and timestamp
    """
    return {
        "status": "ok",
        "service": "LaneSwap API",
        "timestamp": datetime.now(UTC).isoformat()
    }