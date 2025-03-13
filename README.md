# LaneSwap

A lightweight, reliable service monitoring system for distributed applications built with FastAPI and Python.

## Overview

LaneSwap is a Python library that provides real-time monitoring of service health in distributed systems. It allows services to send periodic heartbeats to indicate their operational status and automatically detects when services become unresponsive.

## Key Features

- **Real-time Health Monitoring**: Track the operational status of all your services
- **Automatic Stale Detection**: Identify services that have stopped sending heartbeats
- **Terminal Dashboard**: Beautiful, colorful terminal UI for monitoring service health
- **Progress Tracking**: Monitor long-running tasks with detailed progress updates
- **Flexible Notifications**: Send alerts through various channels when service status changes
- **Low Overhead**: Minimal impact on your services' performance
- **Easy Integration**: Simple API for sending heartbeats from any service
- **MongoDB Integration**: Persistent storage of heartbeat data
- **Discord Notifications**: Real-time alerts via Discord webhooks
- **Async Support**: Built with asyncio for high performance
- **Comprehensive CLI**: Command-line tools for managing and monitoring services

## System Architecture

LaneSwap consists of several main components:

1. **Core Module**: Contains the central heartbeat management system and configuration
   - `heartbeat.py`: Core heartbeat management functionality
   - `config.py`: Configuration management with environment variable support
   - `progress.py`: Progress tracking for long-running tasks
   - `validator.py`: System validation and health checking
   - `types.py`: Type definitions and enums
   - `exceptions.py`: Custom exception classes

2. **API Server**: FastAPI-based server that receives heartbeats from services
   - `main.py`: Main FastAPI application with lifespan management
   - `server.py`: Server startup and configuration
   - `routers/`: API endpoint definitions
   - `middleware/`: Request/response middleware

3. **Client Library**: Async client for sending heartbeats from your services
   - `async_client.py`: Asynchronous client with context manager support

4. **Adapters**: Pluggable storage and notification backends
   - `mongodb.py`: MongoDB storage adapter
   - `discord.py`: Discord webhook notification adapter
   - `base.py`: Base adapter interfaces

5. **Terminal Monitor**: Colorful terminal dashboard for monitoring service health
   - `monitor.py`: Terminal UI implementation
   - `colors.py`: Terminal color utilities
   - `ascii_art.py`: ASCII art for terminal display

6. **CLI**: Command-line interface for interacting with the system
   - `commands.py`: Main CLI command definitions
   - `service_commands.py`: Service-specific commands
   - `terminal_monitor.py`: CLI for terminal monitor
   - `validate.py`: Validation commands

7. **Models**: Data models and schemas
   - `heartbeat.py`: Heartbeat and service models
   - `error.py`: Error logging models
   - `progress.py`: Progress tracking models

## Quick Start

### Installation

```bash
pip install laneswap
```

For a complete installation with all dependencies:

```bash
pip install laneswap[all]
```

### Start the API Server

```bash
python -m laneswap.api.server
```

This will start the API server on port 8000.

### Command Line Options

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

## Terminal Monitor Features

The terminal monitor provides a comprehensive dashboard for monitoring your services:

- **Real-time Updates**: See service status changes as they happen
- **Color-coded Status**: Quickly identify service health with color indicators
- **Automatic Refresh**: Configurable refresh interval
- **Summary Statistics**: Overview of service health status
- **Detailed Service Information**: View complete service information including latency and last heartbeat
- **Keyboard Shortcuts**: Easy navigation with keyboard shortcuts
- **Auto-detection**: Automatically detects if a terminal is available
- **Headless Mode**: Can run in non-terminal mode for headless environments
- **Scroll Preservation**: Preserves terminal scroll history for better navigation
- **Pause/Resume**: Press SPACE to pause/resume auto-refresh for uninterrupted viewing
- **Stable UI**: Consistent and stable terminal UI that handles window resizing
- **Priority Sorting**: Services are sorted by status (critical first) and then by name
- **Adaptive Display**: Automatically adjusts to terminal size and shows the most important services

### Starting the Terminal Monitor

You can start the terminal monitor in several ways:

