"""
Synchronous client for the LaneSwap API.

This module provides a synchronous client for interacting with the LaneSwap API
from other services. It's a wrapper around the asynchronous client for use in
environments where async/await cannot be used.
"""

import asyncio
import logging
import threading
import time
from typing import Dict, Any, Optional, List, Union

from .async_client import LaneswapAsyncClient
from ..models.heartbeat import HeartbeatStatus

logger = logging.getLogger("laneswap.client")


class LaneswapSyncClient:
    """
    Synchronous client for the LaneSwap API.
    
    This client provides methods for registering services and sending
    heartbeats to a LaneSwap API server in a synchronous manner.
    It's a wrapper around the asynchronous client for use in environments
    where async/await cannot be used.
    """
    
    def __init__(
        self,
        api_url: str,
        service_name: Optional[str] = None,
        service_id: Optional[str] = None,
        auto_heartbeat: bool = False,
        heartbeat_interval: int = 30,
        headers: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the LaneSwap synchronous client.
        
        Args:
            api_url: Base URL for the LaneSwap API (e.g., http://localhost:8000)
            service_name: Human-readable name for the service
            service_id: Optional service ID (will be auto-generated if not provided)
            auto_heartbeat: Whether to automatically send heartbeats
            heartbeat_interval: Interval between heartbeats in seconds
            headers: Optional headers to include in all requests
        """
        self.api_url = api_url
        self.service_name = service_name
        self.service_id = service_id
        self.auto_heartbeat = auto_heartbeat
        self.heartbeat_interval = heartbeat_interval
        self.headers = headers or {}
        
        # Create the async client
        self._async_client = LaneswapAsyncClient(
            api_url=api_url,
            service_name=service_name,
            service_id=service_id,
            auto_heartbeat=False,  # We'll handle this ourselves
            heartbeat_interval=heartbeat_interval,
            headers=headers
        )
        
        # Internal state
        self._loop = None
        self._thread = None
        self._heartbeat_thread = None
        self._running = False
        self._connected = False
        self._closed = False
        self.metadata = {}
        
        # Validate parameters
        if not self.service_id and not self.service_name:
            raise ValueError("Either service_id or service_name must be provided")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        self.close()
    
    def _run_async(self, coro):
        """
        Run an async coroutine in a synchronous context.
        
        Args:
            coro: Coroutine to run
            
        Returns:
            The result of the coroutine
        """
        if self._loop is None:
            try:
                # Try to get the current event loop
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                # If there's no event loop, create a new one
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        
        # If the loop is not running, run the coroutine directly
        if not self._loop.is_running():
            return self._loop.run_until_complete(coro)
        
        # If the loop is running, we need to use a future
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()
    
    def connect(self) -> str:
        """
        Connect to the LaneSwap API and register the service if needed.
        
        Returns:
            str: Service ID
        """
        if self._connected and self.service_id:
            return self.service_id
        
        # Connect the async client
        self.service_id = self._run_async(self._async_client.connect())
        self._connected = True
        
        # Start heartbeat thread if auto_heartbeat is enabled
        if self.auto_heartbeat and not self._heartbeat_thread:
            self._heartbeat_thread = threading.Thread(
                target=self._heartbeat_loop,
                daemon=True
            )
            self._heartbeat_thread.start()
        
        return self.service_id
    
    def close(self):
        """
        Close the client session and clean up resources.
        """
        if self._closed:
            return
        
        # Stop heartbeat thread if running
        self._running = False
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=1.0)
        
        # Close the async client
        self._run_async(self._async_client.close())
        self._connected = False
        self._closed = True
        logger.debug("Sync client disconnected")
    
    def register_service(
        self,
        service_name: str,
        service_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Register a service with the LaneSwap API.
        
        Args:
            service_name: Human-readable name for the service
            service_id: Optional service ID (will be auto-generated if not provided)
            metadata: Additional information about the service
            
        Returns:
            str: The registered service ID
        """
        return self._run_async(
            self._async_client.register_service(
                service_name=service_name,
                service_id=service_id,
                metadata=metadata
            )
        )
    
    def send_heartbeat(
        self,
        status: Union[str, HeartbeatStatus] = HeartbeatStatus.HEALTHY,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a heartbeat to the LaneSwap API.
        
        Args:
            status: Service status (healthy, warning, error, etc.)
            message: Optional status message
            metadata: Additional information to include with the heartbeat
            
        Returns:
            Dict[str, Any]: Response from the API
        """
        return self._run_async(
            self._async_client.send_heartbeat(
                status=status,
                message=message,
                metadata=metadata
            )
        )
    
    def get_service(self) -> Dict[str, Any]:
        """
        Get the current status of the service.
        
        Returns:
            Dict[str, Any]: Service status information
        """
        return self._run_async(self._async_client.get_service())
    
    def get_all_services(self) -> Dict[str, Any]:
        """
        Get status information for all registered services.
        
        Returns:
            Dict[str, Any]: Dictionary with services data and summary statistics
        """
        return self._run_async(self._async_client.get_all_services())
    
    def set_metadata(self, metadata: Dict[str, Any]):
        """
        Set metadata for the service.
        
        Args:
            metadata: Metadata to set
        """
        self.metadata.update(metadata)
        self._async_client.set_metadata(metadata)
    
    def _heartbeat_loop(self):
        """Background thread to send periodic heartbeats."""
        self._running = True
        while self._running:
            try:
                self.send_heartbeat(
                    status=HeartbeatStatus.HEALTHY,
                    metadata=self.metadata
                )
            except Exception as e:
                logger.error(f"Failed to send heartbeat: {str(e)}")
            
            # Sleep for the heartbeat interval
            time.sleep(self.heartbeat_interval)
    
    def get_monitor_url(self, start_if_needed=False) -> str:
        """
        Get a URL to the web monitor for this service.
        
        Args:
            start_if_needed: Whether to start the monitor if it's not running
            
        Returns:
            URL to the web monitor
        """
        return self._run_async(
            self._async_client.get_monitor_url(start_if_needed=start_if_needed)
        )
    
    # Progress tracking methods
    def start_progress(
        self,
        task_name: str,
        total_steps: int,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start a progress tracking task.
        
        Args:
            task_name: Name of the task
            total_steps: Total number of steps in the task
            description: Optional description of the task
            metadata: Additional information about the task
            
        Returns:
            str: Task ID
        """
        return self._run_async(
            self._async_client.start_progress(
                task_name=task_name,
                total_steps=total_steps,
                description=description,
                metadata=metadata
            )
        )
    
    def update_progress(
        self,
        task_id: str,
        current_step: int,
        status: str = "running",
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update the progress of a task.
        
        Args:
            task_id: Task ID
            current_step: Current step number
            status: Task status
            message: Optional status message
            metadata: Additional information to include with the update
            
        Returns:
            Dict[str, Any]: Response from the API
        """
        return self._run_async(
            self._async_client.update_progress(
                task_id=task_id,
                current_step=current_step,
                status=status,
                message=message,
                metadata=metadata
            )
        )
    
    def complete_progress(
        self,
        task_id: str,
        status: str = "completed",
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Mark a progress task as completed.
        
        Args:
            task_id: Task ID
            status: Final task status
            message: Optional status message
            metadata: Additional information to include with the update
            
        Returns:
            Dict[str, Any]: Response from the API
        """
        return self._run_async(
            self._async_client.complete_progress(
                task_id=task_id,
                status=status,
                message=message,
                metadata=metadata
            )
        ) 