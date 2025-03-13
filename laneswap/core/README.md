# LaneSwap Core Module

The core module contains the central components of the LaneSwap system, providing the foundation for heartbeat monitoring, configuration management, progress tracking, and system validation.

## Components

### Heartbeat Manager (`heartbeat.py`)

The `HeartbeatManager` is the central component of the LaneSwap system, responsible for:

- Managing service registrations
- Processing heartbeats from services
- Detecting stale services
- Notifying about service status changes
- Coordinating storage and notification adapters

#### Key Features

- **Singleton Pattern**: Global access to a single heartbeat manager instance
- **Async Monitor**: Background task for checking service health
- **Pluggable Adapters**: Support for custom storage and notification adapters
- **Decorator Support**: `with_heartbeat` decorator for automatic heartbeat sending
- **Context Manager**: `heartbeat_system` context manager for easy initialization

#### Usage Example

```python
from laneswap.core.heartbeat import HeartbeatManager, get_manager

# Get the singleton instance
manager = get_manager()

# Register a service
service_id = await manager.register_service(name="my-service")

# Send a heartbeat
await manager.process_heartbeat(
    service_id=service_id,
    status="healthy",
    message="Service is running normally"
)

# Start the monitor
await manager.start_monitor(check_interval=30, stale_threshold=60)

# Stop the monitor
await manager.stop_monitor()
```

### Configuration (`config.py`)

The configuration module provides a flexible way to configure the LaneSwap system using environment variables, configuration files, or programmatic settings.

#### Key Features

- **Environment Variable Support**: Load configuration from environment variables
- **Dotenv Support**: Load configuration from `.env` files
- **Pydantic Models**: Type-safe configuration with validation
- **Nested Configuration**: Hierarchical configuration structure
- **Default Values**: Sensible defaults for all configuration options

#### Configuration Options

- **API Server**:
  - `host`: API server host (default: "0.0.0.0")
  - `port`: API server port (default: 8000)
  - `cors_origins`: CORS allowed origins (default: ["*"])
  - `debug`: Enable debug mode (default: false)

- **Heartbeat**:
  - `check_interval`: Interval for checking service health in seconds (default: 30)
  - `stale_threshold`: Time in seconds after which a service is considered stale (default: 60)

- **MongoDB**:
  - `connection_string`: MongoDB connection string
  - `database_name`: MongoDB database name (default: "laneswap")
  - `heartbeats_collection`: Collection for heartbeats (default: "heartbeats")
  - `errors_collection`: Collection for errors (default: "errors")

- **Discord**:
  - `webhook_url`: Discord webhook URL
  - `username`: Username for Discord messages (default: "LaneSwap")
  - `avatar_url`: Avatar URL for Discord messages

#### Usage Example

```python
from laneswap.core.config import get_settings, configure

# Get the current settings
settings = get_settings()

# Configure programmatically
configure({
    "api": {
        "port": 9000
    },
    "heartbeat": {
        "check_interval": 15,
        "stale_threshold": 45
    },
    "mongodb": {
        "connection_string": "mongodb://localhost:27017",
        "database_name": "my_app"
    }
})

# Get the updated settings
settings = get_settings()
```

### Progress Tracking (`progress.py`)

The progress tracking module provides functionality for monitoring long-running tasks, with support for:

- Creating progress tasks
- Updating task progress
- Completing tasks
- Retrieving task status

#### Key Features

- **Task Management**: Create, update, and complete progress tasks
- **Percentage Calculation**: Automatic calculation of completion percentage
- **Status Tracking**: Track task status (pending, running, completed, failed)
- **Metadata Support**: Store additional information with progress updates
- **Integration with Storage**: Persist progress data using storage adapters

#### Usage Example

```python
from laneswap.core.progress import ProgressManager
from laneswap.core.heartbeat import get_manager

# Get the heartbeat manager
heartbeat_manager = get_manager()

# Create a progress manager
progress_manager = ProgressManager(heartbeat_manager)

# Start a progress task
task_id = await progress_manager.start_progress(
    service_id="my-service",
    task_name="Data Processing",
    total_steps=100,
    description="Processing large dataset"
)

# Update progress
await progress_manager.update_progress(
    task_id=task_id,
    current_step=50,
    status="running",
    message="Processing item 50/100"
)

# Complete the task
await progress_manager.complete_progress(
    task_id=task_id,
    status="completed",
    message="Data processing completed successfully"
)
```

### System Validation (`validator.py`)

The system validation module provides tools for verifying that the LaneSwap system is correctly installed and configured.

#### Key Features

- **Dependency Checking**: Verify that all required dependencies are installed
- **Import Validation**: Check that key components can be imported
- **Configuration Validation**: Verify that the configuration is valid
- **Connectivity Testing**: Test connections to external services (MongoDB, Discord)
- **Detailed Reporting**: Provide detailed information about validation results

#### Usage Example

