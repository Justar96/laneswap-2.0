"""
Asynchronous client for the LaneSwap API.

This module provides an async client for interacting with the LaneSwap API
from other services.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

import aiohttp
from pydantic import BaseModel

from ..models.heartbeat import HeartbeatStatus, ServiceHeartbeat, ServiceRegistration
from ..core.exceptions import LaneswapError, ServiceNotFoundError
from ..core.heartbeat import generate_monitor_url

logger = logging.getLogger("laneswap.client")


class LaneswapAsyncClient:
    """
    Asynchronous client for the LaneSwap API.
    
    This client provides methods for registering services and sending
    heartbeats to a LaneSwap API server.
    """
    
    def __init__(
        self,
        api_url: str,
        service_id: Optional[str] = None,
        service_name: Optional[str] = None,
        heartbeat_interval: int = 30,
        auto_heartbeat: bool = False
    ):
        """
        Initialize the LaneSwap client.
        
        Args:
            api_url: URL of the LaneSwap API server
            service_id: Optional service ID (will be auto-generated if not provided)
            service_name: Service name (required if service_id is not provided)
            heartbeat_interval: Interval in seconds between automatic heartbeats
            auto_heartbeat: Whether to automatically send heartbeats
        """
        self.api_url = api_url.rstrip('/')
        self.service_id = service_id
        self.service_name = service_name
        self.heartbeat_interval = heartbeat_interval
        self.auto_heartbeat = auto_heartbeat
        self._heartbeat_task = None
        self._session = None
        self._metadata = {}
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
        
    async def connect(self) -> str:
        """
        Connect to the LaneSwap API and register the service.
        
        Returns:
            str: The service ID
        """
        if self._session is None:
            self._session = aiohttp.ClientSession()
            
        if self.service_id is None:
            if not self.service_name:
                raise ValueError("service_name is required when service_id is not provided")
                
            # Register the service
            self.service_id = await self.register_service(
                service_name=self.service_name,
                metadata=self._metadata
            )
            
        if self.auto_heartbeat and self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        # Log the monitor URL
        monitor_url = await self.get_monitor_url()
        logger.info(f"Service registered with ID: {self.service_id}")
        logger.info(f"Monitor URL: {monitor_url}")
        
        return self.service_id
        
    async def disconnect(self):
        """Disconnect from the LaneSwap API."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None
            
        if self._session:
            await self._session.close()
            self._session = None
            
    async def register_service(
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
        if self._session is None:
            self._session = aiohttp.ClientSession()
            
        registration = ServiceRegistration(
            service_id=service_id or self.service_id,
            service_name=service_name,
            metadata=metadata or {}
        )
        
        async with self._session.post(
            f"{self.api_url}/api/services",
            json=registration.dict(exclude_none=True)
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(f"Failed to register service: {error_text}")
                
            response_data = await response.json()
            return response_data.get("service_id")
            
    async def send_heartbeat(
        self,
        status: HeartbeatStatus = HeartbeatStatus.HEALTHY,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send a heartbeat to the LaneSwap API."""
        if not self.service_id:
            raise ValueError("Service not registered. Call connect() first.")
            
        if self._session is None:
            self._session = aiohttp.ClientSession()
            
        heartbeat = ServiceHeartbeat(
            status=status,
            message=message,
            metadata=metadata
        )
        
        try:
            async with self._session.post(
                f"{self.api_url}/api/services/{self.service_id}/heartbeat",
                json=heartbeat.dict(exclude_none=True),
                timeout=10  # Add timeout
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Failed to send heartbeat: {response.status} - {error_text}")
                    
                return await response.json()
        except aiohttp.ClientError as e:
            # More specific error handling
            raise RuntimeError(f"Network error when sending heartbeat: {str(e)}") from e
            
    async def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of this service.
        
        Returns:
            Dict[str, Any]: The service status
        """
        if not self.service_id:
            raise ValueError("Service not registered. Call connect() first.")
            
        if self._session is None:
            self._session = aiohttp.ClientSession()
            
        async with self._session.get(
            f"{self.api_url}/api/services/{self.service_id}"
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(f"Failed to get service status: {error_text}")
                
            return await response.json()
            
    async def get_all_services(self) -> Dict[str, Any]:
        """
        Get status information for all registered services.
        
        Returns:
            Dict[str, Any]: Dictionary with services data and summary statistics
        """
        if self._session is None:
            self._session = aiohttp.ClientSession()
            
        async with self._session.get(
            f"{self.api_url}/api/services"
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(f"Failed to get services: {error_text}")
                
            return await response.json()
            
    def set_metadata(self, metadata: Dict[str, Any]):
        """
        Set metadata for the service.
        
        Args:
            metadata: Metadata to set
        """
        self._metadata.update(metadata)
        
    async def _heartbeat_loop(self):
        """Background task to send periodic heartbeats."""
        while True:
            try:
                await self.send_heartbeat(
                    status=HeartbeatStatus.HEALTHY,
                    metadata=self._metadata
                )
            except Exception as e:
                logger.error(f"Failed to send heartbeat: {str(e)}")
                
            await asyncio.sleep(self.heartbeat_interval)

    @property
    def heartbeat_manager(self):
        """
        Get a dummy heartbeat manager that forwards requests to the API.
        
        This allows code that expects a heartbeat manager to work with the client.
        """
        # We'll create a simple proxy object that forwards to our send_heartbeat method
        class ClientHeartbeatProxy:
            def __init__(self, client):
                self.client = client
                
            async def send_heartbeat(self, service_id=None, status=None, message=None, metadata=None):
                # Use the client's service_id if none provided
                service_id = service_id or self.client.service_id
                return await self.client.send_heartbeat(status=status, message=message, metadata=metadata)
        
        return ClientHeartbeatProxy(self)

    async def get_monitor_url(self, start_if_needed=False) -> str:
        """
        Get a URL to the web monitor for this service.
        
        Args:
            start_if_needed: Whether to start the monitor if it's not running
            
        Returns:
            URL to the web monitor
        """
        url = await generate_monitor_url(
            service_id=self.service_id,
            api_url=self.api_url
        )
        
        if start_if_needed:
            try:
                import socket
                import subprocess
                import sys
                import os
                from pathlib import Path
                
                # Function to check if port is in use
                def is_port_in_use(port):
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        return s.connect_ex(('localhost', port)) == 0
                
                # Extract port from URL
                import re
                port_match = re.search(r':(\d+)', url)
                port = 8080  # Default port
                if port_match:
                    port = int(port_match.group(1))
                
                # Check if the monitor is already running
                if not is_port_in_use(port):
                    logger.info(f"Web monitor not running on port {port}. Starting it...")
                    
                    # Start the monitor in a separate process
                    monitor_script = Path(__file__).parent.parent / "examples" / "start_monitor.py"
                    
                    if not monitor_script.exists():
                        logger.warning(f"Monitor script not found at {monitor_script}. Using module approach.")
                        # Use the module approach as fallback
                        cmd = [
                            sys.executable, "-m", 
                            "laneswap.examples.start_monitor",
                            "--port", str(port),
                            "--api-url", self.api_url,
                            "--no-browser"
                        ]
                    else:
                        cmd = [
                            sys.executable, str(monitor_script),
                            "--port", str(port),
                            "--api-url", self.api_url,
                            "--no-browser"
                        ]
                    
                    # Start the process detached from this one
                    try:
                        if os.name == 'nt':  # Windows
                            subprocess.Popen(
                                cmd, 
                                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                            )
                        else:  # Unix/Linux/Mac
                            subprocess.Popen(
                                cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                start_new_session=True
                            )
                        
                        # Wait a moment for the server to start
                        import time
                        time.sleep(3)
                        logger.info("Web monitor started in background process.")
                    except Exception as e:
                        logger.error(f"Failed to start web monitor: {str(e)}")
            except ImportError as e:
                logger.warning(f"Could not check/start web monitor: {str(e)}")
        
        return url 