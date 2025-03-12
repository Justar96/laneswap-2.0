"""
Tests for the core heartbeat functionality.
"""

import pytest
import asyncio
from datetime import datetime

from laneswap.core.heartbeat import (
    HeartbeatManager, 
    HeartbeatStatus,
    get_manager,
    with_heartbeat
)


@pytest.mark.asyncio
async def test_heartbeat_manager_creation():
    """Test creating a heartbeat manager."""
    manager = HeartbeatManager()
    assert manager is not None
    assert isinstance(manager, HeartbeatManager)


@pytest.mark.asyncio
async def test_service_registration():
    """Test registering a service."""
    manager = HeartbeatManager()
    
    service_id = await manager.register_service(
        service_name="Test Service",
        metadata={"version": "1.0.0"}
    )
    
    assert service_id is not None
    assert isinstance(service_id, str)
    
    # Verify the service was registered
    service = await manager.get_service(service_id)
    assert service is not None
    assert service.get("name") == "Test Service"
    assert service.get("metadata", {}).get("version") == "1.0.0"


@pytest.mark.asyncio
async def test_send_heartbeat():
    """Test sending a heartbeat."""
    manager = HeartbeatManager()
    
    # Register a service
    service_id = await manager.register_service(
        service_name="Test Service",
        metadata={"version": "1.0.0"}
    )
    
    # Send a heartbeat
    result = await manager.send_heartbeat(
        service_id=service_id,
        status=HeartbeatStatus.HEALTHY,
        message="Service running normally"
    )
    
    assert result is True
    
    # Get service status
    service = await manager.get_service(service_id)
    assert service is not None
    assert service.get("status") == HeartbeatStatus.HEALTHY.value
    assert service.get("message") == "Service running normally"


@pytest.mark.asyncio
async def test_monitor_start_stop():
    """Test starting and stopping the heartbeat monitor."""
    manager = HeartbeatManager()
    
    # Start the monitor
    await manager.start_monitor()
    assert manager._monitor_running is True
    
    # Stop the monitor
    await manager.stop_monitor()
    assert manager._monitor_running is False


@pytest.mark.asyncio
async def test_get_manager_singleton():
    """Test that get_manager returns a singleton instance."""
    manager1 = get_manager()
    manager2 = get_manager()
    
    assert manager1 is manager2
    assert isinstance(manager1, HeartbeatManager)


@pytest.mark.asyncio
async def test_with_heartbeat_decorator():
    """Test the with_heartbeat decorator."""
    # Create a new manager instance for this test
    manager = HeartbeatManager()
    
    # Register a service
    service_id = await manager.register_service(
        service_name="Test Service",
        metadata={"version": "1.0.0"}
    )
    
    # Set this manager as the global instance by replacing the get_manager function
    import laneswap.core.heartbeat
    original_get_manager = laneswap.core.heartbeat.get_manager
    laneswap.core.heartbeat.get_manager = lambda: manager
    
    # Define a function with the decorator
    @with_heartbeat(service_id=service_id)
    async def test_function():
        await asyncio.sleep(0.1)
        return "success"
    
    try:
        # Call the function
        result = await test_function()
        
        # Verify the result
        assert result == "success"
        
        # Verify a heartbeat was sent
        service = await manager.get_service(service_id)
        assert service is not None
        assert service.get("status") == HeartbeatStatus.HEALTHY.value
    finally:
        # Restore the original get_manager function
        laneswap.core.heartbeat.get_manager = original_get_manager 