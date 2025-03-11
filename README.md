# LaneSwap

A lightweight, reliable service monitoring system for distributed applications built with FastAPI and Python.

## Overview

LaneSwap Heartbeat is a Python library that provides real-time monitoring of service health in distributed systems. It allows services to send periodic heartbeats to indicate their operational status and automatically detects when services become unresponsive.

## Key Features

- **Real-time Health Monitoring**: Track the operational status of all your services
- **Automatic Stale Detection**: Identify services that have stopped sending heartbeats
- **Web Dashboard**: Beautiful, responsive UI for monitoring service health
- **Multi-language Support**: Interface available in English and Thai
- **Flexible Notifications**: Send alerts through various channels when service status changes
- **Low Overhead**: Minimal impact on your services' performance
- **Easy Integration**: Simple API for sending heartbeats from any service
- **MongoDB Integration**: Persistent storage of heartbeat data
- **Discord Notifications**: Real-time alerts via Discord webhooks
- **Async Support**: Built with asyncio for high performance

## Quick Start

### Installation

```bash
pip install laneswap
```

### Start the API Server with Web Monitor

```bash
python -m laneswap.api.server
```

This will:
- Start the API server on port 8000
- Start the web monitor on port 8080
- Open the web monitor in your default browser

### Command Line Options

```bash
# Start without opening a browser
python -m laneswap.api.server --no-browser

# Start without the web monitor
python -m laneswap.api.server --no-monitor

# Specify custom ports
python -m laneswap.api.server --port 9000 --monitor-port 9080
```

### Using the CLI

```bash
# Start the server with web monitor
laneswap server

# Start without opening a browser
laneswap server --no-browser

# Start without the web monitor
laneswap server --no-monitor

# List all registered services
laneswap services list

# Get details for a specific service
laneswap services get <service-id>

# Send a heartbeat for a service
laneswap services heartbeat <service-id> --status healthy
```

### Register a Service and Send Heartbeats

```python
from laneswap.client.async_client import LaneswapAsyncClient
import asyncio

async def main():
    # Create a client
    client = LaneswapAsyncClient(
        api_url="http://localhost:8000",
        service_name="my-service"
    )
    
    # Connect to the API
    await client.connect()
    
    # Send a heartbeat
    await client.send_heartbeat(
        status="healthy",
        message="Service is running normally"
    )
    
    # Use as a context manager
    async with LaneswapAsyncClient(
        api_url="http://localhost:8000",
        service_name="another-service",
        auto_heartbeat=True  # Automatically send heartbeats
    ) as client:
        # Do your work here
        # Heartbeats will be sent automatically
        pass

if __name__ == "__main__":
    asyncio.run(main())
```

## System Architecture

LaneSwap consists of several main components:

1. **API Server**: FastAPI-based server that receives heartbeats from services and stores their status
2. **Web Monitor**: Responsive web dashboard for monitoring service health in real-time
3. **Client Library**: Async client for sending heartbeats from your services
4. **Storage Adapters**: Pluggable storage backends (currently MongoDB)
5. **Notification Adapters**: Pluggable notification systems (currently Discord)
6. **CLI**: Command-line interface for interacting with the system

## Configuration

LaneSwap can be configured using environment variables or a configuration file:

```bash
# Set the MongoDB connection string
export LANESWAP_MONGODB_URI="mongodb://localhost:27017"

# Set the Discord webhook URL for notifications
export LANESWAP_DISCORD_WEBHOOK="https://discord.com/api/webhooks/..."

# Set the check interval for stale services (in seconds)
export LANESWAP_CHECK_INTERVAL="30"

# Set the threshold for considering a service stale (in seconds)
export LANESWAP_STALE_THRESHOLD="60"
```

Or create a `.env` file in your project directory:

```
LANESWAP_MONGODB_URI=mongodb://localhost:27017
LANESWAP_DISCORD_WEBHOOK=https://discord.com/api/webhooks/...
LANESWAP_CHECK_INTERVAL=30
LANESWAP_STALE_THRESHOLD=60
```

## Web Monitor Features

The web monitor provides a comprehensive dashboard for monitoring your services:

- **Real-time Updates**: See service status changes as they happen
- **Search and Filtering**: Quickly find specific services
- **Grid and Table Views**: Choose the view that works best for you
- **Dark/Light Themes**: Customize the interface to your preference
- **Detailed Service Information**: View complete service history and metadata
- **Responsive Design**: Works on desktop and mobile devices
- **Internationalization**: Support for multiple languages

## Adding a New Language

To add a new language to the web monitor:

1. Open `laneswap/examples/web_monitor/i18n.js`
2. Add a new language object to the `translations` object
3. Follow the same structure as the existing languages
4. Add a language selector button in `index.html`

Example of adding German language support:

```javascript
// In i18n.js
const translations = {
    en: {
        // existing English translations
    },
    th: {
        // existing Thai translations
    },
    de: {
        title: "LaneSwap Monitor",
        nav: {
            title: "LaneSwap Monitor",
            dashboard: "Dashboard",
            settings: "Einstellungen",
            help: "Hilfe"
        },
        // Add all other translations
    }
};

// In index.html, add to the language switcher:
// <button class="lang-btn" data-lang="de" onclick="changeLanguage('de')">DE</button>
```

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
- MongoDB connection (if configured)
- Discord webhook (if configured)

