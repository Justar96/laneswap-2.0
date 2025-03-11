"""
Heartbeat monitoring system for tracking service health.
"""

from typing import Dict, Any, Optional, List, Union, Callable
from datetime import datetime, timedelta
import asyncio
import uuid
import logging
import time
import json
from functools import wraps
from contextlib import asynccontextmanager

from .exceptions import ServiceNotFoundError
from .types import HeartbeatStatus
from .config import get_settings

# Import models
from ..models.heartbeat import HeartbeatEvent
from ..models.error import ErrorLog
from ..adapters.base import NotifierAdapter, StorageAdapter

logger = logging.getLogger("laneswap")

# Global state
_services: Dict[str, Dict[str, Any]] = {}
_notifiers: List[NotifierAdapter] = []
_storage: Optional[StorageAdapter] = None
_check_interval: int = 30
_stale_threshold: int = 60
_monitor_task = None
_manager_instance = None

async def initialize(
    notifiers: Optional[List[NotifierAdapter]] = None,
    storage: Optional[StorageAdapter] = None,
    check_interval: Optional[int] = None,
    stale_threshold: Optional[int] = None
) -> None:
    """
    Initialize the heartbeat system.
    
    Args:
        notifiers: List of notification adapters (Discord, etc.)
        storage: Storage adapter for persistence (MongoDB, etc.)
        check_interval: Interval in seconds to check for stale heartbeats
        stale_threshold: Time in seconds after which a heartbeat is considered stale
    """
    # Get the manager
    manager = get_manager()
    
    # Add notifiers
    if notifiers:
        for notifier in notifiers:
            manager.add_notifier_adapter(notifier)
    
    # Set storage
    if storage:
        manager.add_storage_adapter(storage)
    
    # Start the monitor if it's not already running
    if not manager.monitor_task or manager.monitor_task.done():
        await manager.start_monitor(check_interval, stale_threshold)
    else:
        logger.info("Heartbeat monitor is already running")
    
    logger.debug("Heartbeat system initialized")

