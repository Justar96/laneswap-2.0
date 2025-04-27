"""
LaneSwap - A heartbeat monitoring system for distributed services.

LaneSwap provides tools for monitoring the health of distributed services
through heartbeats, with support for various storage backends and notification
channels.
"""

__version__ = "2.0.0"

# Core types
from .core.types import HeartbeatStatus

# Adapter base classes
from .adapters.base import NotifierAdapter, StorageAdapter

# Concrete adapters
from .adapters.discord import DiscordWebhookAdapter
from .adapters.mongodb import MongoDBAdapter

# Core exceptions
from .core.exceptions import LaneSwapError, ServiceNotFoundError

# Model exports
from .models.error import ErrorLog, ErrorResponse
from .models.heartbeat import (
    HeartbeatEvent,
    ServiceHeartbeat,
    ServiceRegistration,
    ServiceStatus,
)
from .laneswap import LaneSwap

__all__ = [
    # Core
    "HeartbeatStatus",
    "LaneSwapError",
    "ServiceNotFoundError",
    "LaneSwap",

    # Models
    "ServiceRegistration",
    "ServiceHeartbeat",
    "ServiceStatus",
    "HeartbeatEvent",
    "ErrorLog",
    "ErrorResponse",

    # Adapters
    "NotifierAdapter",
    "StorageAdapter",
    "MongoDBAdapter",
    "DiscordWebhookAdapter",
]

# Configure logging for the library
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
