"""
Heartbeat manager and utilities for LaneSwap.
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, Optional, Callable, TypeVar, Coroutine

from .types import HeartbeatStatus
from .exceptions import ServiceNotFoundError

logger = logging.getLogger(__name__)

# Singleton manager instance
_manager: Optional["HeartbeatManager"] = None


def get_manager():
    """Get or create the global HeartbeatManager instance."""
    global _manager
    if _manager is None:
        _manager = HeartbeatManager()
    return _manager


def with_heartbeat(service_id: str):
    """Decorator to send a heartbeat after successful function execution."""
    def decorator(func: Callable[..., Coroutine[Any, Any, Any]]):
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            await get_manager().send_heartbeat(
                service_id=service_id,
                status=HeartbeatStatus.HEALTHY
            )
            return result
        return wrapper
    return decorator


class HeartbeatManager:
    """Manager for service heartbeats."""

    def __init__(self):
        # service_id -> service data
        self._services: Dict[str, Dict[str, Any]] = {}
        self._monitor_running: bool = False

    async def register_service(
        self,
        service_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Register a new service and return its ID."""
        service_id = str(uuid.uuid4())
        self._services[service_id] = {
            "id": service_id,
            "name": service_name,
            "status": None,
            "message": None,
            "metadata": metadata or {},
            "events": [],
        }
        return service_id

    async def get_service(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve service data by ID."""
        return self._services.get(service_id)

    async def send_heartbeat(
        self,
        service_id: str,
        status: Any = HeartbeatStatus.HEALTHY,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send a heartbeat for the given service."""
        service = self._services.get(service_id)
        if service is None:
            raise ServiceNotFoundError(f"Service {service_id} not found")
        # Normalize status
        status_value = status.value if isinstance(status, HeartbeatStatus) else status
        service["status"] = status_value
        service["message"] = message
        if metadata is not None:
            service["metadata"] = metadata
        # Record event
        service["events"].append({
            "status": status_value,
            "message": message,
            "metadata": metadata or {},
        })
        return True

    async def start_monitor(self) -> None:
        """Start the background heartbeat monitor."""
        self._monitor_running = True

    async def stop_monitor(self) -> None:
        """Stop the background heartbeat monitor."""
        self._monitor_running = False


async def generate_monitor_url(
    service_id: str,
    api_url: str
) -> str:
    """Generate a URL for the web monitor of a service."""
    # Simple URL generation; adjust as needed
    return f"{api_url}/monitor/{service_id}"
