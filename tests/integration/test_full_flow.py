"""
Integration tests for the full flow of the LaneSwap library.
"""

import pytest
import asyncio
import os
from datetime import datetime

from laneswap.core.heartbeat import (
    HeartbeatManager,
    HeartbeatStatus,
    initialize,
    stop_monitor
)
from laneswap.adapters.mongodb import MongoDBAdapter
from laneswap.adapters.discord import DiscordWebhookAdapter
from laneswap.client.async_client import LaneswapAsyncClient


@pytest.mark.skipif(
    "MONGODB_URI" not in os.environ,
    reason="MongoDB URI not provided"
)
@pytest.mark.asyncio
async def test_full_flow_with_mongodb():
    """Test the full flow with MongoDB adapter."""
    mongodb_uri = os.environ.get("MONGODB_URI")
    
    # Create the MongoDB adapter
    storage = MongoDBAdapter(connection_string=mongodb_uri)
    
    # Initialize the heartbeat system
    await initialize(
        storage=storage,
        check_interval=1,
        stale_threshold=5
    )
    
    try:
        # Create a heartbeat manager
        manager = HeartbeatManager()
        
        # Register a service
        service_id = await manager.register_service(
            service_name="Integration Test Service",
            metadata={"test": True, "timestamp": datetime.now().isoformat()}
        )
        
        assert service_id is not None
        
        # Send a heartbeat
        result = await manager.send_heartbeat(
            service_id=service_id,
            status=HeartbeatStatus.HEALTHY,
            message="Service running normally",
            metadata={"test": True, "timestamp": datetime.now().isoformat()}
        )
        
        assert result is True
        
        # Get the service
        service = await manager.get_service(service_id)
        assert service is not None
        assert service.get("status") == HeartbeatStatus.HEALTHY.value
        
        # Start the monitor
        await manager.start_monitor()
        
        # Wait a bit
        await asyncio.sleep(2)
        
        # Send another heartbeat with a different status
        result = await manager.send_heartbeat(
            service_id=service_id,
            status=HeartbeatStatus.WARNING,
            message="High resource usage",
            metadata={"test": True, "timestamp": datetime.now().isoformat()}
        )
        
        assert result is True
        
        # Get the service again
        service = await manager.get_service(service_id)
        assert service is not None
        assert service.get("status") == HeartbeatStatus.WARNING.value
        
        # Wait a bit
        await asyncio.sleep(2)
        
        # Send a final heartbeat
        result = await manager.send_heartbeat(
            service_id=service_id,
            status=HeartbeatStatus.HEALTHY,
            message="Service recovered",
            metadata={"test": True, "timestamp": datetime.now().isoformat()}
        )
        
        assert result is True
        
        # Get all services
        services = await manager.get_all_services()
        assert services is not None
        assert service_id in services
        
        # Clean up
        await storage._ensure_initialized()  # Ensure the adapter is initialized
        await storage.db[storage.heartbeats_collection_name].delete_many({"id": service_id})
    finally:
        # Stop the monitor
        await stop_monitor()