```bash
# Using the CLI entry point
laneswap-term --api-url http://localhost:8000

# Using the CLI with custom refresh interval
laneswap-term --api-url http://localhost:8000 --refresh 5.0

# Run in non-terminal mode (logging only, no UI)
laneswap-term --api-url http://localhost:8000 --no-terminal

# Force terminal mode even if no terminal is detected
laneswap-term --api-url http://localhost:8000 --force-terminal

# Start in paused mode (no auto-refresh until you press SPACE)
laneswap-term --api-url http://localhost:8000 --paused

# From Python code
from laneswap.terminal import start_monitor
import asyncio

# Auto-detect terminal availability
asyncio.run(start_monitor(api_url="http://localhost:8000", refresh_interval=2.0))

# Force non-terminal mode
asyncio.run(start_monitor(api_url="http://localhost:8000", refresh_interval=2.0, use_terminal=False))

# Start in paused mode
asyncio.run(start_monitor(api_url="http://localhost:8000", refresh_interval=2.0, start_paused=True))
```

### Terminal Monitor Keyboard Controls

While the terminal monitor is running, you can use these keyboard controls:

- **SPACE**: Pause/resume auto-refresh (useful for scrolling through service data)
- **CTRL+C**: Exit the monitor

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

## System Check

To verify that all components of the LaneSwap system are working correctly, you can run the validation command:

```bash
# Run validation with default options
laneswap validate

# Skip web monitor validation
laneswap validate --no-web-monitor

# Treat warnings as errors
laneswap validate --strict

# Run validation without printing results
laneswap validate --quiet
```

You can also run the validation script directly:

```bash
python -m laneswap.examples.verify_installation
```

The validation checks:
- All required dependencies are installed
- Key LaneSwap components can be imported
- Overall system status

If any issues are found, the validator will provide detailed information to help you fix them.

### Automatic Validation

LaneSwap automatically runs validation when:
1. A service is registered for the first time
2. The heartbeat system is initialized
3. The CLI is started

This ensures that any potential issues are detected early, before they cause problems in production.

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

# Start the terminal monitor with a mock API server for demonstration
python -m laneswap.examples.mock_api_server  # Start the mock API server
python -m laneswap.examples.terminal_monitor_example  # Start the terminal monitor
```

### Mock API Server

For testing and demonstration purposes, LaneSwap includes a mock API server that simulates service data without requiring a full setup:

```bash
# Start the mock API server
python -m laneswap.examples.mock_api_server

# Connect the terminal monitor to the mock server
python -m laneswap.examples.terminal_monitor_example --api-url http://localhost:8000

# Connect in non-terminal mode (for headless environments or CI/CD pipelines)
python -m laneswap.examples.terminal_monitor_example --api-url http://localhost:8000 --no-terminal
```

The mock server generates random service data and periodically updates service statuses to demonstrate the terminal monitor's real-time capabilities. The non-terminal mode is useful for automated testing, CI/CD pipelines, or running in headless environments.

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

### Track Progress

```
POST /api/progress
```

Request body:
```json
{
  "service_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_name": "Data Processing",
  "total_steps": 100,
  "description": "Processing large dataset"
}
```

Response:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440001",
  "service_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_name": "Data Processing",
  "total_steps": 100,
  "current_step": 0,
  "status": "pending",
  "created_at": "2023-09-01T12:00:00Z",
  "updated_at": "2023-09-01T12:00:00Z",
  "description": "Processing large dataset"
}
```

### Update Progress

```
PUT /api/progress/{task_id}
```

Request body:
```json
{
  "current_step": 50,
  "status": "running",
  "message": "Processing item 50/100"
}
```

Response:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440001",
  "service_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_name": "Data Processing",
  "total_steps": 100,
  "current_step": 50,
  "status": "running",
  "created_at": "2023-09-01T12:00:00Z",
  "updated_at": "2023-09-01T12:05:00Z",
  "description": "Processing large dataset",
  "message": "Processing item 50/100",
  "percent_complete": 50
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

## Integration Testing

For information on running integration tests, see [INTEGRATION_TESTS.md](INTEGRATION_TESTS.md).

## Contributing

For information on contributing to LaneSwap, see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.