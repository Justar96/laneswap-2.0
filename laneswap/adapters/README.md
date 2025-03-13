# LaneSwap Adapters Module

The adapters module provides pluggable storage and notification backends for the LaneSwap system, allowing for flexible integration with various external systems.

## Components

### Base Adapters (`base.py`)

Defines the base interfaces for storage and notification adapters.

#### Key Interfaces

- **StorageAdapter**: Interface for storing and retrieving heartbeat data
- **NotifierAdapter**: Interface for sending notifications about service status changes

#### Usage Example

```python
from laneswap.adapters.base import StorageAdapter, NotifierAdapter
from laneswap.models.heartbeat import ServiceHeartbeat, ServiceStatus

class CustomStorageAdapter(StorageAdapter):
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

class CustomNotifierAdapter(NotifierAdapter):
    async def notify_status_change(self, service_id: str, old_status: str, new_status: str):
        # Send a notification
        pass
    
    # Implement other required methods...
```

### MongoDB Adapter (`mongodb.py`)

Provides a MongoDB-based storage adapter for persisting heartbeat data.

#### Key Features

- **Async Operations**: Uses Motor for asynchronous MongoDB operations
- **Automatic Indexing**: Creates necessary indexes for efficient queries
- **Connection Management**: Handles MongoDB connection lifecycle
- **Error Handling**: Comprehensive error handling for MongoDB operations
- **Query Optimization**: Optimized queries for heartbeat and service data
- **TTL Indexes**: Time-to-live indexes for automatic data cleanup

#### Usage Example

```python
from laneswap.adapters.mongodb import MongoDBAdapter
from laneswap.core.heartbeat import get_manager

# Create the MongoDB adapter
mongodb = MongoDBAdapter(
    connection_string="mongodb://localhost:27017",
    database_name="laneswap",
    heartbeats_collection="heartbeats",
    errors_collection="errors"
)

# Initialize the adapter
await mongodb.initialize()

# Add the adapter to the heartbeat manager
manager = get_manager()
manager.add_storage_adapter(mongodb)

# Close the adapter when done
await mongodb.close()
```

### Discord Adapter (`discord.py`)

Provides a Discord webhook-based notification adapter for sending alerts about service status changes.

#### Key Features

- **Webhook Integration**: Sends notifications via Discord webhooks
- **Message Formatting**: Rich message formatting with embeds
- **Color Coding**: Color-coded messages based on service status
- **Rate Limiting**: Respects Discord's rate limits
- **Error Handling**: Handles webhook errors gracefully
- **Customizable Appearance**: Configurable username and avatar

#### Usage Example

```python
from laneswap.adapters.discord import DiscordWebhookAdapter
from laneswap.core.heartbeat import get_manager

# Create the Discord adapter
discord = DiscordWebhookAdapter(
    webhook_url="https://discord.com/api/webhooks/...",
    username="LaneSwap Monitor",
    avatar_url="https://example.com/avatar.png"
)

# Add the adapter to the heartbeat manager
manager = get_manager()
manager.add_notifier_adapter(discord)
```

## Adapter Interfaces

### StorageAdapter Interface

The `StorageAdapter` interface defines the following methods:

- `initialize()`: Initialize the storage adapter
- `close()`: Close the storage adapter
- `store_heartbeat(heartbeat)`: Store a heartbeat
- `get_service_status(service_id)`: Get the status of a service
- `get_all_services()`: Get all registered services
- `get_service_heartbeats(service_id, limit)`: Get recent heartbeats for a service
- `register_service(service)`: Register a new service
- `delete_service(service_id)`: Delete a service
- `store_error(error)`: Store an error log
- `get_errors(service_id, limit)`: Get recent errors for a service

### NotifierAdapter Interface

The `NotifierAdapter` interface defines the following methods:

- `notify_status_change(service_id, old_status, new_status)`: Notify about a service status change
- `notify_error(service_id, error_message)`: Notify about a service error
- `notify_stale_service(service_id, last_heartbeat)`: Notify about a stale service
- `notify_service_recovery(service_id)`: Notify about a service recovery

## Integration with Other Modules

The adapters module integrates with other LaneSwap modules:

- **Core Module**: Adapters are used by the heartbeat manager
- **Models Module**: Adapters use data models for storing and retrieving data
- **API Module**: Adapters are indirectly used by the API server through the core module

## Creating Custom Adapters

### Custom Storage Adapter

To create a custom storage adapter, implement the `StorageAdapter` interface:

```python
from laneswap.adapters.base import StorageAdapter
from laneswap.models.heartbeat import ServiceHeartbeat, ServiceStatus, ServiceRegistration
from laneswap.models.error import ErrorLog
from typing import List, Optional
import asyncio

class CustomStorageAdapter(StorageAdapter):
    async def initialize(self):
        # Initialize your storage system
        # E.g., connect to a database, create tables, etc.
        pass
    
    async def close(self):
        # Close connections, clean up resources
        pass
    
    async def store_heartbeat(self, heartbeat: ServiceHeartbeat):
        # Store a heartbeat in your storage system
        # This is called whenever a service sends a heartbeat
        pass
    
    async def get_service_status(self, service_id: str) -> Optional[ServiceStatus]:
        # Retrieve the current status of a service
        # Return None if the service doesn't exist
        pass
    
    async def get_all_services(self) -> List[ServiceStatus]:
        # Retrieve all registered services with their current status
        pass
    
    async def get_service_heartbeats(self, service_id: str, limit: int = 10) -> List[ServiceHeartbeat]:
        # Retrieve recent heartbeats for a service
        # Limit the number of results to 'limit'
        pass
    
    async def register_service(self, service: ServiceRegistration) -> str:
        # Register a new service
        # Return the service ID
        pass
    
    async def delete_service(self, service_id: str) -> bool:
        # Delete a service and all its heartbeats
        # Return True if successful, False otherwise
        pass
    
    async def store_error(self, error: ErrorLog):
        # Store an error log
        pass
    
    async def get_errors(self, service_id: str, limit: int = 10) -> List[ErrorLog]:
        # Retrieve recent errors for a service
        # Limit the number of results to 'limit'
        pass
```

### Custom Notifier Adapter

To create a custom notifier adapter, implement the `NotifierAdapter` interface:

```python
from laneswap.adapters.base import NotifierAdapter
from datetime import datetime

class CustomNotifierAdapter(NotifierAdapter):
    async def notify_status_change(self, service_id: str, old_status: str, new_status: str):
        # Send a notification when a service's status changes
        # E.g., send an email, SMS, or push notification
        pass
    
    async def notify_error(self, service_id: str, error_message: str):
        # Send a notification when a service reports an error
        pass
    
    async def notify_stale_service(self, service_id: str, last_heartbeat: datetime):
        # Send a notification when a service becomes stale
        # (hasn't sent a heartbeat in a while)
        pass
    
    async def notify_service_recovery(self, service_id: str):
        # Send a notification when a service recovers from an error
        # or stale state
        pass
```

## Best Practices

1. **Error Handling**: Implement robust error handling in your adapters
2. **Async Operations**: Use asynchronous operations for all I/O-bound tasks
3. **Connection Pooling**: Use connection pooling for database adapters
4. **Resource Cleanup**: Properly close connections and clean up resources
5. **Rate Limiting**: Respect rate limits for external services
6. **Retry Logic**: Implement retry logic for transient errors
7. **Logging**: Log adapter operations for debugging
8. **Configuration**: Make adapters configurable for different environments
9. **Testing**: Write tests for your adapters
10. **Documentation**: Document your adapter's behavior and requirements 