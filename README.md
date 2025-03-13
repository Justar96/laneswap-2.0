# LaneSwap

A lightweight, reliable service monitoring system for distributed applications built with FastAPI and Python.

## Overview

LaneSwap is a Python library that helps you monitor the health of your applications and services. Think of it as a "health check" system that lets you know when something goes wrong with your services.

### What is a Heartbeat?

In distributed systems, a "heartbeat" is a periodic signal sent by a service to indicate that it's still running and healthy. It's similar to a person's heartbeat - as long as you can detect it, you know the person is alive.

With LaneSwap:
- Your services send regular "I'm alive and healthy" messages (heartbeats)
- If a service stops sending heartbeats, LaneSwap detects this and can notify you
- You can view the status of all your services in a colorful terminal dashboard

This is especially useful in microservice architectures where you have many services running independently.

## Key Features

- **Real-time Health Monitoring**: Track the operational status of all your services
- **Automatic Stale Detection**: Get notified when services stop sending heartbeats
- **Terminal Dashboard**: Beautiful, colorful terminal UI for monitoring service health
- **Progress Tracking**: Monitor long-running tasks with detailed progress updates
- **Flexible Notifications**: Get alerts via Discord when service status changes
- **Low Overhead**: Minimal impact on your services' performance
- **Easy Integration**: Simple API for sending heartbeats from any service
- **MongoDB Integration**: Persistent storage of heartbeat data
- **Discord Notifications**: Real-time alerts via Discord webhooks
- **Async Support**: Built with asyncio for high performance
- **Comprehensive CLI**: Command-line tools for managing and monitoring services

## Documentation

- [API Documentation](laneswap/docs/API.md): Detailed information about the LaneSwap client API
- [Troubleshooting Guide](laneswap/docs/TROUBLESHOOTING.md): Solutions for common issues
- [Migration Guide](laneswap/docs/MIGRATION.md): Guide for migrating from incorrect usage patterns
- [Example Applications](laneswap/examples/): Working examples of LaneSwap integration

## Quick Start Guide

### 1. Installation

Install LaneSwap using pip:

```bash
pip install laneswap
```

For a complete installation with all dependencies:

```bash
pip install laneswap[all]
```

### 2. Start the API Server

The API server receives heartbeats from your services. Start it with:

```bash
python -m laneswap.api.server
```

This will start the API server on port 8000. You should see output indicating the server is running.

### 3. Monitor Your Services

Start the terminal dashboard to see the status of your services:

```bash
laneswap-term --api-url http://localhost:8000
```

### 4. Integrate LaneSwap into Your Application

#### Using the Async Client (for async/await applications)

```python
from laneswap.client.async_client import LaneswapAsyncClient
import asyncio

async def main():
    # Create a client - this connects to the LaneSwap API server
    client = LaneswapAsyncClient(
        api_url="http://localhost:8000",  # URL of your LaneSwap API server
        service_name="my-service",        # Name of your service
        auto_heartbeat=True,              # Automatically send heartbeats
        heartbeat_interval=30             # Send a heartbeat every 30 seconds
    )
    
    # Connect to the API (registers your service)
    await client.connect()
    
    try:
        # Your application logic here
        print("Service is running...")
        await asyncio.sleep(300)  # Run for 5 minutes
    finally:
        # Always close the client when done
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

#### Using the Sync Client (for traditional Python applications)

```python
from laneswap.client.sync_client import LaneswapSyncClient
import time

# Create a client
client = LaneswapSyncClient(
    api_url="http://localhost:8000",  # URL of your LaneSwap API server
    service_name="my-service",        # Name of your service
    auto_heartbeat=True,              # Automatically send heartbeats
    heartbeat_interval=30             # Send a heartbeat every 30 seconds
)

# Connect to the API (registers your service)
client.connect()

try:
    # Your application logic here
    print("Service is running...")
    time.sleep(300)  # Run for 5 minutes
finally:
    # Always close the client when done
    client.close()
```

#### Using Context Managers (recommended)

For cleaner code, you can use context managers:

```python
# Async context manager
async def run_service():
    async with LaneswapAsyncClient(
        api_url="http://localhost:8000",
        service_name="my-service",
        auto_heartbeat=True
    ) as client:
        # Your application logic here
        print("Service is running...")
        await asyncio.sleep(300)  # Run for 5 minutes
        
# Sync context manager
def run_service():
    with LaneswapSyncClient(
        api_url="http://localhost:8000",
        service_name="my-service",
        auto_heartbeat=True
    ) as client:
        # Your application logic here
        print("Service is running...")
        time.sleep(300)  # Run for 5 minutes
