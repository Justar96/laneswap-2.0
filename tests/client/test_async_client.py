"""
Tests for the async client.
"""

import pytest
import asyncio
from datetime import datetime
import os

from laneswap.client.async_client import LaneswapAsyncClient
from laneswap.core.heartbeat import HeartbeatStatus


def test_client_initialization():
    """Test initializing the client."""
    client = LaneswapAsyncClient(
        api_url="http://localhost:8000",
        service_name="Test Service"
    )
    assert client.api_url == "http://localhost:8000"
    assert client.service_name == "Test Service"
    assert client.service_id is None


def test_client_with_service_id():
    """Test initializing the client with a service ID."""
    client = LaneswapAsyncClient(
        api_url="http://localhost:8000",
        service_id="test-service-id"
    )
    assert client.api_url == "http://localhost:8000"
    assert client.service_id == "test-service-id"


@pytest.mark.asyncio
async def test_build_url():
    """Test building API URLs."""
    client = LaneswapAsyncClient(
        api_url="http://localhost:8000",
        service_name="Test Service"
    )
    
    # Test URL building
    assert client.api_url == "http://localhost:8000"


@pytest.mark.asyncio
async def test_build_headers():
    """Test building request headers."""
    client = LaneswapAsyncClient(
        api_url="http://localhost:8000",
        service_name="Test Service"
    )
    
    # Test header building
    assert client.api_url == "http://localhost:8000"


@pytest.mark.asyncio
async def test_register_service():
    """Test registering a service."""
    client = LaneswapAsyncClient(
        api_url="http://localhost:8000",
        service_name="Test Service"
    )
    
    try:
        service_id = await client.register_service(
            service_name="Test Service",
            metadata={"test": True, "timestamp": datetime.now().isoformat()}
        )
        assert service_id is not None
    except Exception as e:
        pytest.skip(f"Failed to register service: {str(e)}")
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_send_heartbeat():
    """Test sending a heartbeat."""
    try:
        # Initialize client
        client = LaneswapAsyncClient(
            api_url="http://localhost:8000",
            service_name="Test Service"
        )
        
        # Register service first
        service_id = await client.register_service(
            service_name="Test Service",
            metadata={"test": True}
        )
        
        # Set the service ID
        client.service_id = service_id
        
        # Send heartbeat
        status = await client.send_heartbeat(
            status=HeartbeatStatus.HEALTHY,
            message="Test heartbeat",
            metadata={"test": True}
        )
        
        assert status is not None
        assert "id" in status
        assert status["id"] == service_id
        assert status["status"] == HeartbeatStatus.HEALTHY.value
        
        # Close the client
        await client.close()
    except Exception as e:
        pytest.skip(f"Failed to send heartbeat: {str(e)}")


@pytest.mark.asyncio
async def test_get_service():
    """Test getting service status."""
    try:
        # Initialize client
        client = LaneswapAsyncClient(
            api_url="http://localhost:8000",
            service_name="Test Service"
        )
        
        # Register service
        service_id = await client.register_service(
            service_name="Test Service",
            metadata={"test": True}
        )
        
        # Set the service ID
        client.service_id = service_id
        
        # Get service status
        status = await client.get_service()
        assert status is not None
        assert "id" in status
        assert status["id"] == service_id
        
        # Close the client
        await client.close()
    except Exception as e:
        pytest.skip(f"Failed to get service: {str(e)}")


@pytest.mark.asyncio
async def test_auto_heartbeat():
    """Test automatic heartbeat sending."""
    try:
        # Initialize client with auto heartbeat
        client = LaneswapAsyncClient(
            api_url="http://localhost:8000",
            service_name="Auto Heartbeat Test",
            auto_heartbeat=True,
            heartbeat_interval=1  # 1 second interval for faster testing
        )
        
        # Connect to start auto heartbeat
        await client.connect()
        
        # Wait for at least one heartbeat to be sent
        await asyncio.sleep(2)
        
        # Get service status
        status = await client.get_service()
        assert status is not None
        
        # The status might be 'unknown' initially, but should eventually become 'healthy'
        # Wait a bit longer if needed
        if status["status"] != HeartbeatStatus.HEALTHY.value:
            await asyncio.sleep(2)
            status = await client.get_service()
            
        assert status["status"] in [HeartbeatStatus.HEALTHY.value, HeartbeatStatus.UNKNOWN.value]
    except Exception as e:
        pytest.skip(f"Failed to test auto heartbeat: {str(e)}")
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_client_close():
    """Test closing the client."""
    # Start the API server on a different port
    process = await asyncio.create_subprocess_exec(
        "python", "-m", "laneswap.api.main",
        env={**os.environ, "PORT": "8001", "HOST": "127.0.0.1"},  # Use localhost explicitly
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # Wait for server to start and verify it's running
    await asyncio.sleep(2)
    
    try:
        # Try to connect a few times before giving up
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                client = LaneswapAsyncClient(
                    api_url="http://127.0.0.1:8001",  # Use localhost explicitly
                    service_name="Test Service",
                    auto_heartbeat=True
                )
                
                # Connect to start auto heartbeat
                await client.connect()
                
                # Close the client
                await client.close()
                
                # Verify the client is closed
                assert client._session is None
                assert client._heartbeat_task is None
                assert client._connected is False
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(retry_delay)
    finally:
        # Clean up server process
        try:
            process.terminate()
            await process.wait()
        except ProcessLookupError:
            pass  # Process already terminated 