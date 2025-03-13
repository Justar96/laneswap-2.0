# LaneSwap API Documentation

This document provides detailed information about the LaneSwap client API and how to use it in your applications.

## Client API

LaneSwap provides two client implementations:

1. `LaneswapAsyncClient`: An asynchronous client that uses `async`/`await` for non-blocking operations
2. `LaneswapSyncClient`: A synchronous wrapper around the async client for environments where `async`/`await` cannot be used

### LaneswapAsyncClient

```python
from laneswap.client.async_client import LaneswapAsyncClient
# or
from laneswap.client import LaneswapAsyncClient
```

#### Constructor

```python
client = LaneswapAsyncClient(
    api_url: str,
    service_name: Optional[str] = None,
    service_id: Optional[str] = None,
    auto_heartbeat: bool = False,
    heartbeat_interval: int = 30,
    headers: Optional[Dict[str, str]] = None
)
```

**Parameters:**
- `api_url`: Base URL for the LaneSwap API (e.g., "http://localhost:8000")
- `service_name`: Human-readable name for the service
- `service_id`: Optional service ID (will be auto-generated if not provided)
- `auto_heartbeat`: Whether to automatically send heartbeats
- `heartbeat_interval`: Interval between heartbeats in seconds
- `headers`: Optional headers to include in all requests

**Note:** Either `service_name` or `service_id` must be provided.

#### Methods

##### `connect()`

Connect to the LaneSwap API and register the service if needed.

```python
service_id = await client.connect()
```

**Returns:** Service ID (str)

##### `close()`

Close the client session and clean up resources.

```python
await client.close()
```

##### `register_service()`

Register a new service with the LaneSwap API.

```python
service_id = await client.register_service(
    service_name: str,
    metadata: Optional[Dict[str, Any]] = None
)
```

**Parameters:**
- `service_name`: Human-readable name for the service
- `metadata`: Optional metadata for the service

**Returns:** Service ID (str)

##### `send_heartbeat()`

Send a heartbeat for the service.

```python
await client.send_heartbeat(
    status: Union[HeartbeatStatus, str] = HeartbeatStatus.HEALTHY,
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
)
```

**Parameters:**
- `status`: Service status (HeartbeatStatus enum or string)
- `message`: Optional status message
- `metadata`: Optional metadata to include with the heartbeat

##### `get_service()`

Get information about a service.

```python
service = await client.get_service(service_id: str)
```

**Parameters:**
- `service_id`: Service ID

**Returns:** Service information (Dict[str, Any])

##### `get_all_services()`

Get information about all services.

```python
services = await client.get_all_services()
```

**Returns:** Dictionary mapping service IDs to service information (Dict[str, Dict[str, Any]])

##### `start_progress()`

Start tracking progress for a long-running task.

```python
task_id = await client.start_progress(
    task_name: str,
    total_steps: int,
    description: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
)
```

**Parameters:**
- `task_name`: Name of the task
- `total_steps`: Total number of steps in the task
- `description`: Optional description of the task
- `metadata`: Optional metadata for the task

**Returns:** Task ID (str)

##### `update_progress()`

Update the progress of a task.

```python
await client.update_progress(
    task_id: str,
    current_step: int,
    status: str = "running",
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
)
```

**Parameters:**
- `task_id`: Task ID
- `current_step`: Current step number
- `status`: Task status (e.g., "running", "paused")
- `message`: Optional status message
- `metadata`: Optional metadata to update

##### `complete_progress()`

Mark a task as completed.

```python
await client.complete_progress(
    task_id: str,
    status: str = "completed",
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
)
```

**Parameters:**
- `task_id`: Task ID
- `status`: Final task status (e.g., "completed", "failed")
- `message`: Optional completion message
- `metadata`: Optional metadata to update

#### Context Manager

The `LaneswapAsyncClient` can be used as an async context manager:

```python
async with LaneswapAsyncClient(
    api_url="http://localhost:8000",
    service_name="My Service",
    auto_heartbeat=True
) as client:
    # Do your work here
    # The client will be automatically closed when exiting the context
```

### LaneswapSyncClient

