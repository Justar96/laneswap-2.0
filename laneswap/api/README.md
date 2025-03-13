# LaneSwap API Module

The API module provides a FastAPI-based server for the LaneSwap system, allowing services to register, send heartbeats, and track progress through HTTP endpoints.

## Components

### Main Application (`main.py`)

The main FastAPI application with lifespan management, middleware configuration, and router inclusion.

#### Key Features

- **Lifespan Management**: Handles startup and shutdown events
- **CORS Middleware**: Configurable CORS support
- **Error Handling**: Global exception handlers
- **Router Integration**: Includes all API routers
- **OpenAPI Documentation**: Automatic API documentation

#### Usage Example

```python
from laneswap.api.main import app
import uvicorn

# Run the server
uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Server Launcher (`server.py`)

A convenience module for starting the API server with command-line arguments.

#### Key Features

- **Command-line Arguments**: Support for host, port, and debug mode
- **Environment Variable Support**: Configuration via environment variables
- **URL Display**: Shows access URLs on startup

#### Usage Example

```bash
# Run with default settings
python -m laneswap.api.server

# Run with custom host and port
python -m laneswap.api.server --host 127.0.0.1 --port 9000

# Run in debug mode
python -m laneswap.api.server --debug
```

### Dependencies (`dependencies.py`)

FastAPI dependency injection functions for common operations.

#### Key Features

- **Heartbeat Manager**: Provides access to the heartbeat manager
- **Progress Manager**: Provides access to the progress manager
- **Request Validation**: Validates request parameters

#### Usage Example

```python
from fastapi import APIRouter, Depends
from laneswap.api.dependencies import get_heartbeat_manager

router = APIRouter()

@router.get("/services")
async def get_services(manager = Depends(get_heartbeat_manager)):
    services = await manager.get_all_services()
    return {"services": services}
```

## Routers

### Health Check Router (`routers/health_check.py`)

Provides endpoints for checking the health of the API server.

#### Endpoints

- `GET /api/health`: Returns the health status of the API server

#### Usage Example

```bash
curl http://localhost:8000/api/health
```

Response:
```json
{
  "status": "ok",
  "timestamp": "2023-09-01T12:00:00Z"
}
```

### Heartbeat Router (`routers/heartbeat.py`)

Provides endpoints for service registration and heartbeat management.

#### Endpoints

- `POST /api/services`: Register a new service
- `GET /api/services`: Get all registered services
- `GET /api/services/{service_id}`: Get a specific service
- `POST /api/services/{service_id}/heartbeat`: Send a heartbeat for a service
- `DELETE /api/services/{service_id}`: Delete a service

#### Usage Example

```bash
# Register a service
curl -X POST http://localhost:8000/api/services \
  -H "Content-Type: application/json" \
  -d '{"name": "my-service", "metadata": {"version": "1.0.0"}}'

# Send a heartbeat
curl -X POST http://localhost:8000/api/services/550e8400-e29b-41d4-a716-446655440000/heartbeat \
  -H "Content-Type: application/json" \
  -d '{"status": "healthy", "message": "Service is running normally"}'
```

### Progress Router (`routers/progress.py`)

Provides endpoints for tracking progress of long-running tasks.

#### Endpoints

- `POST /api/progress`: Start a new progress task
- `GET /api/progress`: Get all progress tasks
- `GET /api/progress/{task_id}`: Get a specific progress task
- `PUT /api/progress/{task_id}`: Update a progress task
- `DELETE /api/progress/{task_id}`: Delete a progress task

#### Usage Example

```bash
# Start a progress task
curl -X POST http://localhost:8000/api/progress \
  -H "Content-Type: application/json" \
  -d '{"service_id": "550e8400-e29b-41d4-a716-446655440000", "task_name": "Data Processing", "total_steps": 100}'

# Update progress
curl -X PUT http://localhost:8000/api/progress/550e8400-e29b-41d4-a716-446655440001 \
  -H "Content-Type: application/json" \
  -d '{"current_step": 50, "status": "running", "message": "Processing item 50/100"}'
```

## Middleware

### Logging Middleware (`middleware/logging.py`)

Middleware for logging API requests and responses.

#### Key Features

- **Request Logging**: Logs incoming requests with method, path, and client IP
- **Response Logging**: Logs responses with status code and processing time
- **Error Logging**: Detailed logging for request errors

### Error Handling Middleware (`middleware/error_handling.py`)

Middleware for handling and formatting API errors.

#### Key Features

- **Exception Catching**: Catches and formats exceptions
- **Error Responses**: Consistent error response format
- **Status Code Mapping**: Maps exception types to HTTP status codes

## Integration with Other Modules

The API module integrates with other LaneSwap modules:

- **Core Module**: Uses the heartbeat manager and progress manager
- **Models Module**: Uses data models for request/response validation
- **Adapters Module**: Indirectly uses storage and notification adapters through the core module

## Advanced Usage

### Custom Routers

You can create custom routers to extend the API functionality:

```python
from fastapi import APIRouter, Depends
from laneswap.api.dependencies import get_heartbeat_manager

# Create a custom router
custom_router = APIRouter()

@custom_router.get("/custom-endpoint")
async def custom_endpoint(manager = Depends(get_heartbeat_manager)):
    # Custom logic
    return {"message": "Custom endpoint"}

# Add the router to the main app
from laneswap.api.main import app
app.include_router(custom_router, prefix="/api", tags=["custom"])
```

### Custom Middleware

You can add custom middleware to the API server:

```python
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class CustomMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Pre-processing
        print(f"Request to {request.url.path}")
        
        # Call the next middleware or endpoint
        response = await call_next(request)
        
        # Post-processing
        print(f"Response from {request.url.path}: {response.status_code}")
        
        return response

# Add the middleware to the main app
from laneswap.api.main import app
app.add_middleware(CustomMiddleware)
```

## Best Practices

1. **Use Dependency Injection**: Use FastAPI's dependency injection for accessing managers and services
2. **Validate Request Data**: Use Pydantic models for request validation
3. **Consistent Response Format**: Use consistent response formats across endpoints
4. **Error Handling**: Use proper error handling and status codes
5. **Documentation**: Document API endpoints with docstrings and examples
6. **Rate Limiting**: Consider adding rate limiting for production deployments
7. **Authentication**: Add authentication for sensitive endpoints in production
8. **Versioning**: Consider API versioning for future compatibility
9. **Testing**: Write tests for all API endpoints
10. **Monitoring**: Monitor API performance and errors 