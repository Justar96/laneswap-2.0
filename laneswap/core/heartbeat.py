from typing import Dict, Any, Optional, List, Callable, Awaitable
import asyncio
import time
import uuid
from datetime import datetime
import logging
from functools import wraps

from ..adapters.base import NotifierAdapter, StorageAdapter
from ..models.heartbeat import HeartbeatStatus, HeartbeatEvent
from ..models.error import ErrorLog

logger = logging.getLogger("laneswap")

class HeartbeatManager:
    """Manages heartbeats for multiple services."""
    
    def __init__(
        self,
        notifiers: Optional[List[NotifierAdapter]] = None,
        storage: Optional[StorageAdapter] = None,
        check_interval: int = 30,
        stale_threshold: int = 60
    ):
        """
        Initialize the heartbeat manager.
        
        Args:
            notifiers: List of notification adapters (Discord, etc.)
            storage: Storage adapter for persistence (MongoDB, etc.)
            check_interval: Interval in seconds to check for stale heartbeats
            stale_threshold: Time in seconds after which a heartbeat is considered stale
        """
        self.services: Dict[str, Dict[str, Any]] = {}
        self.notifiers = notifiers or []
        self.storage = storage
        self.check_interval = check_interval
        self.stale_threshold = stale_threshold
        self._monitor_task = None

    async def register_service(self, service_id: str, service_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Register a new service to be monitored.
        
        Args:
            service_id: Unique identifier for the service
            service_name: Human-readable name for the service
            metadata: Additional information about the service
            
        Returns:
            service_id: The registered service ID
        """
        if not service_id:
            service_id = str(uuid.uuid4())
            
        self.services[service_id] = {
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
        
        self.services[service_id]["events"].append(event.dict())
        
        if self.storage:
            await self.storage.store_heartbeat(service_id, self.services[service_id])
            
        if self._monitor_task is None:
            self._monitor_task = asyncio.create_task(self._monitor_services())
            
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
            service_id: The service identifier
            status: Current health status
            message: Optional message with the heartbeat
            metadata: Additional data to include
            
        Returns:
            Dict with the updated service status
        """
        if service_id not in self.services:
            raise ValueError(f"Service with ID {service_id} not registered")
            
        now = datetime.utcnow()
        previous_status = self.services[service_id]["status"]
        
        # Create heartbeat event
        event = HeartbeatEvent(
            timestamp=now,
            status=status,
            message=message or f"Heartbeat received with status {status.value}",
            metadata=metadata
        )
        
        # Update service information
        self.services[service_id].update({
            "status": status,
            "last_heartbeat": now,
            "last_message": message,
        })
        
        if metadata:
            self.services[service_id]["metadata"].update(metadata)
            
        # Keep only the last 100 events
        self.services[service_id]["events"].append(event.dict())
        self.services[service_id]["events"] = self.services[service_id]["events"][-100:]
        
        # Persist to storage
        if self.storage:
            await self.storage.store_heartbeat(service_id, self.services[service_id])
            
        # Send notifications if status changed
        if status != previous_status:
            status_change_message = (
                f"Service '{self.services[service_id]['name']}' "
                f"status changed from {previous_status.value} to {status.value}"
            )
            
            # Only notify for non-healthy statuses or recovery to healthy
            if status != HeartbeatStatus.HEALTHY or previous_status != HeartbeatStatus.HEALTHY:
                for notifier in self.notifiers:
                    try:
                        await notifier.send_notification(
                            title=f"Service Status Change: {self.services[service_id]['name']}",
                            message=status_change_message,
                            service_info=self.services[service_id],
                            level="warning" if status != HeartbeatStatus.HEALTHY else "info"
                        )
                    except Exception as e:
                        logger.error(f"Failed to send notification: {str(e)}")
                        if self.storage:
                            error_log = ErrorLog(
                                timestamp=datetime.utcnow(),
                                service_id=service_id,
                                error_type="notification_failure",
                                message=f"Failed to send notification: {str(e)}",
                                traceback=None,
                                metadata={"notifier": notifier.__class__.__name__}
                            )
                            await self.storage.store_error(error_log.dict())
        
        return self.services[service_id]

    async def get_service_status(self, service_id: str) -> Dict[str, Any]:
        """
        Get the current status of a service.
        
        Args:
            service_id: The service identifier
            
        Returns:
            Dict with the service status information
        """
        if service_id not in self.services:
            raise ValueError(f"Service with ID {service_id} not registered")
            
        return self.services[service_id]

    async def get_all_services(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status information for all registered services.
        
        Returns:
            Dict mapping service IDs to their status information
        """
        return self.services

    async def _monitor_services(self):
        """Background task to monitor service heartbeats and detect stale services."""
        while True:
            try:
                now = datetime.utcnow()
                
                for service_id, service in self.services.items():
                    if service["last_heartbeat"] is None:
                        continue
                        
                    # Check if heartbeat is stale
                    time_since_last = (now - service["last_heartbeat"]).total_seconds()
                    
                    if time_since_last > self.stale_threshold and service["status"] != HeartbeatStatus.STALE:
                        # Update service to stale status
                        await self.send_heartbeat(
                            service_id=service_id,
                            status=HeartbeatStatus.STALE,
                            message=f"No heartbeat received in {time_since_last:.1f} seconds"
                        )
                
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in monitor task: {str(e)}")
                await asyncio.sleep(self.check_interval)

    def start_monitor(self):
        """Start the background monitoring task if not already running."""
        if self._monitor_task is None or self._monitor_task.done():
            self._monitor_task = asyncio.create_task(self._monitor_services())

    async def stop_monitor(self):
        """Stop the background monitoring task."""
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

# Decorator for wrapping functions/methods with automatic heartbeat
def with_heartbeat(
    heartbeat_manager,
    service_id: str,
    success_status: HeartbeatStatus = HeartbeatStatus.HEALTHY,
    error_status: HeartbeatStatus = HeartbeatStatus.ERROR
):
    """
    Decorator to automatically send heartbeats before and after a function execution.
    
    Args:
        heartbeat_manager: Instance of HeartbeatManager
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
                await heartbeat_manager.send_heartbeat(
                    service_id=service_id,
                    status=HeartbeatStatus.BUSY,
                    message=f"Starting operation: {func.__name__}",
                    metadata={"operation": func.__name__}
                )
                
                result = await func(*args, **kwargs)
                
                execution_time = time.time() - start_time
                await heartbeat_manager.send_heartbeat(
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
                await heartbeat_manager.send_heartbeat(
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
                    heartbeat_manager.send_heartbeat(
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
                    heartbeat_manager.send_heartbeat(
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
                    heartbeat_manager.send_heartbeat(
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

# Global instance for simple usage
_default_manager = None

def get_manager() -> HeartbeatManager:
    """Get the default heartbeat manager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = HeartbeatManager()
    return _default_manager