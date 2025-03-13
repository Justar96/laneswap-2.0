"""
Common types used across the LaneSwap system.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Callable, List, Optional, Union


class HeartbeatStatus(str, Enum):
    """Enum representing possible service health statuses."""
    HEALTHY = "healthy"
    WARNING = "warning"
    DEGRADED = "degraded"
    ERROR = "error"
    BUSY = "busy"
    STALE = "stale"
    UNKNOWN = "unknown"

class ProgressStatus(str, Enum):
    """Status of a function execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELED = "canceled"