async def register_service(
    service_name: str, 
    service_id: Optional[str] = None, 
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Register a new service to be monitored.
    
    Args:
        service_name: Name of the service
        service_id: Optional service ID (will be generated if not provided)
        metadata: Optional metadata for the service
        
    Returns:
        str: Service ID
    """
    # Get the manager
    manager = get_manager()
    
    # Register the service
    return await manager.register_service(service_name, service_id, metadata)

async def send_heartbeat(
    service_id: str, 
    status: HeartbeatStatus = HeartbeatStatus.HEALTHY,
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Update the heartbeat status for a service.
    
    Args:
        service_id: Service ID
        status: Service status
        message: Optional status message
        metadata: Optional metadata to update
        
    Returns:
        Dict[str, Any]: Updated service information
        
    Raises:
        ServiceNotFoundError: If the service is not found
    """
    # Get the manager
    manager = get_manager()
    
    # Send the heartbeat
    return await manager.send_heartbeat(service_id, status, message, metadata)

async def get_service(service_id: str) -> Dict[str, Any]:
    """
    Get the current status of a service.
    
    Args:
        service_id: Service ID
        
    Returns:
        Dict[str, Any]: Service information
        
    Raises:
        ServiceNotFoundError: If the service is not found
    """
    # Get the manager
    manager = get_manager()
    
    # Get the service
    return await manager.get_service(service_id)

async def get_all_services() -> Dict[str, Dict[str, Any]]:
    """
    Get all registered services.
    
    Returns:
        Dict[str, Dict[str, Any]]: Dictionary mapping service IDs to service information
    """
    # Get the manager
    manager = get_manager()
    
    # Get all services
    return await manager.get_all_services()

async def start_monitor() -> None:
    """Start the heartbeat monitor task."""
    # Get the manager
    manager = get_manager()
    
    # Start the monitor
    await manager.start_monitor()

async def stop_monitor() -> None:
    """Stop the heartbeat monitor task."""
    # Get the manager
    manager = get_manager()
    
    # Stop the monitor
    await manager.stop_monitor()

@asynccontextmanager
async def heartbeat_system(
    notifiers: Optional[List[NotifierAdapter]] = None,
    storage: Optional[StorageAdapter] = None,
    check_interval: int = 30,
    stale_threshold: int = 60
):
    """
    Context manager for the heartbeat system.
    
    Args:
        notifiers: List of notification adapters
        storage: Storage adapter for persistence
        check_interval: Interval to check for stale heartbeats
        stale_threshold: Time after which a heartbeat is considered stale
    """
    await initialize(notifiers, storage, check_interval, stale_threshold)
    try:
        yield
    finally:
        try:
            await stop_monitor()
        except Exception as e:
            logger.warning(f"Error stopping heartbeat monitor during cleanup: {str(e)}")

def with_heartbeat(
    service_id: str,
    success_status: HeartbeatStatus = HeartbeatStatus.HEALTHY,
    error_status: HeartbeatStatus = HeartbeatStatus.ERROR
):
    """
    Decorator to automatically send heartbeats before and after a function execution.
    
    Args:
        service_id: Service identifier
        success_status: Status to report on successful execution
        error_status: Status to report on error
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                await send_heartbeat(
                    service_id=service_id,
                    status=HeartbeatStatus.BUSY,
                    message=f"Starting operation: {func.__name__}",
                    metadata={"operation": func.__name__}
                )
                
                result = await func(*args, **kwargs)
                
                execution_time = time.time() - start_time
                await send_heartbeat(
                    service_id=service_id,
                    status=success_status,
                    message=f"Operation completed: {func.__name__}",
                    metadata={
                        "operation": func.__name__,
                        "execution_time": execution_time
                    }
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                await send_heartbeat(
                    service_id=service_id,
                    status=error_status,
                    message=f"Operation failed: {func.__name__} - {str(e)}",
                    metadata={
                        "operation": func.__name__,
                        "execution_time": execution_time,
                        "error": str(e)
                    }
                )
                raise
                
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            
            loop = asyncio.get_event_loop()
            
            try:
                # Send starting heartbeat
                loop.run_until_complete(
                    send_heartbeat(
                        service_id=service_id,
                        status=HeartbeatStatus.BUSY,
                        message=f"Starting operation: {func.__name__}",
                        metadata={"operation": func.__name__}
                    )
                )
                
                # Execute the function
                result = func(*args, **kwargs)
                
                # Send success heartbeat
                execution_time = time.time() - start_time
                loop.run_until_complete(
                    send_heartbeat(
                        service_id=service_id,
                        status=success_status,
                        message=f"Operation completed: {func.__name__}",
                        metadata={
                            "operation": func.__name__,
                            "execution_time": execution_time
                        }
                    )
                )
                
                return result
                
            except Exception as e:
                # Send error heartbeat
                execution_time = time.time() - start_time
                loop.run_until_complete(
                    send_heartbeat(
                        service_id=service_id,
                        status=error_status,
                        message=f"Operation failed: {func.__name__} - {str(e)}",
                        metadata={
                            "operation": func.__name__,
                            "execution_time": execution_time,
                            "error": str(e)
                        }
                    )
                )
                raise
                
        # Return the appropriate wrapper based on whether the function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
        
    return decorator

async def generate_monitor_url(
    service_id: Optional[str] = None,
    base_url: Optional[str] = None,
    api_url: Optional[str] = None
) -> str:
    """
    Generate a URL for the web monitor dashboard.
    
    Args:
        service_id: Optional service ID to focus on
        base_url: Base URL for the web monitor (defaults to config.MONITOR_URL)
        api_url: API URL for the backend (defaults to auto-detection)
        
    Returns:
        URL string for the web monitor
    """
    from .config import MONITOR_URL
    
    # Use the provided base_url or the configured MONITOR_URL
    base_url = base_url or MONITOR_URL
    
    # Ensure base_url has the correct format
    if not base_url.startswith(('http://', 'https://')):
        base_url = 'http://' + base_url
    
    # Build the query parameters
    params = []
    
    # Add API URL if provided
    if api_url:
        # Ensure api_url has the correct format
        if not api_url.startswith(('http://', 'https://')):
            api_url = 'http://' + api_url
        params.append(f"api={api_url}")
    
    # Add service ID if provided
    if service_id:
        # Don't verify the service exists - just include it in the URL
        params.append(f"service={service_id}")
    
    # Construct the final URL
    url = base_url
    if not url.endswith("/"):
        url += "/"
    
    # Add query parameters directly
    if params:
        url += "?" + "&".join(params)
    
    return url

class HeartbeatManager:
    """Manager for heartbeat monitoring."""
    
    def __init__(
        self,
        notifiers: Optional[List[NotifierAdapter]] = None,
        storage: Optional[StorageAdapter] = None,
        check_interval: Optional[int] = None,
        stale_threshold: Optional[int] = None
    ):
        """
        Initialize the heartbeat manager.
        
        Args:
            notifiers: List of notification adapters
            storage: Storage adapter for persistence
            check_interval: Interval in seconds to check for stale heartbeats
            stale_threshold: Time in seconds after which a heartbeat is considered stale
        """
        # Get settings
        settings = get_settings()
        
        self.services: Dict[str, Dict[str, Any]] = {}
        self.notifiers: List[NotifierAdapter] = notifiers or []
        self.storage = storage
        self.check_interval = check_interval or settings.heartbeat.check_interval
        self.stale_threshold = stale_threshold or settings.heartbeat.stale_threshold
        self.monitor_task = None
        
        logger.debug(f"HeartbeatManager initialized with check_interval={self.check_interval}, stale_threshold={self.stale_threshold}")
    
    def add_notifier_adapter(self, adapter: NotifierAdapter) -> None:
        """
        Add a notifier adapter to the manager.
        
        Args:
            adapter: Notifier adapter to add
        """
        if adapter not in self.notifiers:
            self.notifiers.append(adapter)
            logger.debug(f"Added notifier adapter: {adapter.__class__.__name__}")
    
    def add_storage_adapter(self, adapter: StorageAdapter) -> None:
        """
        Set the storage adapter for the manager.
        
        Args:
            adapter: Storage adapter to set
        """
        self.storage = adapter
        logger.debug(f"Set storage adapter: {adapter.__class__.__name__}")
    
    async def start_monitor(self, check_interval: Optional[int] = None, stale_threshold: Optional[int] = None) -> None:
        """
        Start the heartbeat monitor task.
        
        Args:
            check_interval: Interval in seconds to check for stale heartbeats
            stale_threshold: Time in seconds after which a heartbeat is considered stale
        """
        # Update intervals if provided
        if check_interval is not None:
            self.check_interval = check_interval
        if stale_threshold is not None:
            self.stale_threshold = stale_threshold
            
        # Stop existing monitor if running
        if self.monitor_task and not self.monitor_task.done():
            try:
                await self.stop_monitor()
            except Exception as e:
                logger.warning(f"Error stopping existing monitor: {str(e)}")
                # Reset the monitor task if we couldn't stop it properly
                self.monitor_task = None
            
        # Start the monitor task
        self.monitor_task = asyncio.create_task(self._monitor_heartbeats())
        logger.info(f"Started heartbeat monitor (check_interval={self.check_interval}s, stale_threshold={self.stale_threshold}s)")
    
    async def stop_monitor(self) -> None:
        """Stop the heartbeat monitor task."""
        if self.monitor_task and not self.monitor_task.done():
            self.monitor_task.cancel()
            try:
                # Check if the task is in the current event loop
                current_loop = asyncio.get_running_loop()
                task_loop = self.monitor_task._loop
                
                if current_loop is task_loop:
                    # Only await the task if it's in the current event loop
                    await self.monitor_task
                else:
                    # If task is in a different loop, just cancel and don't await
                    logger.warning("Monitor task is in a different event loop, cannot await cancellation")
            except asyncio.CancelledError:
                pass
            except RuntimeError as e:
                # Handle case where there's no running event loop
                logger.warning(f"Error while stopping monitor: {str(e)}")
            
            self.monitor_task = None
            logger.info("Stopped heartbeat monitor")
    
    async def _monitor_heartbeats(self) -> None:
        """Background task to monitor heartbeats and detect stale services."""
        try:
            while True:
                await self._check_heartbeats()
                await asyncio.sleep(self.check_interval)
        except asyncio.CancelledError:
            logger.debug("Heartbeat monitor task cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in heartbeat monitor: {str(e)}", exc_info=True)
    
    async def _check_heartbeats(self) -> None:
        """Check all services for stale heartbeats."""
        now = datetime.now()
        stale_threshold = timedelta(seconds=self.stale_threshold)
        
        # Copy services to avoid modification during iteration
        services = self.services.copy()
        
        for service_id, service in services.items():
            # Skip services that are already marked as stale
            if service.get("status") == "stale":
                continue
                
            # Check if the service has a last_heartbeat
            last_heartbeat = service.get("last_heartbeat")
            if not last_heartbeat:
                continue
                
            # Convert string to datetime if needed
            if isinstance(last_heartbeat, str):
                try:
                    last_heartbeat = datetime.fromisoformat(last_heartbeat.replace("Z", "+00:00"))
                except ValueError:
                    continue
            
            # Check if the heartbeat is stale
            if now - last_heartbeat > stale_threshold:
                # Update service status to stale
                service["status"] = "stale"
                service["status_message"] = f"No heartbeat received in {self.stale_threshold} seconds"
                self.services[service_id] = service
                
                # Send notifications
                for notifier in self.notifiers:
                    try:
                        await notifier.send_notification(
                            title=f"Service Stale: {service.get('name', service_id)}",
                            message=f"No heartbeat received in {self.stale_threshold} seconds",
                            service_info=service,
                            level="warning"
                        )
                    except Exception as e:
                        logger.error(f"Error sending stale notification: {str(e)}")
                
                logger.warning(f"Service {service_id} ({service.get('name', 'Unknown')}) marked as stale")
    
    async def register_service(
        self, 
        service_name: str, 
        service_id: Optional[str] = None, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Register a new service to be monitored.
        
        Args:
            service_name: Name of the service
            service_id: Optional service ID (will be generated if not provided)
            metadata: Optional metadata for the service
            
        Returns:
            str: Service ID
        """
        # Generate service ID if not provided
        if not service_id:
            service_id = str(uuid.uuid4())
            
        # Create service record
        now = datetime.now()
        service = {
            "id": service_id,
            "name": service_name,
            "status": "unknown",
            "status_message": "Service registered",
            "last_heartbeat": None,
            "metadata": metadata or {},
            "created_at": now,
            "updated_at": now,
            "events": [
                {
                    "type": "registration",
                    "timestamp": now,
                    "status": "unknown",
                    "message": "Service registered"
                }
            ]
        }
        
        # Store service
        self.services[service_id] = service
        
        # Store in persistent storage if available
        if self.storage:
            try:
                await self.storage.store_heartbeat(service_id, service)
            except Exception as e:
                logger.error(f"Error storing service registration: {str(e)}")
        
        # Send notifications
        for notifier in self.notifiers:
            try:
                await notifier.send_notification(
                    title=f"Service Registered: {service_name}",
                    message=f"Service {service_name} registered with ID {service_id}",
                    service_info=service,
                    level="info"
                )
            except Exception as e:
                logger.error(f"Error sending registration notification: {str(e)}")
        
        logger.info(f"Service registered: {service_name} (ID: {service_id})")
        return service_id
    
    async def send_heartbeat(
        self, 
        service_id: str, 
        status: HeartbeatStatus = HeartbeatStatus.HEALTHY,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update the heartbeat status for a service.
        
        Args:
            service_id: Service ID
            status: Service status
            message: Optional status message
            metadata: Optional metadata to update
            
        Returns:
            Dict[str, Any]: Updated service information
            
        Raises:
            ServiceNotFoundError: If the service is not found
        """
        # Check if service exists
        if service_id not in self.services:
            raise ServiceNotFoundError(f"Service not found: {service_id}")
            
        # Get service
        service = self.services[service_id]
        
        # Convert status to string
        status_str = status.value if isinstance(status, HeartbeatStatus) else str(status)
        
        # Get previous status for change detection
        previous_status = service.get("status")
        
        # Update service
        now = datetime.now()
        service["status"] = status_str
        service["status_message"] = message or f"Status updated to {status_str}"
        service["last_heartbeat"] = now
        service["updated_at"] = now
        
        # Update metadata if provided
        if metadata:
            if "metadata" not in service:
                service["metadata"] = {}
            service["metadata"].update(metadata)
        
        # Add event
        event = {
            "type": "heartbeat",
            "timestamp": now,
            "status": status_str,
            "message": message or f"Status updated to {status_str}"
        }
        
        if "events" not in service:
            service["events"] = []
        service["events"].append(event)
        
        # Limit events to last 100
        if len(service["events"]) > 100:
            service["events"] = service["events"][-100:]
        
        # Store updated service
        self.services[service_id] = service
        
        # Store in persistent storage if available
        if self.storage:
            try:
                await self.storage.store_heartbeat(service_id, service)
            except Exception as e:
                logger.error(f"Error storing heartbeat: {str(e)}")
        
        # Send notifications if status changed
        if previous_status and previous_status != status_str:
            for notifier in self.notifiers:
                try:
                    # Determine notification level based on status
                    level = "info"
                    if status_str == "warning":
                        level = "warning"
                    elif status_str == "error":
                        level = "error"
                    elif status_str == "healthy" and previous_status in ["warning", "error", "stale"]:
                        level = "success"
                    
                    await notifier.send_notification(
                        title=f"Service Status Change: {service.get('name', service_id)}",
                        message=f"Status changed from {previous_status} to {status_str}" + 
                                (f": {message}" if message else ""),
                        service_info=service,
                        level=level
                    )
                except Exception as e:
                    logger.error(f"Error sending status change notification: {str(e)}")
        
        logger.debug(f"Heartbeat received for service {service_id}: {status_str}")
        return service
    
    async def get_service(self, service_id: str) -> Dict[str, Any]:
        """
        Get the current status of a service.
        
        Args:
            service_id: Service ID
            
        Returns:
            Dict[str, Any]: Service information
            
        Raises:
            ServiceNotFoundError: If the service is not found
        """
        # Check if service exists
        if service_id not in self.services:
            # Try to get from storage if available
            if self.storage:
                try:
                    service = await self.storage.get_heartbeat(service_id)
                    if service:
                        return service
                except Exception as e:
                    logger.error(f"Error retrieving service from storage: {str(e)}")
            
            raise ServiceNotFoundError(f"Service not found: {service_id}")
            
        return self.services[service_id]
    
    async def get_all_services(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all registered services.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary mapping service IDs to service information
        """
        # If storage is available, try to get all services from storage
        if self.storage:
            try:
                services = await self.storage.get_all_heartbeats()
                # Update in-memory services
                self.services.update(services)
            except Exception as e:
                logger.error(f"Error retrieving services from storage: {str(e)}")
        
        return self.services

def get_manager() -> Optional[HeartbeatManager]:
    """
    Get the global heartbeat manager instance.
    
    Returns:
        Optional[HeartbeatManager]: The global heartbeat manager instance, or None if not initialized
    """
    global _manager_instance
    
    if _manager_instance is None:
        # Create a new manager instance
        _manager_instance = HeartbeatManager()
        
        # Initialize with global state if available
        if _notifiers:
            for notifier in _notifiers:
                _manager_instance.add_notifier_adapter(notifier)
        
        if _storage:
            _manager_instance.add_storage_adapter(_storage)
        
        if _services:
            _manager_instance.services = _services.copy()
    
    return _manager_instance