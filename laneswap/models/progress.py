"""
Models for progress tracking.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from ..core.types import ProgressStatus


class ExecutionStep(BaseModel):
    """Information about a step in a function execution."""
    timestamp: datetime
    description: str
    progress: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ErrorInfo(BaseModel):
    """Information about an error that occurred during function execution."""
    message: str
    type: str
    traceback: Optional[str] = None

class ExecutionSummary(BaseModel):
    """Summary information about a function execution."""
    id: str
    function: str
    status: ProgressStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ExecutionDetail(ExecutionSummary):
    """Detailed information about a function execution."""
    steps: List[ExecutionStep] = Field(default_factory=list)
    error: Optional[ErrorInfo] = None
    result: Optional[Any] = None

class ExecutionStatistics(BaseModel):
    """Statistics about function executions."""
    total: int
    status_counts: Dict[str, int] = Field(default_factory=dict)
    function_counts: Dict[str, int] = Field(default_factory=dict)
    avg_duration: float = 0
    success_rate: float = 0