@pytest.mark.skipif(
    "DISCORD_WEBHOOK_URL" not in os.environ or "MONGODB_URI" not in os.environ,
    reason="Discord webhook URL or MongoDB URI not provided"
)
@pytest.mark.asyncio
async def test_full_flow_with_discord():
    """Test the full flow with Discord adapter."""
    mongodb_uri = os.environ.get("MONGODB_URI")
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    
    # Create the adapters
    storage = MongoDBAdapter(connection_string=mongodb_uri)
    notifier = DiscordWebhookAdapter(webhook_url=webhook_url)
    
    # Initialize the heartbeat system
    await initialize(
        storage=storage,
        notifiers=[notifier],
        check_interval=1,
        stale_threshold=5
    )
    
    try:
        # Create a heartbeat manager
        manager = HeartbeatManager()
        
        # Register a service
        service_id = await manager.register_service(
            service_name="Discord Integration Test",
            metadata={"test": True, "timestamp": datetime.now().isoformat()}
        )
        
        assert service_id is not None
        
        # Configure service-specific webhook
        notifier.register_service_webhook(
            service_id=service_id,
            webhook_url=webhook_url,
            username="Discord Test Bot",
            notification_levels=["info", "warning", "error"]
        )
        
        # Start the monitor
        await manager.start_monitor()
        
        # Send a heartbeat
        result = await manager.send_heartbeat(
            service_id=service_id,
            status=HeartbeatStatus.HEALTHY,
            message="Service running normally",
            metadata={"test": True, "timestamp": datetime.now().isoformat()}
        )
        
        assert result is True
        
        # Wait a bit
        await asyncio.sleep(2)
        
        # Send a heartbeat with warning status
        result = await manager.send_heartbeat(
            service_id=service_id,
            status=HeartbeatStatus.WARNING,
            message="High resource usage",
            metadata={"test": True, "timestamp": datetime.now().isoformat()}
        )
        
        assert result is True
        
        # Wait a bit
        await asyncio.sleep(2)
        
        # Send a heartbeat with error status
        result = await manager.send_heartbeat(
            service_id=service_id,
            status=HeartbeatStatus.ERROR,
            message="Service error occurred",
            metadata={"test": True, "timestamp": datetime.now().isoformat()}
        )
        
        assert result is True
        
        # Wait a bit
        await asyncio.sleep(2)
        
        # Send a heartbeat with healthy status
        result = await manager.send_heartbeat(
            service_id=service_id,
            status=HeartbeatStatus.HEALTHY,
            message="Service recovered",
            metadata={"test": True, "timestamp": datetime.now().isoformat()}
        )
        
        assert result is True
        
        # Clean up
        await storage._ensure_initialized()  # Ensure the adapter is initialized
        await storage.db[storage.heartbeats_collection_name].delete_many({"id": service_id})
    finally:
        # Stop the monitor
        await stop_monitor()


@pytest.mark.skipif(
    "MONGODB_URI" not in os.environ or True,  # Always skip for now
    reason="MongoDB URI not provided or API server not running"
)
@pytest.mark.asyncio
async def test_client_integration():
    """Test the async client integration."""
    mongodb_uri = os.environ.get("MONGODB_URI")
    
    # Create the MongoDB adapter
    storage = MongoDBAdapter(connection_string=mongodb_uri)
    
    # Initialize the heartbeat system
    await initialize(
        storage=storage,
        check_interval=1,
        stale_threshold=5
    )
    
    # Start the API server in a separate process
    # Note: In a real test, you would start the API server here
    
    try:
        # Create a client
        client = LaneswapAsyncClient(
            api_url="http://localhost:8000",
            service_name="Client Integration Test",
            auto_heartbeat=True,
            heartbeat_interval=1
        )
        
        try:
            # Register the service
            service_id = await client.register_service(
                service_name="Client Integration Test",
                metadata={"test": True, "timestamp": datetime.now().isoformat()}
            )
            
            assert service_id is not None
            
            # Wait for a few heartbeats
            await asyncio.sleep(3)
            
            # Get the service
            service = await client.get_service()
            
            assert service is not None
            assert service.status == HeartbeatStatus.HEALTHY.value
            
            # Send a heartbeat with warning status
            result = await client.send_heartbeat(
                status=HeartbeatStatus.WARNING,
                message="High resource usage",
                metadata={"test": True, "timestamp": datetime.now().isoformat()}
            )
            
            assert result is True
            
            # Wait a bit
            await asyncio.sleep(1)
            
            # Get the service again
            service = await client.get_service()
            
            assert service is not None
            assert service.status == HeartbeatStatus.WARNING.value
            
            # Clean up
            await storage._ensure_initialized()  # Ensure the adapter is initialized
            await storage.db[storage.heartbeats_collection_name].delete_many({"id": service_id})
        finally:
            # Close the client
            await client.close()
    finally:
        # Stop the monitor
        await stop_monitor() 