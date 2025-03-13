"""
Models for error handling.
"""

import time
from datetime import UTC, datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ErrorLog(BaseModel):
    """Model for error logs."""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
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
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    details: Optional[Dict[str, Any]] = None


class ValidationError(BaseModel):
    """Model for validation errors."""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    field: str
    error: str
    value: str
