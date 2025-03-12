"""
LaneSwap - A heartbeat monitoring system for distributed services.

LaneSwap provides tools for monitoring the health of distributed services
through heartbeats, with support for various storage backends and notification
channels.
"""

__version__ = "0.1.2"

# Core exports
from .core.heartbeat import (
    HeartbeatManager,
    get_manager,
    with_heartbeat,
    HeartbeatStatus
)

# Model exports
from .models.heartbeat import (
    ServiceRegistration,
    ServiceHeartbeat,
    ServiceStatus,
    HeartbeatEvent
)
from .models.error import ErrorLog, ErrorResponse

# Adapter base classes
from .adapters.base import NotifierAdapter, StorageAdapter

# Concrete adapters
from .adapters.mongodb import MongoDBAdapter
from .adapters.discord import DiscordWebhookAdapter

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