```python
from laneswap.client.sync_client import LaneswapSyncClient
# or
from laneswap.client import LaneswapSyncClient
```

The `LaneswapSyncClient` provides a synchronous interface to the LaneSwap API by running the async client in a background thread. It has the same methods as the async client, but they are called synchronously.

#### Constructor

```python
client = LaneswapSyncClient(
    api_url: str,
    service_name: Optional[str] = None,
    service_id: Optional[str] = None,
    auto_heartbeat: bool = False,
    heartbeat_interval: int = 30,
    headers: Optional[Dict[str, str]] = None
)
```

**Parameters:**
- Same as `LaneswapAsyncClient`

#### Methods

##### `connect()`

Connect to the LaneSwap API and register the service if needed.

```python
service_id = client.connect(timeout=30.0)
```

**Parameters:**
- `timeout`: Timeout in seconds for the connection

**Returns:** Service ID (str)

##### `close()`

Close the client session and clean up resources.

```python
client.close(timeout=5.0)
```

**Parameters:**
- `timeout`: Timeout in seconds for the close operation

##### `send_heartbeat()`

Send a heartbeat for the service.

```python
client.send_heartbeat(
    status=HeartbeatStatus.HEALTHY,
    message="Service is running normally",
    metadata={"version": "1.0.0"},
    timeout=30.0
)
```

**Parameters:**
- Same as `LaneswapAsyncClient` plus:
- `timeout`: Timeout in seconds for the operation

##### Other Methods

All other methods from `LaneswapAsyncClient` are available with the same parameters, plus an optional `timeout` parameter.

#### Context Manager

The `LaneswapSyncClient` can be used as a context manager:

```python
with LaneswapSyncClient(
    api_url="http://localhost:8000",
    service_name="My Service",
    auto_heartbeat=True
) as client:
    # Do your work here
    # The client will be automatically closed when exiting the context
```

## HeartbeatStatus Enum

The `HeartbeatStatus` enum defines the possible status values for a service:

```python
from laneswap.core.types import HeartbeatStatus

# Available status values
HeartbeatStatus.HEALTHY    # Service is healthy
HeartbeatStatus.WARNING    # Service has a warning
HeartbeatStatus.ERROR      # Service has an error
HeartbeatStatus.BUSY       # Service is busy
HeartbeatStatus.IDLE       # Service is idle
HeartbeatStatus.UNKNOWN    # Service status is unknown
HeartbeatStatus.SHUTDOWN   # Service is shutting down
```

## Examples

### Async Client - Basic Usage

```python
import asyncio
from laneswap.client.async_client import LaneswapAsyncClient
from laneswap.core.types import HeartbeatStatus

async def main():
    # Create a client
    client = LaneswapAsyncClient(
        api_url="http://localhost:8000",
        service_name="My Service"
    )
    
    try:
        # Connect to the API
        await client.connect()
        
        # Send a heartbeat
        await client.send_heartbeat(
            status=HeartbeatStatus.HEALTHY,
            message="Service is running normally",
            metadata={"version": "1.0.0"}
        )
        
        # Do some work
        await asyncio.sleep(5)
        
        # Send another heartbeat
        await client.send_heartbeat(
            status=HeartbeatStatus.BUSY,
            message="Service is processing data",
            metadata={"cpu_usage": 75}
        )
    finally:
        # Close the client
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### Async Client - Using Auto-Heartbeat

```python
import asyncio
from laneswap.client.async_client import LaneswapAsyncClient

async def main():
    async with LaneswapAsyncClient(
        api_url="http://localhost:8000",
        service_name="My Service",
        auto_heartbeat=True,  # Enable automatic heartbeats
        heartbeat_interval=30  # Send heartbeats every 30 seconds
    ) as client:
        # Do your work here
        # Heartbeats will be sent automatically
        await asyncio.sleep(120)  # Run for 2 minutes

if __name__ == "__main__":
    asyncio.run(main())
```

### Sync Client - Basic Usage

```python
import time
from laneswap.client.sync_client import LaneswapSyncClient
from laneswap.core.types import HeartbeatStatus

