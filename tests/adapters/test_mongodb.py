"""
Tests for the MongoDB adapter.
"""

import pytest
import asyncio
from datetime import datetime, UTC
import os
from typing import Dict, Any

from laneswap.adapters.mongodb import MongoDBAdapter
from laneswap.core.heartbeat import HeartbeatStatus
from laneswap.models.error import ErrorLog


@pytest.mark.skipif(
    "MONGODB_URI" not in os.environ,
    reason="MongoDB URI not provided"
)
@pytest.mark.asyncio
async def test_mongodb_initialization():
    """Test initializing the MongoDB adapter."""
    adapter = MongoDBAdapter(
        connection_string=os.environ["MONGODB_URI"],
        database_name=os.environ.get("MONGODB_NAME", "laneswap_test")
    )
    
    await adapter.initialize()
    assert adapter._initialized is True
    await adapter.close()


@pytest.mark.skipif(
    "MONGODB_URI" not in os.environ,
    reason="MongoDB URI not provided"
)
@pytest.mark.asyncio
async def test_store_heartbeat():
    """Test storing a heartbeat."""
    adapter = MongoDBAdapter(
        connection_string=os.environ["MONGODB_URI"],
        database_name=os.environ.get("MONGODB_NAME", "laneswap_test")
    )
    
    await adapter.initialize()
    
    try:
        # Create test heartbeat data
        service_id = "test-service"
        heartbeat_data = {
            "service_id": service_id,
            "timestamp": datetime.now(UTC),
            "status": HeartbeatStatus.HEALTHY.value,
            "message": "Test heartbeat",
            "metadata": {"test": True}
        }
        
        # Store the heartbeat
        result = await adapter.store_heartbeat(service_id, heartbeat_data)
        assert result is True
        
        # Verify the heartbeat was stored
        stored = await adapter.get_service_heartbeat(service_id)
        assert stored is not None
        assert stored["service_id"] == service_id
        assert stored["status"] == HeartbeatStatus.HEALTHY.value
        assert stored["message"] == "Test heartbeat"
        assert stored["metadata"]["test"] is True
    finally:
        await adapter.close()


@pytest.mark.skipif(
    "MONGODB_URI" not in os.environ,
    reason="MongoDB URI not provided"
)
@pytest.mark.asyncio
async def test_store_error():
    """Test storing an error log."""
    adapter = MongoDBAdapter(
        connection_string=os.environ["MONGODB_URI"],
        database_name=os.environ.get("MONGODB_NAME", "laneswap_test")
    )
    
    await adapter.initialize()
    
    try:
        # Create test error data
        error_data = {
            "service_id": "test-service",
            "timestamp": datetime.now(UTC),
            "error_type": "TestError",
            "message": "Test error message",
            "metadata": {"test": True}
        }
        
        # Store the error
        result = await adapter.store_error(error_data)
        assert result is True
        
        # Verify the error was stored
        errors = await adapter.get_errors(service_id="test-service", limit=1)
        assert len(errors) == 1
        stored = errors[0]
        assert stored["service_id"] == "test-service"
        assert stored["error_type"] == "TestError"
        assert stored["message"] == "Test error message"
        assert stored["metadata"]["test"] is True
    finally:
        await adapter.close()


@pytest.mark.skipif(
    "MONGODB_URI" not in os.environ,
    reason="MongoDB URI not provided"
)
@pytest.mark.asyncio
async def test_get_all_heartbeats():
    """Test getting all heartbeats."""
    adapter = MongoDBAdapter(
        connection_string=os.environ["MONGODB_URI"],
        database_name=os.environ.get("MONGODB_NAME", "laneswap_test")
    )
    
    await adapter.initialize()
    
    # Store multiple heartbeats
    service_ids = []
    for i in range(3):
        service_id = f"test-service-{i}-{datetime.now().timestamp()}"
        service_ids.append(service_id)
        
        heartbeat_data = {
            "status": HeartbeatStatus.HEALTHY.value,
            "message": f"Service {i} running normally",
            "timestamp": datetime.now(),
            "metadata": {"test": True, "index": i}
        }
        
        await adapter.store_heartbeat(service_id, heartbeat_data)
    
    # Get all heartbeats
    all_heartbeats = await adapter.get_all_heartbeats()
    
    # Verify all test services are in the results
    for service_id in service_ids:
        assert service_id in all_heartbeats
        assert all_heartbeats[service_id]["status"] == HeartbeatStatus.HEALTHY.value
    
    # Clean up
    for service_id in service_ids:
        await adapter.db[adapter.heartbeats_collection_name].delete_one({"service_id": service_id}) 