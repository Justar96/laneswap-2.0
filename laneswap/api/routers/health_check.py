from fastapi import APIRouter, Response
from datetime import datetime, timezone

router = APIRouter()


@router.get("/health", summary="Health check endpoint")
async def health_check():
    """
    Simple health check endpoint to verify the API is running.
    
    Returns:
        dict: Basic health information
    """
    return {
        "status": "ok",
        "service": "laneswap",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }