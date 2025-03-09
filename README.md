# LaneSwap Heartbeat Monitoring System

A lightweight, reliable service monitoring system for distributed applications built with FastAPI and Python.

## Overview

LaneSwap Heartbeat is a Python library that provides real-time monitoring of service health in distributed systems. It allows services to send periodic heartbeats to indicate their operational status and automatically detects when services become unresponsive.

## Features

- **Service Health Monitoring**: Track the operational status of multiple services
- **Automatic Stale Detection**: Identify services that have stopped sending heartbeats
- **Flexible Notifications**: Send alerts through various channels when service status changes
- **Persistent Storage**: Store heartbeat history for analysis and reporting
- **Minimal Overhead**: Designed for high performance with low resource usage
- **Decorator Support**: Easily wrap functions with automatic heartbeat reporting
- **Async-First Design**: Built with asyncio for non-blocking operations
- **Functional Programming Approach**: Clean, modular code with minimal state management
- **Web Dashboard**: Real-time monitoring interface with filtering and search capabilities

## Installation

```bash
# Install from PyPI
pip install laneswap

# Or install the development version
pip install git+https://github.com/yourusername/laneswap.git
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

# New configuration variables
API_URL=http://localhost:8000
MONITOR_URL=http://localhost:8080
```

## Quick Start

```python
import asyncio
from laneswap.core.heartbeat import register_service, send_heartbeat, with_heartbeat, heartbeat_system
from laneswap.core.types import HeartbeatStatus
from laneswap.adapters.discord import DiscordNotifier
from laneswap.adapters.mongodb import MongoDBStorage

async def main():
    # Setup storage and notifications
    discord_notifier = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/...")
    mongo_storage = MongoDBStorage(connection_string="mongodb://localhost:27017", database_name="heartbeat_db")
    
    # Initialize the heartbeat system with context manager
    async with heartbeat_system(
        notifiers=[discord_notifier],
        storage=mongo_storage,
        check_interval=30,
        stale_threshold=60
    ):
        # Register a service
        service_id = await register_service(
            service_name="my-api-service",
            metadata={"version": "1.0.0", "environment": "production"}
        )
        
        # Send a heartbeat
        await send_heartbeat(
            service_id=service_id,
            status=HeartbeatStatus.HEALTHY,
            message="Service is running normally"
        )
        
        # Use the decorator for automatic heartbeats
        @with_heartbeat(service_id=service_id)
        async def process_data():
            # Your service logic here
            await asyncio.sleep(1)
            return {"processed": True}
        
        await process_data()

if __name__ == "__main__":
    asyncio.run(main())
```

## Using the REST API

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

## Command Line Interface

LaneSwap includes a command-line interface for managing services:

```bash
# Register a service
laneswap register --name "My Service" --metadata '{"version": "1.0.0"}'

# Send a heartbeat
laneswap heartbeat --id your-service-id --status healthy --message "Running normally"

# List all services
laneswap list

# Get details for a specific service
laneswap get --id your-service-id

# Start the API server
laneswap server --port 8000 --mongodb-url mongodb://localhost:27017

# Monitor services in real-time (terminal UI)
laneswap monitor --interval 5
```

## Web Monitor

LaneSwap includes a web-based dashboard for monitoring service health in real-time.

### Starting the Dashboard

```bash
# Start the dashboard on port 8080 (default)
laneswap dashboard --api-url http://localhost:8000

# Specify a custom port
laneswap dashboard --port 9090 --api-url http://localhost:8000
```

### Generating Monitor URLs

You can generate URLs to the web monitor for specific services:

```bash
# Generate a URL for all services
laneswap monitor-link --api-url http://localhost:8000

# Generate a URL for a specific service
laneswap monitor-link --service-id your-service-id --api-url http://localhost:8000
```

### Programmatic URL Generation

You can also generate monitor URLs programmatically:

```python
from laneswap.core.heartbeat import generate_monitor_url

async def main():
    # Register a service
    service_id = await register_service("my-service")
    
    # Generate a monitor URL for this service
    monitor_url = await generate_monitor_url(
        service_id=service_id,
        api_url="http://localhost:8000"
    )
    
    print(f"Monitor your service at: {monitor_url}")
```

The web monitor provides:

- Real-time status updates for all services
- Detailed service information including metadata
- Filtering and search capabilities
- Grid and table views
- Auto-refresh functionality

## Starting the Web Monitor

There are several ways to start the web monitor:

1. **Using the dashboard command**:
   ```bash
   laneswap dashboard --port 8080 --api-url http://localhost:8000
   ```

2. **Using the start-monitor command** (uses configured URLs):
   ```bash
   laneswap start-monitor
   ```

3. **Automatically when generating a monitor link**:
   ```bash
   laneswap monitor-link --service-id your-service-id --start-if-needed
   ```

4. **From your code**:
   ```python
   # The start_if_needed parameter will start the monitor if it's not running
   monitor_url = await client.get_monitor_url(start_if_needed=True)
   ```

## Accessing the Web Monitor

The web monitor can be accessed in several ways:

1. **Using localhost**:
   ```
   http://localhost:8080/
   ```

