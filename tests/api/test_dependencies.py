"""
Tests for the API dependencies module.
"""

import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock, patch

from laneswap.api.dependencies import get_heartbeat_manager, validate_service_exists
from laneswap.core.heartbeat import HeartbeatManager


@pytest.mark.asyncio
async def test_get_heartbeat_manager():
    """Test the get_heartbeat_manager dependency."""
    # Mock the get_manager function to return a valid manager
    with patch('laneswap.api.dependencies.get_manager') as mock_get_manager:
        # Setup the mock to return a valid manager
        mock_manager = HeartbeatManager()
        mock_get_manager.return_value = mock_manager
        
        # Call the dependency
        result = await get_heartbeat_manager()
        
        # Verify the result
        assert result is mock_manager
        mock_get_manager.assert_called_once()


@pytest.mark.asyncio
async def test_get_heartbeat_manager_not_initialized():
    """Test the get_heartbeat_manager dependency when manager is not initialized."""
    # Mock the get_manager function to return None
    with patch('laneswap.api.dependencies.get_manager') as mock_get_manager:
        mock_get_manager.return_value = None
        
        # Call the dependency and expect an exception
        with pytest.raises(HTTPException) as excinfo:
            await get_heartbeat_manager()
        
        # Verify the exception
        assert excinfo.value.status_code == 503
        assert "Heartbeat manager not initialized" in excinfo.value.detail
        mock_get_manager.assert_called_once()


@pytest.mark.asyncio
async def test_validate_service_exists():
    """Test the validate_service_exists dependency."""
    # Create a mock manager
    mock_manager = AsyncMock()
    mock_manager.get_service.return_value = {"id": "test-service", "name": "Test Service"}
    
    # Call the dependency
    service_id = await validate_service_exists("test-service", mock_manager)
    
    # Verify the result
    assert service_id == "test-service"
    mock_manager.get_service.assert_called_once_with("test-service")


@pytest.mark.asyncio
async def test_validate_service_not_found():
    """Test the validate_service_exists dependency when service is not found."""
    # Create a mock manager
    mock_manager = AsyncMock()
    mock_manager.get_service.return_value = None
    
    # Call the dependency and expect an exception
    with pytest.raises(HTTPException) as excinfo:
        await validate_service_exists("non-existent", mock_manager)
    
    # Verify the exception
    assert excinfo.value.status_code == 404
    assert "Service with ID non-existent not found" in excinfo.value.detail
    mock_manager.get_service.assert_called_once_with("non-existent") 