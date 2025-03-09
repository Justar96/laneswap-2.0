# Laneswap Heartbeat Monitoring System

A Python-based service health monitoring library built with FastAPI that allows any service to send heartbeats and track their status.

## Features

- **Service Heartbeat Monitoring**: Track the health status of multiple services
- **Status Tracking**: Supports multiple status types (healthy, degraded, error, busy, stale)
- **Discord Webhook Integration**: Send notifications to Discord when service status changes
- **MongoDB Integration**: Store heartbeat data and error logs in MongoDB Atlas
- **Easy API Integration**: Simple REST API for services to send heartbeats
- **Web Monitor**: Simple HTML/CSS/JS dashboard to monitor service status

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/laneswap.git
cd laneswap

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Configuration

Laneswap can be configured using environment variables:

```
# MongoDB configuration
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DATABASE=laneswap

# Discord webhook configuration
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook-url
DISCORD_WEBHOOK_USERNAME=Laneswap Monitor

# Heartbeat configuration
HEARTBEAT_CHECK_INTERVAL=30  # seconds
HEARTBEAT_STALE_THRESHOLD=60  # seconds

# API configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false
CORS_ORIGINS=*
```

## Usage

### Starting the API server

```bash
# With environment variables
python -m laneswap.api.main

# Or using a .env file
# Create a .env file with the configuration variables above
python -m laneswap.api.main
```

### Using the library in your service

```python
import asyncio
from laneswap.core.heartbeat import get_manager

async def main():
    # Get the default heartbeat manager
    manager = get_manager()
    
    # Register your service
    service_id = await manager.register_service(
        service_id="my-service-123",  # Optional, will be auto-generated if not provided
        service_name="My Service",
        metadata={
            "version": "1.0.0",
            "environment": "production"
        }
    )
    
    # Send heartbeats
    await manager.send_heartbeat(
        service_id=service_id,
        status="healthy",
        message="Service is running normally",
        metadata={
            "memory_usage_mb": 120,
            "active_connections": 45
        }
    )
    
    # Later, you can update with a different status
    await manager.send_heartbeat(
        service_id=service_id,
        status="degraded",
        message="Service is experiencing slow response times"
    )

if __name__ == "__main__":
    asyncio.run(main())
```

### Using the REST API

Register a service:

```bash
curl -X POST http://localhost:8000/api/services \
  -H "Content-Type: application/json" \
  -d '{"service_name": "My Service", "metadata": {"version": "1.0.0"}}'
```

Send a heartbeat:

```bash
curl -X POST http://localhost:8000/api/services/your-service-id/heartbeat \
  -H "Content-Type: application/json" \
  -d '{"status": "healthy", "message": "Service running normally"}'
```

Get service status:

```bash
curl http://localhost:8000/api/services/your-service-id
```

Get all services:

```bash
curl http://localhost:8000/api/services
```

### Running the example service

```bash
# Start the API server first
python -m laneswap.api.main

# In another terminal, run the example service
python -m laneswap.examples.simple_service --api-url http://localhost:8000
```

### Using the Web Monitor

Open the `laneswap/examples/web_monitor/index.html` file in your browser. Enter the API URL (e.g., `http://localhost:8000`) and click "Refresh" to view your services.

## Project Structure

```
laneswap/
├── __init__.py
├── core/           # Core functionality
│   ├── heartbeat.py    # Main heartbeat manager
│   ├── config.py       # Configuration handling
├── adapters/       # Integration adapters
│   ├── discord.py      # Discord webhook notifications
│   ├── mongodb.py      # MongoDB storage
├── api/            # FastAPI implementation
│   ├── main.py         # API entrypoint
│   ├── routers/        # API routes
├── models/         # Data models
├── examples/       # Example usage
│   ├── simple_service.py   # Example service
│   ├── web_monitor/        # Web dashboard
```

## Extending Laneswap

### Creating a Custom Notifier

Implement the `NotifierAdapter` interface:

```python
from typing import Dict, Any, Optional
from laneswap.adapters.base import NotifierAdapter

class MyCustomNotifier(NotifierAdapter):
    async def send_notification(
        self,
        title: str,
        message: str,
        service_info: Optional[Dict[str, Any]] = None,
        level: str = "info"
    ) -> bool:
        # Your notification logic here
        return True
```

### Creating a Custom Storage Adapter

Implement the `StorageAdapter` interface:

```python
from typing import Dict, Any, Optional, List
from laneswap.adapters.base import StorageAdapter

class MyCustomStorage(StorageAdapter):
    async def store_heartbeat(
        self,
        service_id: str,
        heartbeat_data: Dict[str, Any]
    ) -> bool:
        # Your storage logic here
        return True
    
    # Implement other required methods...
```

## License

MIT