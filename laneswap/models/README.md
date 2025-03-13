# LaneSwap Models Module

The models module provides Pydantic data models for the LaneSwap system, ensuring type safety and validation for all data structures.

## Components

### Heartbeat Models (`heartbeat.py`)

Data models for service registration, heartbeats, and service status.

#### Key Models

- **ServiceRegistration**: Model for registering a new service
- **ServiceHeartbeat**: Model for service heartbeats
- **ServiceStatus**: Model for service status information
- **HeartbeatEvent**: Model for heartbeat events

#### Usage Example

```python
from laneswap.models.heartbeat import ServiceRegistration, ServiceHeartbeat, ServiceStatus
from datetime import datetime
import uuid

# Create a service registration
registration = ServiceRegistration(
    name="my-service",
    metadata={"version": "1.0.0", "environment": "production"}
)

# Create a service heartbeat
heartbeat = ServiceHeartbeat(
    service_id=str(uuid.uuid4()),
    status="healthy",
    timestamp=datetime.utcnow(),
    message="Service is running normally",
    metadata={"cpu_usage": 25, "memory_usage": 150}
)

# Create a service status
status = ServiceStatus(
    service_id=heartbeat.service_id,
    name="my-service",
    status="healthy",
    created_at=datetime.utcnow(),
    last_heartbeat=datetime.utcnow(),
    message="Service is running normally",
    metadata={"version": "1.0.0", "environment": "production"}
)
```

### Error Models (`error.py`)

Data models for error logging and error responses.

#### Key Models

- **ErrorLog**: Model for error logs
- **ErrorResponse**: Model for error responses

#### Usage Example

```python
from laneswap.models.error import ErrorLog, ErrorResponse
from datetime import datetime
import uuid

# Create an error log
error_log = ErrorLog(
    service_id=str(uuid.uuid4()),
    timestamp=datetime.utcnow(),
    error_type="RuntimeError",
    message="Failed to connect to database",
    stack_trace="Traceback (most recent call last):\n  ...",
    metadata={"attempt": 3, "retry": True}
)

# Create an error response
error_response = ErrorResponse(
    error_code="DB_CONNECTION_ERROR",
    message="Failed to connect to database",
    details="Connection timed out after 30 seconds",
    timestamp=datetime.utcnow()
)
```

### Progress Models (`progress.py`)

Data models for progress tracking of long-running tasks.

#### Key Models

- **ProgressTask**: Model for progress tasks
- **ProgressUpdate**: Model for progress updates
- **ProgressStatus**: Model for progress status information

#### Usage Example

```python
from laneswap.models.progress import ProgressTask, ProgressUpdate, ProgressStatus
from datetime import datetime
import uuid

# Create a progress task
task = ProgressTask(
    task_id=str(uuid.uuid4()),
    service_id=str(uuid.uuid4()),
    task_name="Data Processing",
    total_steps=100,
    current_step=0,
    status="pending",
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow(),
    description="Processing large dataset"
)

# Create a progress update
update = ProgressUpdate(
    task_id=task.task_id,
    current_step=50,
    status="running",
    message="Processing item 50/100"
)

# Create a progress status
status = ProgressStatus(
    task_id=task.task_id,
    service_id=task.service_id,
    task_name="Data Processing",
    total_steps=100,
    current_step=50,
    status="running",
    created_at=task.created_at,
    updated_at=datetime.utcnow(),
    description="Processing large dataset",
    message="Processing item 50/100",
    percent_complete=50
)
```

## Model Validation

All models include validation rules to ensure data integrity:

- **Required Fields**: Fields that must be provided
- **Field Types**: Type checking for all fields
- **Field Constraints**: Constraints on field values (e.g., min/max values)
- **Default Values**: Default values for optional fields
- **Computed Fields**: Fields that are computed from other fields

## Integration with Other Modules

The models module integrates with other LaneSwap modules:

- **API Module**: Models are used for request/response validation
- **Core Module**: Models are used for data structures
- **Adapters Module**: Models are used for storing and retrieving data
- **Client Module**: Models are used for API communication

## Advanced Usage

### Custom Validation

You can add custom validation to models using Pydantic validators:

```python
from pydantic import BaseModel, validator
from typing import Dict, Any, Optional
from datetime import datetime

class CustomServiceHeartbeat(BaseModel):
    service_id: str
    status: str
    timestamp: datetime = datetime.utcnow()
    message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @validator("status")
    def validate_status(cls, v):
        valid_statuses = ["healthy", "warning", "error", "critical", "unknown"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v
    
    @validator("metadata")
    def validate_metadata(cls, v):
        if v is not None and "cpu_usage" in v:
            cpu_usage = v["cpu_usage"]
            if not isinstance(cpu_usage, (int, float)) or cpu_usage < 0 or cpu_usage > 100:
                raise ValueError("CPU usage must be a number between 0 and 100")
        return v
```

### Model Inheritance

You can create custom models by inheriting from the base models:

```python
from laneswap.models.heartbeat import ServiceHeartbeat
from typing import Dict, Any, Optional
from datetime import datetime

class ExtendedServiceHeartbeat(ServiceHeartbeat):
    region: str
    instance_id: str
    uptime: int
    custom_metrics: Optional[Dict[str, Any]] = None
```

### Model Conversion

You can convert between different model types:

```python
from laneswap.models.heartbeat import ServiceRegistration, ServiceStatus
from datetime import datetime
import uuid

# Create a service registration
registration = ServiceRegistration(
    name="my-service",
    metadata={"version": "1.0.0", "environment": "production"}
)

# Convert to a service status
service_id = str(uuid.uuid4())
status = ServiceStatus(
    service_id=service_id,
    name=registration.name,
    status="unknown",
    created_at=datetime.utcnow(),
    metadata=registration.metadata
)
```

## Best Practices

1. **Type Hints**: Use type hints for all fields
2. **Validation**: Add validation for all fields
3. **Default Values**: Provide sensible default values for optional fields
4. **Documentation**: Document model fields with docstrings
5. **Immutability**: Use immutable models when possible
6. **Serialization**: Use model serialization methods for JSON conversion
7. **Deserialization**: Use model deserialization methods for JSON parsing
8. **Validation Errors**: Handle validation errors gracefully
9. **Model Updates**: Use model copy and update methods for updates
10. **Model Composition**: Use model composition for complex data structures 