```python
from laneswap.core.validator import SystemValidator

# Create a validator
validator = SystemValidator()

# Run validation
results = await validator.validate()

# Check if validation passed
if results.passed:
    print("System validation passed!")
else:
    print("System validation failed:")
    for error in results.errors:
        print(f"- {error}")
```

### Types and Enums (`types.py`)

The types module provides type definitions and enums used throughout the LaneSwap system.

#### Key Types

- **HeartbeatStatus**: Enum for service status (HEALTHY, WARNING, ERROR, CRITICAL, UNKNOWN)
- **ProgressStatus**: Enum for progress task status (PENDING, RUNNING, COMPLETED, FAILED)
- **ServiceID**: Type alias for service identifiers
- **TaskID**: Type alias for progress task identifiers

#### Usage Example

```python
from laneswap.core.types import HeartbeatStatus, ProgressStatus

# Use status enums
status = HeartbeatStatus.HEALTHY
progress_status = ProgressStatus.RUNNING

# Check status
if status == HeartbeatStatus.HEALTHY:
    print("Service is healthy")
```

### Exceptions (`exceptions.py`)

The exceptions module provides custom exception classes for the LaneSwap system.

#### Key Exceptions

- **LaneswapError**: Base exception class for all LaneSwap errors
- **ServiceNotFoundError**: Raised when a service is not found
- **InvalidServiceIDError**: Raised when an invalid service ID is provided
- **InvalidHeartbeatError**: Raised when an invalid heartbeat is provided
- **StorageError**: Raised when a storage operation fails
- **NotifierError**: Raised when a notification operation fails

#### Usage Example

```python
from laneswap.core.exceptions import ServiceNotFoundError

try:
    # Try to get a service that doesn't exist
    service = await manager.get_service("non-existent-id")
except ServiceNotFoundError as e:
    print(f"Service not found: {e}")
```

## Integration with Other Modules

The core module integrates with other LaneSwap modules:

- **API Module**: The API server uses the heartbeat manager to process API requests
- **Client Module**: The client library communicates with the API server
- **Adapters Module**: Storage and notification adapters plug into the heartbeat manager
- **Terminal Module**: The terminal monitor displays data from the heartbeat manager
- **CLI Module**: The CLI commands interact with the heartbeat manager

## Advanced Usage

### Custom Adapters

You can create custom storage and notification adapters by implementing the `StorageAdapter` and `NotifierAdapter` interfaces:

```python
from laneswap.adapters.base import StorageAdapter, NotifierAdapter
from laneswap.models.heartbeat import ServiceHeartbeat, ServiceStatus

class MyStorageAdapter(StorageAdapter):
    async def initialize(self):
        # Initialize the storage
        pass
    
    async def store_heartbeat(self, heartbeat: ServiceHeartbeat):
        # Store a heartbeat
        pass
    
    async def get_service_status(self, service_id: str) -> ServiceStatus:
        # Get service status
        pass
    
    # Implement other required methods...

class MyNotifierAdapter(NotifierAdapter):
    async def notify_status_change(self, service_id: str, old_status: str, new_status: str):
        # Send a notification
        pass
    
    # Implement other required methods...

# Add the adapters to the manager
manager = get_manager()
manager.add_storage_adapter(MyStorageAdapter())
manager.add_notifier_adapter(MyNotifierAdapter())
```

### Custom Heartbeat Processing

You can customize how heartbeats are processed by extending the `HeartbeatManager` class:

```python
from laneswap.core.heartbeat import HeartbeatManager
from laneswap.models.heartbeat import ServiceHeartbeat

class CustomHeartbeatManager(HeartbeatManager):
    async def process_heartbeat(self, service_id: str, status: str, message: str = None, metadata: dict = None):
        # Custom pre-processing
        if status == "warning" and "cpu_usage" in metadata and metadata["cpu_usage"] > 90:
            status = "critical"
            message = f"{message} (CPU usage critical: {metadata['cpu_usage']}%)"
        
        # Call the parent method
        return await super().process_heartbeat(service_id, status, message, metadata)

# Use the custom manager
custom_manager = CustomHeartbeatManager()
# Set it as the global manager
from laneswap.core.heartbeat import _set_manager
_set_manager(custom_manager)
```

## Best Practices

1. **Use the Singleton**: Always use `get_manager()` to access the heartbeat manager
2. **Initialize Early**: Start the heartbeat monitor early in your application lifecycle
3. **Clean Shutdown**: Stop the monitor during application shutdown
4. **Error Handling**: Handle exceptions from heartbeat operations
5. **Consistent Status**: Use the `HeartbeatStatus` enum for consistent status values
6. **Regular Heartbeats**: Send heartbeats at regular intervals (recommended: 15-30 seconds)
7. **Informative Messages**: Include useful information in heartbeat messages
8. **Metadata**: Use metadata to provide additional context for heartbeats
9. **Progress Tracking**: Use progress tracking for long-running tasks
10. **Validation**: Run system validation during application startup 