from typing import Dict, Any, Optional
import logging
from datetime import datetime
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from ...models.error import ErrorResponse
from ...core.heartbeat import get_manager

logger = logging.getLogger("laneswap")


async def log_error(
    request: Request,
    error_type: str,
    message: str,
    status_code: int,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an error to the MongoDB error collection if available.
    
    Args:
        request: FastAPI request object
        error_type: Type of error
        message: Error message
        status_code: HTTP status code
        details: Additional error details
    """
    manager = get_manager()
    if not manager or not manager.storage:
        return
        
    # Get service_id from request path if available
    service_id = None
    path_params = request.path_params
    if "service_id" in path_params:
        service_id = path_params["service_id"]
        
    # Create error log entry
    error_data = {
        "timestamp": datetime.utcnow(),
        "service_id": service_id,
        "error_type": error_type,
        "message": message,
        "status_code": status_code,
        "request_method": request.method,
        "request_url": str(request.url),
        "client_host": request.client.host if request.client else None,
        "metadata": details or {}
    }
    
    try:
        await manager.storage.store_error(error_data)
    except Exception as e:
        logger.error(f"Failed to log error to storage: {str(e)}")


def add_error_handlers(app: FastAPI) -> None:
    """
    Add custom exception handlers to the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors from request data."""
        error_details = []
        for error in exc.errors():
            error_details.append({
                "loc": error.get("loc", []),
                "msg": error.get("msg", ""),
                "type": error.get("type", "")
            })
            
        error_response = ErrorResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error="Validation Error",
            message="Request validation failed",
            details={"errors": error_details}
        )
        
        await log_error(
            request=request,
            error_type="validation_error",
            message="Request validation failed",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"errors": error_details}
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.dict()
        )
        
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle uncaught exceptions."""
        # Log the exception
        logger.exception(f"Unhandled exception: {str(exc)}")
        
        error_type = exc.__class__.__name__
        error_response = ErrorResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=str(exc),
            details={"type": error_type}
        )
        
        await log_error(
            request=request,
            error_type=error_type,
            message=str(exc),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.dict()
        )