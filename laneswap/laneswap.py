"""
Facade for the LaneSwap service, providing a unified API over the HeartbeatManager.
"""
from typing import Optional, Dict, Any

from .core.heartbeat import get_manager
from .core.types import HeartbeatStatus
from .models.heartbeat import ServiceRegistrationResponse


class LaneSwap:
    """Facade class to expose heartbeat operations via a unified interface."""
    def __init__(self):
        self._manager = get_manager()

    async def register(
        self,
        service_name: str,
        service_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ServiceRegistrationResponse:
        """Register a new service and return its registration response."""
        sid = await self._manager.register_service(service_name=service_name, metadata=metadata)
        return ServiceRegistrationResponse(service_id=sid)

    async def send_heartbeat(
        self,
        service_id: str,
        status: HeartbeatStatus,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send a heartbeat update for the given service."""
        return await self._manager.send_heartbeat(
            service_id=service_id,
            status=status,
            message=message,
            metadata=metadata
        )

    async def get_service(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the service data for a given service ID."""
        return await self._manager.get_service(service_id)

    async def get_all_services(self) -> Dict[str, Dict[str, Any]]:
        """Return a dict of all registered services and their data."""
        # Direct access to internal storage
        return self._manager._services
