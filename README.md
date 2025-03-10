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
```

### Start the Web Monitor

```bash
python -m laneswap.examples.start_monitor
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

if __name__ == "__main__":
    asyncio.run(main())
```

## System Architecture

LaneSwap consists of three main components:

1. **API Server**: Receives heartbeats from services and stores their status
2. **Web Monitor**: Provides a real-time dashboard for monitoring service health
3. **Client Library**: Makes it easy to send heartbeats from your services

## Configuration

LaneSwap can be configured using environment variables or a configuration file:

```bash
# Set the MongoDB connection string
export LANESWAP_MONGODB_URI="mongodb://localhost:27017"

# Set the Discord webhook URL for notifications
export LANESWAP_DISCORD_WEBHOOK="https://discord.com/api/webhooks/..."
```

Or create a `config.yaml` file:

```yaml
storage:
  type: mongodb
  uri: mongodb://localhost:27017
  database: laneswap

notifications:
  discord:
    webhook: https://discord.com/api/webhooks/...
```

## Web Monitor Features

The web monitor provides a comprehensive dashboard for monitoring your services:

- **Real-time Updates**: See service status changes as they happen
- **Search and Filtering**: Quickly find specific services
- **Grid and Table Views**: Choose the view that works best for you
- **Dark/Light Themes**: Customize the interface to your preference
- **Detailed Service Information**: View complete service history and metadata

## Adding a New Language

To add a new language to the web monitor:

1. Open `laneswap/examples/web_monitor/i18n.js`
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

## Example Services

LaneSwap includes several example services to help you get started:

```bash
# Start a simple service that sends heartbeats every 5 seconds
python -m laneswap.examples.simple_service

# Start a service that reports progress on a long-running task
python -m laneswap.examples.progress_service
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

### Get All Services

```
GET /api/services
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.