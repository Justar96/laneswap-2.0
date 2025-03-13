# LaneSwap Client Module

The client module provides a Python client for interacting with the LaneSwap API, allowing services to register, send heartbeats, and track progress.

## Components

### Async Client (`async_client.py`)

The `LaneswapAsyncClient` is an asynchronous client for the LaneSwap API, providing methods for all API operations.

#### Key Features

- **Async/Await Support**: Built with asyncio for non-blocking operations
- **Context Manager**: Can be used as an async context manager
- **Auto-Heartbeat**: Optional automatic heartbeat sending
- **Retry Logic**: Automatic retry for failed requests
- **Error Handling**: Comprehensive error handling
- **Service Registration**: Automatic service registration
- **Progress Tracking**: Methods for tracking progress of long-running tasks

#### Usage Example

```python
from laneswap.client.async_client import LaneswapAsyncClient
import asyncio

async def main():
    # Create a client
    client = LaneswapAsyncClient(
        api_url="http://localhost:8000",
        service_name="my-service",
        metadata={"version": "1.0.0"}
    )
    
    # Connect to the API (registers the service)
    await client.connect()
    
    # Send a heartbeat
    await client.send_heartbeat(
        status="healthy",
        message="Service is running normally",
        metadata={"cpu_usage": 25, "memory_usage": 150}
    )
    
    # Close the connection
    await client.close()
    
    # Or use as a context manager
    async with LaneswapAsyncClient(
        api_url="http://localhost:8000",
        service_name="another-service",
        auto_heartbeat=True,  # Automatically send heartbeats
        heartbeat_interval=30  # Send heartbeats every 30 seconds
    ) as client:
        # Do your work here
        # Heartbeats will be sent automatically
        
        # Start a progress task
        task_id = await client.start_progress(
            task_name="Data Processing",
            total_steps=100,
            description="Processing large dataset"
        )
        
        # Update progress
        for i in range(100):
            await client.update_progress(
                task_id=task_id,
                current_step=i+1,
                status="running",
                message=f"Processing item {i+1}/100"
            )
            await asyncio.sleep(0.1)
        
        # Complete the progress task
        await client.complete_progress(
            task_id=task_id,
            status="completed",
            message="Data processing completed successfully"
        )

if __name__ == "__main__":
    asyncio.run(main())
```

## Client Configuration

The client can be configured with various options:

### Basic Configuration

- `api_url`: URL of the LaneSwap API server (required)
- `service_name`: Name of the service (required)
- `metadata`: Additional metadata for the service (optional)

### Auto-Heartbeat Configuration

- `auto_heartbeat`: Whether to automatically send heartbeats (default: False)
- `heartbeat_interval`: Interval in seconds between heartbeats (default: 30)
- `heartbeat_status`: Default status for automatic heartbeats (default: "healthy")
- `heartbeat_message`: Default message for automatic heartbeats (default: "Service is running normally")

### Connection Configuration

- `timeout`: Request timeout in seconds (default: 10)
- `max_retries`: Maximum number of retries for failed requests (default: 3)
- `retry_delay`: Delay in seconds between retries (default: 1)
- `verify_ssl`: Whether to verify SSL certificates (default: True)

## Client Methods

### Connection Management

- `connect()`: Connect to the API and register the service
- `close()`: Close the connection and stop automatic heartbeats
- `is_connected()`: Check if the client is connected

### Heartbeat Management

- `send_heartbeat()`: Send a heartbeat for the service
- `start_auto_heartbeat()`: Start sending automatic heartbeats
- `stop_auto_heartbeat()`: Stop sending automatic heartbeats

### Service Management

- `register_service()`: Register a new service
- `get_service()`: Get information about a service
- `get_all_services()`: Get information about all services
- `delete_service()`: Delete a service

### Progress Tracking

- `start_progress()`: Start a new progress task
- `update_progress()`: Update a progress task
- `complete_progress()`: Complete a progress task
- `get_progress()`: Get information about a progress task
- `get_all_progress()`: Get information about all progress tasks
- `delete_progress()`: Delete a progress task

## Error Handling

The client provides comprehensive error handling:

- `LaneswapClientError`: Base class for all client errors
- `ConnectionError`: Raised when the client fails to connect to the API
- `AuthenticationError`: Raised when authentication fails
- `RequestError`: Raised when a request fails
- `ServiceNotFoundError`: Raised when a service is not found
- `InvalidServiceIDError`: Raised when an invalid service ID is provided
- `InvalidHeartbeatError`: Raised when an invalid heartbeat is provided
- `InvalidProgressError`: Raised when an invalid progress update is provided

Example error handling:

```python
from laneswap.client.async_client import LaneswapAsyncClient, LaneswapClientError

async def main():
    try:
        async with LaneswapAsyncClient(
            api_url="http://localhost:8000",
            service_name="my-service"
        ) as client:
            await client.send_heartbeat(status="healthy")
    except LaneswapClientError as e:
        print(f"Client error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
```

## Integration with Other Modules

The client module integrates with other LaneSwap modules:

- **API Module**: Communicates with the API server
- **Models Module**: Uses data models for request/response validation
- **Core Module**: Uses core types and exceptions

## Advanced Usage

### Custom Headers

You can add custom headers to all requests:

```python
from laneswap.client.async_client import LaneswapAsyncClient

async def main():
    client = LaneswapAsyncClient(
        api_url="http://localhost:8000",
        service_name="my-service",
        headers={
            "X-Custom-Header": "custom-value",
            "Authorization": "Bearer my-token"
        }
    )
    
    await client.connect()
```

### Custom Session

You can provide a custom aiohttp session:

```python
import aiohttp
from laneswap.client.async_client import LaneswapAsyncClient

async def main():
    # Create a custom session
    session = aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=30),
        headers={"User-Agent": "MyCustomClient/1.0"}
    )
    
    # Use the custom session
    client = LaneswapAsyncClient(
        api_url="http://localhost:8000",
        service_name="my-service",
        session=session
    )
    
    await client.connect()
    
    # Don't forget to close the session
    await session.close()
```

### Heartbeat Decorator

You can use the `with_heartbeat` decorator from the core module with the client:

```python
from laneswap.core.heartbeat import with_heartbeat
from laneswap.client.async_client import LaneswapAsyncClient
import asyncio

# Create a client
client = LaneswapAsyncClient(
    api_url="http://localhost:8000",
    service_name="my-service"
)

@with_heartbeat(
    client=client,
    success_status="healthy",
    error_status="error"
)
async def my_function():
    # Do something
    return "Success"

async def main():
    await client.connect()
    
    # This will automatically send heartbeats
    result = await my_function()
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Best Practices

1. **Use Context Manager**: Use the client as an async context manager when possible
2. **Enable Auto-Heartbeat**: Enable auto-heartbeat for long-running services
3. **Handle Errors**: Implement proper error handling
4. **Close Connections**: Always close the client when done
5. **Use Metadata**: Include useful metadata with service registration and heartbeats
6. **Track Progress**: Use progress tracking for long-running tasks
7. **Retry Configuration**: Adjust retry settings based on your network reliability
8. **Timeout Configuration**: Set appropriate timeouts for your environment
9. **Secure Connections**: Use HTTPS in production
10. **Monitor Client**: Log client errors and connection issues 