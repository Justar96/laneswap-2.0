"""
Tests for the API error handler middleware.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from laneswap.api.middleware.error_handler import log_error, add_error_handlers
from laneswap.models.error import ErrorResponse


@pytest.mark.asyncio
async def test_log_error_with_storage():
    """Test logging an error with storage available."""
    # Mock the request
    mock_request = MagicMock()
    mock_request.path_params = {"service_id": "test-service"}
    mock_request.method = "GET"
    mock_request.url = "http://localhost:8000/api/services/test-service"
    mock_request.client.host = "127.0.0.1"
    
    # Mock the heartbeat manager
    mock_manager = MagicMock()
    mock_manager.storage = AsyncMock()
    
    # Mock the get_manager function
    with patch('laneswap.api.middleware.error_handler.get_manager', return_value=mock_manager):
        # Call the function
        await log_error(
            request=mock_request,
            error_type="test_error",
            message="Test error message",
            status_code=500,
            details={"test": True}
        )
        
        # Verify the storage.store_error was called
        mock_manager.storage.store_error.assert_called_once()
        
        # Check the error data
        error_data = mock_manager.storage.store_error.call_args[0][0]
        assert error_data["service_id"] == "test-service"
        assert error_data["error_type"] == "test_error"
        assert error_data["message"] == "Test error message"
        assert error_data["status_code"] == 500
        assert error_data["request_method"] == "GET"
        assert error_data["metadata"] == {"test": True}


@pytest.mark.asyncio
async def test_log_error_without_storage():
    """Test logging an error without storage available."""
    # Mock the request
    mock_request = MagicMock()
    
    # Mock the heartbeat manager without storage
    mock_manager = MagicMock()
    mock_manager.storage = None
    
    # Mock the get_manager function
    with patch('laneswap.api.middleware.error_handler.get_manager', return_value=mock_manager):
        # Call the function
        await log_error(
            request=mock_request,
            error_type="test_error",
            message="Test error message",
            status_code=500
        )
        
        # No assertions needed, just make sure it doesn't raise an exception


@pytest.mark.asyncio
async def test_log_error_without_manager():
    """Test logging an error without a manager available."""
    # Mock the request
    mock_request = MagicMock()
    
    # Mock the get_manager function to return None
    with patch('laneswap.api.middleware.error_handler.get_manager', return_value=None):
        # Call the function
        await log_error(
            request=mock_request,
            error_type="test_error",
            message="Test error message",
            status_code=500
        )
        
        # No assertions needed, just make sure it doesn't raise an exception


@pytest.mark.asyncio
async def test_log_error_with_exception():
    """Test logging an error when an exception occurs."""
    # Mock the request
    mock_request = MagicMock()
    mock_request.path_params = {}
    
    # Mock the heartbeat manager
    mock_manager = MagicMock()
    mock_manager.storage = AsyncMock()
    mock_manager.storage.store_error.side_effect = Exception("Storage error")
    
    # Mock the get_manager function
    with patch('laneswap.api.middleware.error_handler.get_manager', return_value=mock_manager):
        # Mock the logger
        with patch('laneswap.api.middleware.error_handler.logger') as mock_logger:
            # Call the function
            await log_error(
                request=mock_request,
                error_type="test_error",
                message="Test error message",
                status_code=500
            )
            
            # Verify the logger.error was called
            mock_logger.error.assert_called_once()
            assert "Failed to log error to storage" in mock_logger.error.call_args[0][0]


def test_add_error_handlers():
    """Test adding error handlers to a FastAPI app."""
    # Create a mock FastAPI app
    app = MagicMock()
    
    # Call the function
    add_error_handlers(app)
    
    # Verify that exception handlers were added
    assert app.exception_handler.call_count == 2
    
    # Check that the correct exception types were registered
    exception_types = [call_args[0][0] for call_args in app.exception_handler.call_args_list]
    assert RequestValidationError in exception_types
    assert Exception in exception_types


@pytest.mark.asyncio
async def test_validation_exception_handler():
    """Test the validation exception handler."""
    # Create a FastAPI app
    app = FastAPI()
    
    # Add error handlers
    add_error_handlers(app)
    
    # Get the validation exception handler
    validation_handler = None
    for handler in app.exception_handlers.values():
        if handler.__name__ == 'validation_exception_handler':
            validation_handler = handler
            break
    
    assert validation_handler is not None
    
    # Create a mock request
    mock_request = MagicMock()
    
    # Create a validation error
    validation_error = RequestValidationError(
        errors=[
            {
                "loc": ("body", "name"),
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    )
    
    # Mock the log_error function and model_dump to avoid datetime serialization issues
    with patch('laneswap.api.middleware.error_handler.log_error') as mock_log_error, \
         patch('laneswap.models.error.ErrorResponse.model_dump', return_value={
             "error_type": "validation_error",
             "message": "Validation error",
             "status_code": 422,
             "timestamp": "2023-01-01T12:00:00Z",
             "details": [{"loc": ["body", "name"], "msg": "field required", "type": "value_error.missing"}]
         }):
        # Call the handler
        response = await validation_handler(mock_request, validation_error)
        
        # Verify the response
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Verify log_error was called
        mock_log_error.assert_called_once()


@pytest.mark.asyncio
async def test_general_exception_handler():
    """Test the general exception handler."""
    # Create a FastAPI app
    app = FastAPI()
    
    # Add error handlers
    add_error_handlers(app)
    
    # Get the general exception handler
    general_handler = None
    for handler in app.exception_handlers.values():
        if handler.__name__ == 'general_exception_handler':
            general_handler = handler
            break
    
    assert general_handler is not None
    
    # Create a mock request
    mock_request = MagicMock()
    
    # Create an exception
    exception = ValueError("Test error")
    
    # Mock the log_error function, logger, and model_dump to avoid datetime serialization issues
    with patch('laneswap.api.middleware.error_handler.log_error') as mock_log_error, \
         patch('laneswap.api.middleware.error_handler.logger') as mock_logger, \
         patch('laneswap.models.error.ErrorResponse.model_dump', return_value={
             "error_type": "server_error",
             "message": "Internal server error",
             "status_code": 500,
             "timestamp": "2023-01-01T12:00:00Z",
             "details": {"error": "Test error"}
         }):
        # Call the handler
        response = await general_handler(mock_request, exception)
        
        # Verify the response
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
        # Verify log_error was called
        mock_log_error.assert_called_once()
        
        # Verify logger.exception was called
        mock_logger.exception.assert_called_once() 