If any issues are found, the script will provide detailed information to help you fix them.

## Troubleshooting

### Common Issues

#### MongoDB Connection Failures

If you see errors like:
```
Failed to initialize MongoDB adapter: localhost:27017: [WinError 10061] No connection could be made because the target machine actively refused it
```

This means MongoDB is not running or not accessible. To fix:

1. Make sure MongoDB is installed and running:
   ```bash
   # Check if MongoDB is running
   mongosh
   ```

2. If MongoDB is not installed, you can install it or use a Docker container:
   ```bash
   # Run MongoDB in Docker
   docker run -d -p 27017:27017 --name mongodb mongo:latest
   ```

3. Update your connection string in the `.env` file if your MongoDB is running on a different host or port.

#### Import Errors

If you encounter import errors during the system check, ensure all dependencies are installed:

```bash
pip install -r requirements.txt
```

#### Web Monitor Issues

If the web monitor fails to start:

1. Check if the port is already in use:
   ```bash
   # On Windows
   netstat -ano | findstr :8080
   
   # On Linux/macOS
   lsof -i :8080
   ```

2. Try specifying a different port:
   ```bash
   python -m laneswap.api.server --monitor-port 9080
   ```

3. Ensure you have the required permissions to open the browser automatically.

#### Configuration Issues

If configuration checks fail:

1. Verify your `.env` file is in the correct location (project root directory)
2. Check for syntax errors in your configuration
3. Try setting environment variables directly:
   ```bash
   # Windows
   set LANESWAP_MONGODB_URI=mongodb://localhost:27017
   
   # Linux/macOS
   export LANESWAP_MONGODB_URI=mongodb://localhost:27017
   ```

## Running Without MongoDB

LaneSwap can run without MongoDB, but heartbeat data will not be persisted between restarts. To run without MongoDB:

```bash
# Set empty MongoDB URI to disable MongoDB integration
export LANESWAP_MONGODB_URI=""

# Or in .env file
# LANESWAP_MONGODB_URI=
```

## Example Services

LaneSwap includes several example services to help you get started:

```bash
# Start a simple service that sends heartbeats every 5 seconds
python -m laneswap.examples.simple_service

# Start a service that reports progress on a long-running task
python -m laneswap.examples.progress_service

# Test Discord webhook notifications
python -m laneswap.examples.discord_webhook_example
```

## API Reference

### Register a Service

```
POST /api/services
```

Request body:
```json
{
  "name": "my-service",
  "metadata": {
    "version": "1.0.0",
    "environment": "production"
  }
}
```

Response:
```json
{
  "service_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "my-service",
  "status": "unknown",
  "created_at": "2023-09-01T12:00:00Z",
  "last_heartbeat": null,
  "metadata": {
    "version": "1.0.0",
    "environment": "production"
  }
}
```

### Send a Heartbeat

```
POST /api/services/{service_id}/heartbeat
```

Request body:
```json
{
  "status": "healthy",
  "message": "Service is running normally",
  "metadata": {
    "cpu_usage": 25,
    "memory_usage": 150
  }
}
```

Response:
```json
{
  "service_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "healthy",
  "timestamp": "2023-09-01T12:01:00Z",
  "message": "Service is running normally",
  "metadata": {
    "cpu_usage": 25,
    "memory_usage": 150
  }
}
```

### Get All Services

```
GET /api/services
```

Response:
```json
{
  "services": [
    {
      "service_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "my-service",
      "status": "healthy",
      "created_at": "2023-09-01T12:00:00Z",
      "last_heartbeat": "2023-09-01T12:01:00Z",
      "metadata": {
        "version": "1.0.0",
        "environment": "production"
      }
    }
  ]
}
```

### Get Service Status

```
GET /api/services/{service_id}
```

Response:
```json
{
  "service_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "my-service",
  "status": "healthy",
  "created_at": "2023-09-01T12:00:00Z",
  "last_heartbeat": "2023-09-01T12:01:00Z",
  "message": "Service is running normally",
  "metadata": {
    "version": "1.0.0",
    "environment": "production"
  }
}
```

## Advanced Usage

### Using the Heartbeat Decorator

You can use the `with_heartbeat` decorator to automatically send heartbeats when a function is called:

```python
from laneswap.core.heartbeat import with_heartbeat
from laneswap.core.types import HeartbeatStatus

@with_heartbeat(
    service_id="my-service",
    success_status=HeartbeatStatus.HEALTHY,
    error_status=HeartbeatStatus.ERROR
)
async def my_function():
    # Do something
    return "Success"
```

### Using the Heartbeat Context Manager

You can use the `heartbeat_system` context manager to initialize and clean up the heartbeat system:

```python
from laneswap.core.heartbeat import heartbeat_system
from laneswap.adapters.mongodb import MongoDBAdapter
from laneswap.adapters.discord import DiscordWebhookAdapter

async def main():
    # Create adapters
    mongodb = MongoDBAdapter("mongodb://localhost:27017")
    discord = DiscordWebhookAdapter("https://discord.com/api/webhooks/...")
    
    # Initialize the heartbeat system
    async with heartbeat_system(
        notifiers=[discord],
        storage=mongodb,
        check_interval=30,
        stale_threshold=60
    ):
        # The heartbeat system is now running
        # Register services and send heartbeats
        pass
    
    # The heartbeat system is now stopped
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.