```

## Common Issues and Troubleshooting

If you encounter issues while using LaneSwap, please refer to our [Troubleshooting Guide](laneswap/docs/TROUBLESHOOTING.md) for solutions to common problems.

Some common issues include:
- API server not running
- Incorrect API URL
- Network connectivity issues
- Missing dependencies

## Configuration

LaneSwap can be configured using environment variables or a configuration file:

### Using Environment Variables

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

### Using a .env File

Create a `.env` file in your project directory:

```
LANESWAP_MONGODB_URI=mongodb://localhost:27017
LANESWAP_DISCORD_WEBHOOK=https://discord.com/api/webhooks/...
LANESWAP_CHECK_INTERVAL=30
LANESWAP_STALE_THRESHOLD=60
```

## Terminal Monitor

The terminal monitor provides a colorful dashboard for monitoring your services in real-time.

### Starting the Terminal Monitor

```bash
# Basic usage
laneswap-term --api-url http://localhost:8000

# With custom refresh interval (5 seconds)
laneswap-term --api-url http://localhost:8000 --refresh 5.0

# Start in paused mode (no auto-refresh until you press SPACE)
laneswap-term --api-url http://localhost:8000 --paused
```

### Terminal Monitor Keyboard Controls

- **SPACE**: Pause/resume auto-refresh (useful for scrolling through service data)
- **CTRL+C**: Exit the monitor

### Example Terminal Monitor Output

```
┌─────────────────────────────────────────────────────────────────┐
│                         LaneSwap Monitor                         │
├─────────────────────────────────────────────────────────────────┤
│ Services: 5 | Healthy: 3 | Warning: 1 | Error: 1 | Stale: 0     │
├─────────────────────────────────────────────────────────────────┤
│ ID                  | Name           | Status  | Last Heartbeat │
├─────────────────────────────────────────────────────────────────┤
│ 123abc456def        | API Server     | HEALTHY | 5s ago         │
│ 789ghi101jkl        | Database       | HEALTHY | 12s ago        │
│ 202mno303pqr        | Auth Service   | WARNING | 25s ago        │
│ 404stu505vwx        | Payment System | ERROR   | 1m ago         │
│ 606yza707bcd        | User Service   | HEALTHY | 8s ago         │
└─────────────────────────────────────────────────────────────────┘
```

## Progress Tracking

LaneSwap includes a progress tracking system for monitoring long-running tasks:

```python
from laneswap.client.async_client import LaneswapAsyncClient
import asyncio

async def main():
    async with LaneswapAsyncClient(
        api_url="http://localhost:8000",
        service_name="data-processor"
    ) as client:
        # Start a progress task
        task_id = await client.start_progress(
            task_name="Data Processing",
            total_steps=100,
            description="Processing large dataset"
        )
        
        # Update progress as the task progresses
        for i in range(100):
            # Do some work
            await asyncio.sleep(0.1)
            
            # Update the progress
            await client.update_progress(
                task_id=task_id,
                current_step=i+1,
                status="running",
                message=f"Processing item {i+1}/100"
            )
        
        # Complete the progress task
        await client.complete_progress(
            task_id=task_id,
            status="completed",
            message="Data processing completed successfully"
        )

if __name__ == "__main__":
    asyncio.run(main())
```

## Command Line Interface

LaneSwap provides a comprehensive command-line interface for managing and monitoring services:

```bash
# Start the server
laneswap server

# List all registered services
laneswap services list

# Get details for a specific service
laneswap services get <service-id>

# Send a heartbeat for a service
laneswap services heartbeat <service-id> --status healthy

# Start the terminal monitor
laneswap-term --api-url http://localhost:8000
```

## System Architecture

LaneSwap consists of several main components:

1. **Core Module**: Contains the central heartbeat management system
2. **API Server**: FastAPI-based server that receives heartbeats from services
3. **Client Library**: Clients for sending heartbeats from your services
4. **Adapters**: Pluggable storage and notification backends
5. **Terminal Monitor**: Colorful terminal dashboard for monitoring service health
6. **CLI**: Command-line interface for interacting with the system
7. **Models**: Data models and schemas

## Example Applications

Check out the example applications in the `laneswap/examples/` directory:

- `simple_service.py`: A basic service that sends heartbeats
- `weather_app_example.py`: A more complex example of a weather service
- `sync_client_example.py`: Example using the synchronous client
- `progress_service.py`: Example of tracking progress for long-running tasks

## Running Without MongoDB

LaneSwap can run without MongoDB, but heartbeat data will not be persisted between restarts. To run without MongoDB:

```bash
# Set empty MongoDB URI to disable MongoDB integration
export LANESWAP_MONGODB_URI=""
```

## Next Steps

1. Try the [example applications](laneswap/examples/) to see LaneSwap in action
2. Read the [API Documentation](laneswap/docs/API.md) for detailed information
3. Check out the [Troubleshooting Guide](laneswap/docs/TROUBLESHOOTING.md) if you encounter issues

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.