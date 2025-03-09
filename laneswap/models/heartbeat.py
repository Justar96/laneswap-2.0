from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class HeartbeatStatus(str, Enum):
    """Enum representing possible service health statuses."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    ERROR = "error"
    BUSY = "busy"
    STALE = "stale"
    UNKNOWN = "unknown"


class HeartbeatEvent(BaseModel):
    """Represents a single heartbeat event."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
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
    last_heartbeat: Optional[datetime] = None
    last_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    events: List[Dict[str, Any]] = Field(default_factory=list)


class MultiServiceStatus(BaseModel):
    """Model for multiple service statuses response."""
    services: Dict[str, ServiceStatus]
    summary: Dict[str, int] = Field(default_factory=dict)