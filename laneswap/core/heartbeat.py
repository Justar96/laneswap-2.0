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

async def initialize(
    notifiers: Optional[List[NotifierAdapter]] = None,
    storage: Optional[StorageAdapter] = None,
    check_interval: int = 30,
    stale_threshold: int = 60
) -> None:
    """
    Initialize the heartbeat system.
    
    Args:
        notifiers: List of notification adapters (Discord, etc.)
        storage: Storage adapter for persistence (MongoDB, etc.)
        check_interval: Interval in seconds to check for stale heartbeats
        stale_threshold: Time in seconds after which a heartbeat is considered stale
    """
    global _notifiers, _storage, _check_interval, _stale_threshold
    
    _notifiers = notifiers or []
    _storage = storage
    _check_interval = check_interval
    _stale_threshold = stale_threshold
    
    # Connect to storage if provided
    if _storage:
        try:
            await _storage.connect()
        except Exception as e:
            logger.error(f"Failed to connect to storage: {str(e)}")
    
    # Start the monitor task
    await start_monitor()

async def register_service(
    service_name: str, 
    service_id: Optional[str] = None, 
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Register a new service to be monitored.
    
    Args:
        service_name: Human-readable name for the service
        service_id: Optional unique identifier for the service (generated if not provided)
        metadata: Additional information about the service
        
    Returns:
        service_id: The registered service ID
    """
    global _services
    
    if not service_id:
        service_id = str(uuid.uuid4())
        
    _services[service_id] = {
        "id": service_id,
        "name": service_name,
        "status": HeartbeatStatus.UNKNOWN,
        "last_heartbeat": None,
        "metadata": metadata or {},
        "events": []
    }
    
    event = HeartbeatEvent(
        timestamp=datetime.utcnow(),
        status=HeartbeatStatus.UNKNOWN,
        message=f"Service {service_name} registered"
    )
    
    _services[service_id]["events"].append(event.dict())
    
    if _storage:
        await _storage.store_heartbeat(service_id, _services[service_id])
        
    if _monitor_task is None:
        await start_monitor()
        
    return service_id

async def send_heartbeat(
    service_id: str, 
    status: HeartbeatStatus = HeartbeatStatus.HEALTHY,
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Update the heartbeat status for a service.
    
    Args:
        service_id: The service identifier
        status: Current health status
        message: Optional message with the heartbeat
        metadata: Additional data to include
        
    Returns:
        Dict with the updated service status
    """
    global _services, _notifiers, _storage
    
    if service_id not in _services:
        raise ServiceNotFoundError(f"Service with ID {service_id} not registered")
        
    now = datetime.utcnow()
    previous_status = _services[service_id]["status"]
    
    # Create heartbeat event
    event = HeartbeatEvent(
        timestamp=now,
        status=status,
        message=message or f"Heartbeat received with status {status.value}",
        metadata=metadata
    )
    
    # Update service information
    _services[service_id].update({
        "status": status,
        "last_heartbeat": now,
        "last_message": message,
    })
    
    if metadata:
        _services[service_id]["metadata"].update(metadata)
        
    # Keep only the last 100 events
    _services[service_id]["events"].append(event.dict())
    _services[service_id]["events"] = _services[service_id]["events"][-100:]
    
    # Persist to storage
    if _storage:
        await _storage.store_heartbeat(service_id, _services[service_id])
        
    # Send notifications if status changed
    if status != previous_status:
        status_change_message = (
            f"Service '{_services[service_id]['name']}' "
            f"status changed from {previous_status.value} to {status.value}"
        )
        
        # Only notify for non-healthy statuses or recovery to healthy
        if status != HeartbeatStatus.HEALTHY or previous_status != HeartbeatStatus.HEALTHY:
            for notifier in _notifiers:
                try:
                    await notifier.send_notification(
                        title=f"Service Status Change: {_services[service_id]['name']}",
                        message=status_change_message,
                        service_info=_services[service_id],
                        level="warning" if status != HeartbeatStatus.HEALTHY else "info"
                    )
                except Exception as e:
                    logger.error(f"Failed to send notification: {str(e)}")
                    if _storage:
                        error_log = ErrorLog(
                            timestamp=datetime.utcnow(),
                            service_id=service_id,
                            error_type="notification_failure",
                            message=f"Failed to send notification: {str(e)}",
                            traceback=None,
                            metadata={"notifier": notifier.__class__.__name__}
                        )
                        await _storage.store_error(error_log.dict())
    
    return _services[service_id]

async def get_service(service_id: str) -> Dict[str, Any]:
    """
    Get the current status of a service.
    
    Args:
        service_id: The service identifier
        
    Returns:
        Dict with the service status information
    
    Raises:
        ServiceNotFoundError: If the service ID is not found
    """
    if service_id not in _services:
        raise ServiceNotFoundError(f"Service with ID {service_id} not registered")
        
    return _services[service_id]

async def get_all_services() -> Dict[str, Dict[str, Any]]:
    """
    Get status information for all registered services.
    
    Returns:
        Dict mapping service IDs to their status information
    """
    return _services

async def _monitor_heartbeats():
    """Background task to monitor service heartbeats and detect stale services."""
    global _services, _check_interval, _stale_threshold
    
    while True:
        try:
            now = datetime.utcnow()
            
            for service_id, service in _services.items():
                if service["last_heartbeat"] is None:
                    continue
                    
                # Check if heartbeat is stale
                time_since_last = (now - service["last_heartbeat"]).total_seconds()
                
                if time_since_last > _stale_threshold and service["status"] != HeartbeatStatus.STALE:
                    # Update service to stale status
                    await send_heartbeat(
                        service_id=service_id,
                        status=HeartbeatStatus.STALE,
                        message=f"No heartbeat received in {time_since_last:.1f} seconds"
                    )
            
            await asyncio.sleep(_check_interval)
        except Exception as e:
            logger.error(f"Error in monitor task: {str(e)}")
            await asyncio.sleep(_check_interval)

async def start_monitor():
    """Start the background task to check for stale heartbeats."""
    global _monitor_task
    
    # If the monitor is already running, don't start another one
    if _monitor_task and not _monitor_task.done() and not _monitor_task.cancelled():
        logger.debug("Heartbeat monitor already running")
        return
    
    # Create a new monitor task
    _monitor_task = asyncio.create_task(_monitor_heartbeats())
    logger.debug("Heartbeat monitor started")

async def stop_monitor():
    """Stop the background monitoring task."""
    global _monitor_task
    
    if _monitor_task and not _monitor_task.done():
        _monitor_task.cancel()
        try:
            await _monitor_task
        except asyncio.CancelledError:
            pass
        _monitor_task = None

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
        await stop_monitor()

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

# Compatibility layer for code that expects the HeartbeatManager class
class HeartbeatManager:
    """
    Compatibility class for backward compatibility.
    This class wraps the functional API to maintain compatibility with code
    that expects the HeartbeatManager class.
    """
    
    def __init__(
        self,
        notifiers: Optional[List[NotifierAdapter]] = None,
        storage: Optional[StorageAdapter] = None,
        check_interval: int = 30,
        stale_threshold: int = 60
    ):
        """Initialize the heartbeat manager."""
        self.notifiers = notifiers or []
        self.storage = storage
        self.check_interval = check_interval
        self.stale_threshold = stale_threshold
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Ensure the heartbeat system is initialized."""
        if not self._initialized:
            await initialize(
                notifiers=self.notifiers,
                storage=self.storage,
                check_interval=self.check_interval,
                stale_threshold=self.stale_threshold
            )
            self._initialized = True
    
    async def register_service(
        self, 
        service_name: str, 
        service_id: Optional[str] = None, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Register a new service to be monitored."""
        await self._ensure_initialized()
        return await register_service(service_name, service_id, metadata)
    
    async def send_heartbeat(
        self, 
        service_id: str, 
        status: HeartbeatStatus = HeartbeatStatus.HEALTHY,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update the heartbeat status for a service."""
        await self._ensure_initialized()
        return await send_heartbeat(service_id, status, message, metadata)
    
    async def get_service(self, service_id: str) -> Dict[str, Any]:
        """Get the current status of a service."""
        await self._ensure_initialized()
        return await get_service(service_id)
    
    async def get_all_services(self) -> Dict[str, Any]:
        """Get all registered services."""
        await self._ensure_initialized()
        return await get_all_services()
    
    async def start_monitor(self):
        """Start the heartbeat monitor task."""
        await self._ensure_initialized()
        # The monitor is started automatically during initialization
    
    async def stop_monitor(self):
        """Stop the background monitoring task."""
        if self._initialized:
            await stop_monitor()
            self._initialized = False

# For backward compatibility
def get_manager() -> HeartbeatManager:
    """Get or create the default heartbeat manager instance."""
    return HeartbeatManager()