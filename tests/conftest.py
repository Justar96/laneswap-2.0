"""Test fixtures for LaneSwap."""

import asyncio
import pytest
from typing import Dict, Any, Optional, List
import os
from datetime import datetime, UTC

from laneswap.core.heartbeat import HeartbeatManager, get_manager
from laneswap.models.heartbeat import HeartbeatStatus


class MockStorageAdapter:
    """Mock storage adapter for testing."""
    
    def __init__(self):
        self.heartbeats = {}
        self.errors = []
        
    async def connect(self):
        """Connect to the storage."""
        return True
        
    async def store_heartbeat(self, service_id: str, heartbeat_data: Dict[str, Any]) -> bool:
        """Store a heartbeat."""
        if service_id not in self.heartbeats:
            self.heartbeats[service_id] = []
        self.heartbeats[service_id].append(heartbeat_data)
        return True
        
    async def get_service_heartbeat(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest heartbeat for a service."""
        if service_id not in self.heartbeats or not self.heartbeats[service_id]:
            return None
        return self.heartbeats[service_id][-1]
        
    async def get_all_heartbeats(self) -> Dict[str, Dict[str, Any]]:
        """Get all heartbeats."""
        result = {}
        for service_id, heartbeats in self.heartbeats.items():
            if heartbeats:
                result[service_id] = heartbeats[-1]
        return result
        
    async def store_error(self, error_data: Dict[str, Any]) -> bool:
        """Store an error."""
        self.errors.append(error_data)
        return True
        
    async def get_errors(
        self,
        service_id: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """Get errors."""
        if service_id:
            filtered = [e for e in self.errors if e.get("service_id") == service_id]
        else:
            filtered = self.errors
        return filtered[skip:skip+limit]
        
    async def is_healthy(self) -> bool:
        """Check if the storage is healthy."""
        return True


class MockNotifierAdapter:
    """Mock notifier adapter for testing."""
    
    def __init__(self):
        self.notifications = []
        
    async def send_notification(
        self,
        title: str,
        message: str,
        service_info: Optional[Dict[str, Any]] = None,
        level: str = "info"
    ) -> bool:
        """Send a notification."""
        self.notifications.append({
            "title": title,
            "message": message,
            "service_info": service_info,
            "level": level,
            "timestamp": datetime.now(UTC)
        })
        return True


@pytest.fixture
def mock_storage():
    """Fixture for a mock storage adapter."""
    return MockStorageAdapter()


@pytest.fixture
def mock_notifier():
    """Fixture for a mock notifier adapter."""
    return MockNotifierAdapter()


@pytest.fixture
async def heartbeat_manager(mock_storage, mock_notifier):
    """Fixture for a heartbeat manager with mock adapters."""
    # Reset the default manager
    global _default_manager
    _default_manager = None
    
    manager = get_manager()
    manager.storage = mock_storage
    manager.notifiers = [mock_notifier]
    manager.check_interval = 1
    manager.stale_threshold = 5
    
    yield manager
    
    # Clean up
    await manager.stop_monitor() 