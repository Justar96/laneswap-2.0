# LaneSwap Troubleshooting Guide

This guide covers common issues you might encounter when using LaneSwap and how to resolve them.

## Common Errors

### `AttributeError: 'ServiceHeartbeat' object has no attribute 'start'`

**Problem**: This error occurs when trying to call a `start()` method on a `ServiceHeartbeat` object, which doesn't exist.

**Solution**: The `ServiceHeartbeat` class is a Pydantic model used for data validation and serialization, not for managing heartbeat functionality. To properly use LaneSwap for heartbeat monitoring, you should use the `LaneswapAsyncClient` class:

```python
from laneswap.client.async_client import LaneswapAsyncClient
from laneswap.core.types import HeartbeatStatus

# Create the client
client = LaneswapAsyncClient(
    api_url="http://localhost:8000",
    service_name="My Service",
    auto_heartbeat=True,  # Enable automatic heartbeats
    heartbeat_interval=30  # Send heartbeats every 30 seconds
)

# Connect to the API (this registers the service)
await client.connect()

# Send a heartbeat
await client.send_heartbeat(
    status=HeartbeatStatus.HEALTHY,
    message="Service is running normally"
)

# Close the connection when done
await client.close()
```

For a complete example, see the [weather_app_example.py](../examples/weather_app_example.py) file.

If you're using a synchronous environment and can't use `async`/`await`, use the `LaneswapSyncClient` instead:

```python
from laneswap.client.sync_client import LaneswapSyncClient
from laneswap.core.types import HeartbeatStatus

# Create the client
client = LaneswapSyncClient(
    api_url="http://localhost:8000",
    service_name="My Service",
    auto_heartbeat=True
)

# Connect to the API
client.connect()

# Send a heartbeat
client.send_heartbeat(
    status=HeartbeatStatus.HEALTHY,
    message="Service is running normally"
)

# Close the connection when done
client.close()
```

For a complete example, see the [sync_client_example.py](../examples/sync_client_example.py) file.

### `ConnectionRefusedError: [Errno 111] Connection refused`

**Problem**: This error occurs when the LaneSwap API server is not running or not accessible at the specified URL.

**Solution**:
1. Make sure the LaneSwap API server is running:
   ```bash
   python -m laneswap.api.server
   ```
2. Check that the API URL is correct:
   ```python
   client = LaneswapAsyncClient(
       api_url="http://localhost:8000",  # Verify this URL is correct
       service_name="My Service"
   )
   ```
3. If running in a containerized environment, ensure network connectivity between containers.

### `ValueError: Either service_id or service_name must be provided`

**Problem**: This error occurs when creating a `LaneswapAsyncClient` or `LaneswapSyncClient` without providing either a `service_id` or `service_name`.

**Solution**: Always provide at least a `service_name` when creating a client:

```python
# Correct
client = LaneswapAsyncClient(
    api_url="http://localhost:8000",
    service_name="My Service"  # This is required
)

# Also correct (if you already have a service ID)
client = LaneswapAsyncClient(
    api_url="http://localhost:8000",
    service_id="existing-service-id"
)
```

### `ServiceNotFoundError: Service not found: <service_id>`

**Problem**: This error occurs when trying to send a heartbeat for a service that doesn't exist.

**Solution**:
1. Make sure you're using the correct service ID.
2. If you're using a stored service ID, ensure the service is still registered.
3. Register the service before sending heartbeats:
   ```python
   # Connect will register the service if it doesn't exist
   await client.connect()
   
   # Or register explicitly
   service_id = await client.register_service(
       service_name="My Service",
       metadata={"version": "1.0.0"}
   )
   ```

### `RuntimeError: Client not running`

**Problem**: This error occurs when trying to use a `LaneswapSyncClient` method before calling `connect()` or after calling `close()`.

**Solution**: Always call `connect()` before using the client and ensure you don't use the client after calling `close()`:

```python
client = LaneswapSyncClient(
    api_url="http://localhost:8000",
    service_name="My Service"
)

# Connect first
client.connect()

# Now you can use the client
client.send_heartbeat(status="healthy")

# After closing, you can't use the client anymore
client.close()
```