2. **Using your machine's IP address**:
   ```
   http://YOUR_IP_ADDRESS:8080/
   ```
   You can find your IP address by running:
   ```bash
   # On Windows
   ipconfig
   
   # On Linux/Mac
   ifconfig
   ```

3. **Using 127.0.0.1**:
   ```
   http://127.0.0.1:8080/
   ```

If you're having trouble accessing the web monitor, try these alternatives.

## Advanced Usage

### Function Decorator

The `with_heartbeat` decorator automatically sends heartbeats before and after function execution:

```python
from laneswap.core.heartbeat import with_heartbeat, register_service
from laneswap.core.types import HeartbeatStatus

async def setup():
    service_id = await register_service("data-processor")
    
    @with_heartbeat(
        service_id=service_id,
        success_status=HeartbeatStatus.HEALTHY,
        error_status=HeartbeatStatus.ERROR
    )
    async def process_batch(batch_id):
        # This function will automatically send heartbeats:
        # - When starting (BUSY status)
        # - On success (HEALTHY status)
        # - On error (ERROR status with exception details)
        pass
```

### Context Manager

Use the context manager for clean setup and teardown:

```python
from laneswap.core.heartbeat import heartbeat_system, register_service, send_heartbeat

async def main():
    async with heartbeat_system(check_interval=15, stale_threshold=45):
        service_id = await register_service("my-service")
        # Your application code here
        await send_heartbeat(service_id, status=HeartbeatStatus.HEALTHY)
```

## Reliability

The LaneSwap Heartbeat system is designed with reliability in mind:

- **False Positive Rate**: <1% under normal network conditions
- **Detection Time**: Configurable, typically within 2x the stale_threshold
- **Overhead**: <5ms per heartbeat operation
- **Scalability**: Tested with 1000+ services on a single monitor

The system uses a time-based approach rather than counting missed heartbeats, which provides more accurate stale detection in environments with variable network latency.

## Architecture

LaneSwap uses a functional programming approach with these key components:

1. **Core Heartbeat System**: Manages service registration and status tracking
2. **Notification Adapters**: Send alerts through various channels (Discord, Slack, Email, etc.)
3. **Storage Adapters**: Persist heartbeat data (MongoDB, Redis, SQLite, etc.)
4. **Web Dashboard**: Visualize service health in real-time

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

## Project Structure

```
laneswap/
├── __init__.py
├── core/           # Core functionality
│   ├── heartbeat.py    # Main heartbeat functions
│   ├── types.py        # Type definitions
│   ├── exceptions.py   # Custom exceptions
│   ├── config.py       # Configuration handling
├── adapters/       # Integration adapters
│   ├── base.py         # Base adapter interfaces
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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Troubleshooting

### Web Monitor Not Found (404)

If you're seeing a 404 error when trying to access the web monitor, make sure:

1. The web monitor server is running on the correct port (default: 8080)
2. You're accessing the correct URL (http://localhost:8080/)
3. You're not trying to access the monitor at the API URL (port 8000)

To start the web monitor:

```bash
laneswap dashboard --api-url http://localhost:8000
```

### Service Not Found Error

If you get a "Service Not Found" error when sending a heartbeat:

1. Make sure the service ID is correct
2. Register the service first before sending heartbeats:

```bash
# Register the service
laneswap register --name "My Service"

# Send a heartbeat using the returned service ID
laneswap heartbeat --id your-service-id --status healthy
```

### Multiple Heartbeat Monitors

If you see a warning about the heartbeat monitor already running, this is normal and can be ignored. The system prevents multiple monitor instances from running simultaneously.

## Important Note on URLs

LaneSwap uses two different servers:

1. **API Server** (default: http://localhost:8000) - Handles heartbeats and service registration
2. **Web Monitor** (default: http://localhost:8080) - Provides the web dashboard

Make sure you're using the correct URL for each purpose:
- For sending heartbeats and registering services, use the API URL
- For viewing the dashboard, use the Web Monitor URL

You can configure these URLs using environment variables:
```
API_URL=http://localhost:8000
MONITOR_URL=http://localhost:8080
```

### Firewall Issues

If you're still having trouble accessing the web monitor, check your firewall settings:

1. **Windows Firewall**:
   - Open Windows Defender Firewall
   - Click "Allow an app or feature through Windows Defender Firewall"
   - Make sure Python is allowed for both private and public networks

2. **Linux/Mac**:
   - Check if any firewall is blocking port 8080:
   ```bash
   sudo ufw status  # Ubuntu/Debian
   sudo firewall-cmd --list-all  # CentOS/RHEL
   ```

## Internationalization

The LaneSwap web monitor supports multiple languages:

- English (default)
- Thai (ไทย)

To change the language:
1. Click on the language button (EN/TH) in the top right corner of the web monitor
2. Or select a language in the Settings menu

### Adding New Languages

To add support for additional languages:

1. Edit the `i18n.js` file in the web monitor directory
2. Add a new language object to the `translations` object
3. Follow the same structure as the existing languages
4. Add a language selector button in `index.html`

## System Check

To verify that all components of the LaneSwap system are working correctly, you can run the system check script:

```bash
python -m laneswap.examples.system_check
```

This script checks:
- All required modules can be imported
- Configuration is loaded correctly
- Web monitor is working
- API server is working
- Client is working

If any issues are found, the script will provide detailed information to help you fix them.