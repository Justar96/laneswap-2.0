"""
LaneSwap - A heartbeat monitoring system for distributed services.

LaneSwap provides tools for monitoring the health of distributed services
through heartbeats, with support for various storage backends and notification
channels.
"""

__version__ = "0.1.2"

# Adapter base classes
from .adapters.base import NotifierAdapter, StorageAdapter

# Concrete adapters
from .adapters.discord import DiscordWebhookAdapter
from .adapters.mongodb import MongoDBAdapter

# Core exports
from .core.heartbeat import (
    HeartbeatManager,
    HeartbeatStatus,
    get_manager,
    with_heartbeat,
)
from .models.error import ErrorLog, ErrorResponse

# Model exports
from .models.heartbeat import (
    HeartbeatEvent,
    ServiceHeartbeat,
    ServiceRegistration,
    ServiceStatus,
)

__all__ = [
    # Core
    "HeartbeatManager",
    "get_manager",
    "with_heartbeat",
    "HeartbeatStatus",

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