### `TimeoutError: Connection timed out`

**Problem**: This error occurs when a `LaneswapSyncClient` operation takes too long to complete.

**Solution**:
1. Check that the LaneSwap API server is running and responsive.
2. Increase the timeout value:
   ```python
   # Increase connect timeout to 60 seconds
   client.connect(timeout=60.0)
   
   # Increase operation timeout to 60 seconds
   client.send_heartbeat(
       status="healthy",
       timeout=60.0
   )
   ```

## Best Practices

### Use the Client as a Context Manager

#### Async Client

The `LaneswapAsyncClient` can be used as an async context manager, which automatically handles connection and cleanup:

```python
async with LaneswapAsyncClient(
    api_url="http://localhost:8000",
    service_name="My Service",
    auto_heartbeat=True
) as client:
    # Do your work here
    # Heartbeats will be sent automatically
    pass  # The client will be closed automatically
```

#### Sync Client

The `LaneswapSyncClient` can be used as a context manager:

```python
with LaneswapSyncClient(
    api_url="http://localhost:8000",
    service_name="My Service",
    auto_heartbeat=True
) as client:
    # Do your work here
    # Heartbeats will be sent automatically
    pass  # The client will be closed automatically
```

### Enable Auto-Heartbeat for Simple Services

For services that don't need to send custom heartbeats, enable the auto-heartbeat feature:

```python
client = LaneswapAsyncClient(
    api_url="http://localhost:8000",
    service_name="My Service",
    auto_heartbeat=True,  # Enable automatic heartbeats
    heartbeat_interval=30  # Send heartbeats every 30 seconds
)
```

### Send Custom Heartbeats for Important Events

Even with auto-heartbeat enabled, you can send custom heartbeats for important events:

```python
# Send a warning heartbeat
await client.send_heartbeat(
    status=HeartbeatStatus.WARNING,
    message="High resource usage detected",
    metadata={"cpu_usage": 85, "memory_usage": 90}
)

# Send an error heartbeat
await client.send_heartbeat(
    status=HeartbeatStatus.ERROR,
    message="Failed to connect to database",
    metadata={"error": "Connection timeout"}
)
```

### Always Close the Client

#### Async Client

Always close the async client when you're done with it to clean up resources:

```python
# Using try/finally
try:
    await client.connect()
    # Do your work
finally:
    await client.close()

# Or using the context manager (preferred)
async with LaneswapAsyncClient(...) as client:
    # Do your work
```

#### Sync Client

Always close the sync client when you're done with it to clean up resources:

```python
# Using try/finally
try:
    client.connect()
    # Do your work
finally:
    client.close()

# Or using the context manager (preferred)
with LaneswapSyncClient(...) as client:
    # Do your work
```

## Advanced Troubleshooting

### Debugging Connection Issues

If you're having trouble connecting to the LaneSwap API, you can enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Checking Service Status

#### Async Client

You can check the status of a service using the async client:

```python
# Get service status
service = await client.get_service(service_id)
print(f"Service status: {service['status']}")

# Get all services
services = await client.get_all_services()
for service_id, service in services.items():
    print(f"Service {service['name']}: {service['status']}")
```

#### Sync Client

You can check the status of a service using the sync client:

```python
# Get service status
service = client.get_service(service_id)
print(f"Service status: {service['status']}")

# Get all services
services = client.get_all_services()
for service_id, service in services.items():
    print(f"Service {service['name']}: {service['status']}")
```

### Monitoring with the Terminal UI

You can monitor services using the terminal UI:

```bash
python -m laneswap.terminal.monitor --api-url http://localhost:8000
```

Or from Python:

```python
from laneswap.terminal.monitor import start_monitor
import asyncio

asyncio.run(start_monitor(api_url="http://localhost:8000"))
```

## Still Need Help?

If you're still experiencing issues, please:

1. Check the [examples directory](../examples/) for working examples.
2. Review the [API documentation](./API.md) for detailed information about the API.
3. Check the [Migration Guide](./MIGRATION.md) for help migrating from incorrect usage patterns.
4. Open an issue on the GitHub repository with a detailed description of your problem. 