def main():
    # Create a client
    client = LaneswapSyncClient(
        api_url="http://localhost:8000",
        service_name="My Service"
    )
    
    try:
        # Connect to the API
        client.connect()
        
        # Send a heartbeat
        client.send_heartbeat(
            status=HeartbeatStatus.HEALTHY,
            message="Service is running normally",
            metadata={"version": "1.0.0"}
        )
        
        # Do some work
        time.sleep(5)
        
        # Send another heartbeat
        client.send_heartbeat(
            status=HeartbeatStatus.BUSY,
            message="Service is processing data",
            metadata={"cpu_usage": 75}
        )
    finally:
        # Close the client
        client.close()

if __name__ == "__main__":
    main()
```

### Sync Client - Using Context Manager

```python
import time
from laneswap.client.sync_client import LaneswapSyncClient
from laneswap.core.types import HeartbeatStatus

def main():
    with LaneswapSyncClient(
        api_url="http://localhost:8000",
        service_name="My Service",
        auto_heartbeat=True  # Enable automatic heartbeats
    ) as client:
        # Do your work here
        # Heartbeats will be sent automatically
        for i in range(10):
            print(f"Working... {i+1}/10")
            time.sleep(1)

if __name__ == "__main__":
    main()
```

### Tracking Progress

```python
import asyncio
from laneswap.client.async_client import LaneswapAsyncClient

async def main():
    async with LaneswapAsyncClient(
        api_url="http://localhost:8000",
        service_name="Data Processor"
    ) as client:
        # Start a progress task
        task_id = await client.start_progress(
            task_name="Data Processing",
            total_steps=100,
            description="Processing large dataset"
        )
        
        # Update progress as the task progresses
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

### Error Handling

```python
import asyncio
from laneswap.client.async_client import LaneswapAsyncClient
from laneswap.core.types import HeartbeatStatus
from laneswap.core.exceptions import ServiceNotFoundError

async def main():
    client = LaneswapAsyncClient(
        api_url="http://localhost:8000",
        service_name="My Service"
    )
    
    try:
        # Connect to the API
        await client.connect()
        
        try:
            # Do some work that might fail
            result = await some_function_that_might_fail()
            
            # Send success heartbeat
            await client.send_heartbeat(
                status=HeartbeatStatus.HEALTHY,
                message="Operation completed successfully",
                metadata={"result": result}
            )
        except Exception as e:
            # Send error heartbeat
            await client.send_heartbeat(
                status=HeartbeatStatus.ERROR,
                message=f"Operation failed: {str(e)}",
                metadata={"error": str(e)}
            )
            raise
    except ServiceNotFoundError:
        print("Service not found. Make sure the service is registered.")
    except ConnectionError:
        print("Could not connect to the LaneSwap API. Make sure the server is running.")
    finally:
        # Close the client
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Advanced Usage

### Custom Headers

```python
client = LaneswapAsyncClient(
    api_url="http://localhost:8000",
    service_name="My Service",
    headers={
        "Authorization": "Bearer my-token",
        "X-Custom-Header": "custom-value"
    }
)
```

### Monitoring Multiple Services

```python
import asyncio
from laneswap.client.async_client import LaneswapAsyncClient

async def monitor_services():
    client = LaneswapAsyncClient(api_url="http://localhost:8000")
    
    try:
        # Get all services
        services = await client.get_all_services()
        
        # Print service status
        for service_id, service in services.items():
            print(f"Service: {service['name']}")
            print(f"Status: {service['status']}")
            print(f"Last heartbeat: {service['last_heartbeat']}")
            print("---")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(monitor_services())
```

## Error Handling

The client can raise the following exceptions:

- `ServiceNotFoundError`: The specified service was not found
- `ValueError`: Invalid parameters were provided
- `ConnectionError`: Could not connect to the LaneSwap API
- `TimeoutError`: Request timed out
- `RuntimeError`: Client is not running or other runtime error
- `aiohttp.ClientError`: Error communicating with the API (async client only)
- `asyncio.TimeoutError`: Request timed out (async client only)

Always wrap client calls in try/except blocks to handle these exceptions gracefully. 