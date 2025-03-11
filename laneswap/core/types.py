"""
Common types used across the LaneSwap system.
"""

from enum import Enum
from typing import Dict, Any, Optional, List, Union, Callable
from datetime import datetime

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