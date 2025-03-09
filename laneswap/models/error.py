from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ErrorLog(BaseModel):
    """Model for error logs."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    service_id: Optional[str] = None
    error_type: str
    message: str
    traceback: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Model for API error responses."""
    status_code: int
    error: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[Dict[str, Any]] = None