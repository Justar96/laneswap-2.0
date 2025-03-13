# Migration Guide

This guide is for users who are migrating from incorrect usage patterns to the correct way of using LaneSwap.

## Migrating from ServiceHeartbeat.start() to LaneswapAsyncClient

If you're currently using code like this:

```python
from laneswap.models.heartbeat import ServiceHeartbeat

# Incorrect usage
heartbeat = ServiceHeartbeat(service_name="Weather App")
heartbeat.start()  # This will fail with AttributeError
```

You should migrate to using the `LaneswapAsyncClient` class instead:

```python
from laneswap.client.async_client import LaneswapAsyncClient
import asyncio

async def main():
    # Create the client
    client = LaneswapAsyncClient(
        api_url="http://localhost:8000",
        service_name="Weather App",
        auto_heartbeat=True  # Enable automatic heartbeats
    )
    
    # Connect to the API (this registers the service)
    await client.connect()
    
    try:
        # Your application logic here
        await asyncio.sleep(60)  # Run for 60 seconds
    finally:
        # Close the client
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Using the Context Manager

For even cleaner code, you can use the async context manager:

```python
from laneswap.client.async_client import LaneswapAsyncClient
import asyncio

async def main():
    async with LaneswapAsyncClient(
        api_url="http://localhost:8000",
        service_name="Weather App",
        auto_heartbeat=True  # Enable automatic heartbeats
    ) as client:
        # Your application logic here
        await asyncio.sleep(60)  # Run for 60 seconds
        
        # Send custom heartbeats when needed
        await client.send_heartbeat(
            status="healthy",
            message="Custom heartbeat message",
            metadata={"custom": "data"}
        )

if __name__ == "__main__":
    asyncio.run(main())
```

## Migrating a Class-Based Application

If you have a class-based application, you can integrate LaneSwap like this:

```python
from laneswap.client.async_client import LaneswapAsyncClient
from laneswap.core.types import HeartbeatStatus
import asyncio

class MyApplication:
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.client = None
        self.running = False
    
    async def start(self):
        """Start the application with heartbeat monitoring."""
        # Create the LaneSwap client
        self.client = LaneswapAsyncClient(
            api_url=self.api_url,
            service_name="My Application",
            auto_heartbeat=True
        )
        
        # Connect to the API
        await self.client.connect()
        
        # Start the main app loop
        self.running = True
        await self.run()
    
    async def stop(self):
        """Stop the application."""
        self.running = False
        
        if self.client:
            # Send a final heartbeat
            await self.client.send_heartbeat(
                status=HeartbeatStatus.SHUTDOWN,
                message="Application shutting down"
            )
            
            # Close the client
            await self.client.close()
    
    async def run(self):
        """Main application loop."""
        try:
            while self.running:
                # Your application logic here
                await asyncio.sleep(1)
        except Exception as e:
            # Send error heartbeat
            if self.client:
                await self.client.send_heartbeat(
                    status=HeartbeatStatus.ERROR,
                    message=f"Error: {str(e)}",
                    metadata={"error": str(e)}
                )
            raise

async def main():
    app = MyApplication()
    
    try:
        await app.start()
    except KeyboardInterrupt:
        pass
    finally:
        await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## Migrating from Synchronous Code

If you're using synchronous code and can't easily switch to async/await, you can use the synchronous wrapper:

```python
import time
import threading
import asyncio
from laneswap.client.async_client import LaneswapAsyncClient

class SyncHeartbeatClient:
    def __init__(self, api_url, service_name):
        self.api_url = api_url
        self.service_name = service_name
        self.client = None
        self.loop = None
        self.thread = None
        self.running = False
    
    def start(self):
        """Start the heartbeat client in a background thread."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_async_loop)
        self.thread.daemon = True
        self.thread.start()
        
        # Wait for the client to be initialized
        while self.client is None and self.running:
            time.sleep(0.1)
    
    def _run_async_loop(self):
        """Run the async event loop in a background thread."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        async def init_client():
            self.client = LaneswapAsyncClient(
                api_url=self.api_url,
                service_name=self.service_name,
                auto_heartbeat=True
            )
            await self.client.connect()
        
        self.loop.run_until_complete(init_client())
        
        try:
            self.loop.run_forever()
        finally:
            self.loop.close()
    
    def stop(self):
        """Stop the heartbeat client."""
        if not self.running:
            return
        
        self.running = False
        
        async def cleanup():
            if self.client:
                await self.client.close()
        
        if self.loop and self.loop.is_running():
            self.loop.create_task(cleanup())
            self.loop.call_soon_threadsafe(self.loop.stop)
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)
    
    def send_heartbeat(self, status="healthy", message=None, metadata=None):
        """Send a heartbeat synchronously."""
        if not self.running or not self.client or not self.loop:
            raise RuntimeError("Client not running")
        
        async def do_send():
            await self.client.send_heartbeat(
                status=status,
                message=message,
                metadata=metadata
            )
        
        future = asyncio.run_coroutine_threadsafe(do_send(), self.loop)
        future.result(timeout=5.0)  # Wait for the result with a timeout

# Usage example
if __name__ == "__main__":
    client = SyncHeartbeatClient(
        api_url="http://localhost:8000",
        service_name="Sync Service"
    )
    
    try:
        # Start the client
        client.start()
        
        # Your synchronous application logic
        for i in range(10):
            print(f"Doing work {i+1}/10")
            
            # Send custom heartbeats
            client.send_heartbeat(
                status="healthy",
                message=f"Work progress: {i+1}/10",
                metadata={"progress": (i+1)/10}
            )
            
            time.sleep(1)
    finally:
        # Stop the client
        client.stop()
```

## Further Help

If you're still having trouble migrating your code, please refer to:

1. [API Documentation](API.md) for detailed information about the API
2. [Troubleshooting Guide](TROUBLESHOOTING.md) for solutions to common issues
3. [Example Applications](../examples/) for working examples of LaneSwap integration 