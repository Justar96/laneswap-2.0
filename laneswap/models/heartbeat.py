"""
Models for heartbeat monitoring.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, UTC
from pydantic import BaseModel, Field

from ..core.types import HeartbeatStatus


class HeartbeatEvent(BaseModel):
    """Represents a single heartbeat event."""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: HeartbeatStatus
    message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ServiceRegistration(BaseModel):
    """Model for service registration."""
    service_id: Optional[str] = None  # If None, will be auto-generated
    service_name: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ServiceHeartbeat(BaseModel):
    """Model for heartbeat updates."""
    status: HeartbeatStatus = HeartbeatStatus.HEALTHY
    message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ServiceStatus(BaseModel):
    """Model for service status response."""
    id: str
    name: str
    status: HeartbeatStatus
    message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_heartbeat: Optional[datetime] = None
    events: List[Dict[str, Any]] = Field(default_factory=list)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class MultiServiceStatus(BaseModel):
    """Model for multiple service statuses response."""
    services: Dict[str, ServiceStatus]
    summary: Dict[str, Any] = Field(default_factory=dict)


class ServiceRegistrationResponse(BaseModel):
    """Response model for service registration."""
    service_id: str