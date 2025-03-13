"""
Heartbeat monitoring system for tracking service health.
"""

import asyncio
import logging

# Import models
import time
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

from ..adapters.base import NotifierAdapter, StorageAdapter
from ..models.error import ErrorLog
from ..models.heartbeat import HeartbeatEvent
from .config import get_settings
from .exceptions import ServiceNotFoundError
from .types import HeartbeatStatus

# Import validator
try:
    from .validator import ValidationError, run_validation
    _validator_available = True
except ImportError:
    _validator_available = False

logger = logging.getLogger("laneswap")

# Global state
_services: Dict[str, Dict[str, Any]] = {}
_notifiers: List[NotifierAdapter] = []
_storage: Optional[StorageAdapter] = None
_check_interval: int = 30
_stale_threshold: int = 60
_monitor_task = None
_manager_instance = None
_validation_performed = False

async def initialize(
    notifiers: Optional[List[NotifierAdapter]] = None,
    storage: Optional[StorageAdapter] = None,
    check_interval: Optional[int] = None,
    stale_threshold: Optional[int] = None,
    validate: bool = True
) -> None:
    """
    Initialize the heartbeat system with the given configuration.

    Args:
        notifiers: List of notifier adapters to use
        storage: Storage adapter to use
        check_interval: Interval in seconds to check for stale services
        stale_threshold: Threshold in seconds to consider a service stale
        validate: Whether to run system validation
    """
    global _manager_instance, _validation_performed

    # Get the manager instance
    manager = get_manager()
    _manager_instance = manager

    # Add notifiers
    if notifiers:
        for notifier in notifiers:
            manager.add_notifier_adapter(notifier)

    # Add storage
    if storage:
        manager.add_storage_adapter(storage)

    if check_interval is not None or stale_threshold is not None:
        await manager.start_monitor(check_interval, stale_threshold)

    # Run validation if requested
    if validate and _validator_available and not _validation_performed:
        try:
            from .validator import run_validation
            run_validation(check_terminal_monitor=True, print_results=True)
            _validation_performed = True
        except Exception as e:
            logger.warning("System validation failed: %s", str(e))

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
    global _validation_performed

    # Run validation if not already performed
    if _validator_available and not _validation_performed:
        try:
            from .validator import run_validation
            run_validation(check_terminal_monitor=True, print_results=True)
            _validation_performed = True
        except Exception as e:
            logger.warning("System validation failed: %s", str(e))

    # Get the manager
    manager = get_manager()

    # Register the service
    return await manager.register_service(service_name, service_id, metadata)

async def send_heartbeat(
    service_id: str,
    status: HeartbeatStatus = HeartbeatStatus.HEALTHY,
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Update the heartbeat status for a service.

    Args:
        service_id: Service ID
        status: Service status
        message: Optional status message
        metadata: Optional metadata to update

    Returns:
        bool: True if the heartbeat was sent successfully

    Raises:
        ServiceNotFoundError: If the service is not found
    """
    # Get the manager
    manager = get_manager()

    # Send the heartbeat
    await manager.send_heartbeat(service_id, status, message, metadata)
    return True

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
    stale_threshold: int = 60,
    validate: bool = True
):
    """
    Context manager for the heartbeat system.

    Args:
        notifiers: List of notification adapters (Discord, etc.)
        storage: Storage adapter for persistence (MongoDB, etc.)
        check_interval: Interval in seconds to check for stale heartbeats
        stale_threshold: Time in seconds after which a heartbeat is considered stale
        validate: Whether to validate the system configuration
    """
    try:
        # Initialize the system
        await initialize(
            notifiers=notifiers,
            storage=storage,
            check_interval=check_interval,
            stale_threshold=stale_threshold,
            validate=validate
        )

        # Start the monitor
        manager = get_manager()
        if manager:
            await manager.start_monitor()

        # Yield control back to the caller
        yield
    finally:
        # Stop the monitor
        manager = get_manager()
        if manager:
            await manager.stop_monitor()

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
    """
    Manager for heartbeat monitoring.
    """

    def __init__(
        self,
        notifiers: Optional[List[NotifierAdapter]] = None,
        storage: Optional[StorageAdapter] = None,
        check_interval: Optional[int] = None,
        stale_threshold: Optional[int] = None,
        validate: bool = True
    ):
        """
        Initialize a new HeartbeatManager.

        Args:
            notifiers: List of notifier adapters to use
            storage: Storage adapter to use
            check_interval: Interval in seconds to check for stale services
            stale_threshold: Threshold in seconds to consider a service stale
            validate: Whether to run system validation
        """
        global _validation_performed

        # Initialize services dictionary
        self._services = {}

        # Initialize notifiers
        self._notifiers = []
        if notifiers:
            for notifier in notifiers:
                self.add_notifier_adapter(notifier)

        # Initialize storage
        self._storage = None
        if storage:
            self.add_storage_adapter(storage)

        # Set check interval and stale threshold
        self._check_interval = check_interval or _check_interval
        self._stale_threshold = stale_threshold or _stale_threshold

        # Initialize monitor task and state
        self._monitor_task = None
        self._monitor_running = False

        # Run validation if requested
        if validate and _validator_available:
            try:
                from .validator import run_validation
                run_validation(check_terminal_monitor=True, print_results=True)
                _validation_performed = True
            except Exception as e:
                logger.warning("System validation failed: %s", str(e))

    def add_notifier_adapter(self, adapter: NotifierAdapter) -> None:
        """
        Add a notifier adapter to the manager.

        Args:
            adapter: Notifier adapter to add
        """
        if adapter not in self._notifiers:
            self._notifiers.append(adapter)
            logger.debug("Added notifier adapter: %s", adapter.__class__.__name__)

    def add_storage_adapter(self, adapter: StorageAdapter) -> None:
        """
        Set the storage adapter for the manager.

        Args:
            adapter: Storage adapter to set
        """
        self._storage = adapter
        logger.debug("Set storage adapter: %s", adapter.__class__.__name__)

    async def start_monitor(self, check_interval: Optional[int] =
        None, stale_threshold: Optional[int] = None) -> None:
        """
        Start the heartbeat monitor task.

        Args:
            check_interval: Interval in seconds to check for stale heartbeats
            stale_threshold: Time in seconds after which a heartbeat is considered stale
        """
        # Update intervals if provided
        if check_interval is not None:
            self._check_interval = check_interval
        if stale_threshold is not None:
            self._stale_threshold = stale_threshold

        # Stop existing monitor if running
        if self._monitor_task and not self._monitor_task.done():
            try:
                await self.stop_monitor()
            except Exception as e:
                logger.warning("Error stopping existing monitor: %s", str(e))
                # Reset the monitor task if we couldn't stop it properly
                self._monitor_task = None

        # Start the monitor task
        self._monitor_task = asyncio.create_task(self._monitor_heartbeats())
        self._monitor_running = True
        logger.info("Started heartbeat monitor (check_interval=%ss, stale_threshold=%ss)", self._check_interval, self._stale_threshold)

    async def stop_monitor(self) -> None:
        """Stop the heartbeat monitor task."""
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                # Check if the task is in the current event loop
                current_loop = asyncio.get_running_loop()
                task_loop = self._monitor_task._loop

                if current_loop is task_loop:
                    # Only await the task if it's in the current event loop
                    await self._monitor_task
                else:
                    # If task is in a different loop, just cancel and don't await
                    logger.warning("Monitor task is in a different event loop, cannot await cancellation")
            except asyncio.CancelledError:
                pass
            except RuntimeError as e:
                # Handle case where there's no running event loop
                logger.warning("Error while stopping monitor: %s", str(e))

            self._monitor_task = None
            self._monitor_running = False
            logger.info("Stopped heartbeat monitor")

    async def _monitor_heartbeats(self) -> None:
        """Background task to monitor heartbeats and detect stale services."""
        try:
            while True:
                await self._check_heartbeats()
                await asyncio.sleep(self._check_interval)
        except asyncio.CancelledError:
            logger.debug("Heartbeat monitor task cancelled")
            raise
        except Exception as e:
            logger.error("Error in heartbeat monitor: %s", str(e), exc_info=True)

    async def _check_heartbeats(self) -> None:
        """Check all services for stale heartbeats."""
        now = datetime.now(UTC)
        stale_threshold = timedelta(seconds=self._stale_threshold)

        # Copy services to avoid modification during iteration
        services = self._services.copy()

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
                service["status_message"] = f"No heartbeat received in {self._stale_threshold} seconds"
                self._services[service_id] = service

                # Send notifications
                for notifier in self._notifiers:
                    try:
                        await notifier.send_notification(
                            title=f"Service Stale: {service.get('name', service_id)}",
                            message=f"No heartbeat received in {self._stale_threshold} seconds",
                            service_info=service,
                            level="warning"
                        )
                    except Exception as e:
                        logger.error("Error sending stale notification: %s", str(e))

                logger.warning("Service %s (%s) marked as stale", service_id, service.get('name', 'Unknown'))

    async def register_service(
        self,
        service_name: str,
        service_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Register a new service with the heartbeat system.

        Args:
            service_name: Name of the service
            service_id: Optional service ID (will be generated if not provided)
            metadata: Optional metadata for the service

        Returns:
            Service ID
        """
        global _validation_performed

        # Run validation if not already performed
        if _validator_available and not _validation_performed:
            try:
                from .validator import run_validation
                run_validation(check_terminal_monitor=True, print_results=True)
                _validation_performed = True
            except Exception as e:
                logger.warning("System validation failed: %s", str(e))

        # Generate service ID if not provided
        if service_id is None:
            service_id = str(uuid.uuid4())

        # Create service entry
        service = {
            "id": service_id,
            "name": service_name,
            "status": HeartbeatStatus.UNKNOWN,
            "created_at": datetime.now(UTC).isoformat(),
            "last_heartbeat": None,
            "last_message": None,
            "metadata": metadata or {},
            "events": []
        }

        # Add to services dict
        self._services[service_id] = service

        # Store in persistent storage if available
        if self._storage:
            try:
                await self._storage.store_service(service)
            except Exception as e:
                logger.error("Error storing service in persistent storage: %s", str(e))

        logger.info("Service registered: %s (ID: %s)", service_name, service_id)

        return service_id

    async def send_heartbeat(
        self,
        service_id: str,
        status: HeartbeatStatus = HeartbeatStatus.HEALTHY,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update the heartbeat status for a service.

        Args:
            service_id: Service ID
            status: Service status
            message: Optional status message
            metadata: Optional metadata to update

        Returns:
            bool: True if the heartbeat was sent successfully

        Raises:
            ServiceNotFoundError: If the service is not found
        """
        # Check if service exists
        if service_id not in self._services:
            raise ServiceNotFoundError(f"Service not found: {service_id}")

        # Get service
        service = self._services[service_id]

        # Convert status to string
        status_str = status.value if isinstance(status, HeartbeatStatus) else str(status)

        # Get previous status for change detection
        previous_status = service.get("status")

        # Update service
        now = datetime.now(UTC)
        service["status"] = status_str
        service["status_message"] = message or f"Status updated to {status_str}"
        service["message"] = message  # Add message field
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
        self._services[service_id] = service

        # Store in persistent storage if available
        if self._storage:
            try:
                await self._storage.store_heartbeat(service_id, service)
            except Exception as e:
                logger.error("Error storing heartbeat: %s", str(e))
                return False

        # Send notifications if status changed
        if previous_status and previous_status != status_str:
            for notifier in self._notifiers:
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
                    logger.error("Error sending status change notification: %s", str(e))

        logger.debug("Heartbeat received for service %s: %s", service_id, status_str)
        return True

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
        if service_id not in self._services:
            # Try to get from storage if available
            if self._storage:
                try:
                    service = await self._storage.get_heartbeat(service_id)
                    if service:
                        return service
                except Exception as e:
                    logger.error("Error retrieving service from storage: %s", str(e))

            raise ServiceNotFoundError(f"Service not found: {service_id}")

        return self._services[service_id]

    async def get_all_services(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all registered services.

        Returns:
            Dict[str, Dict[str, Any]]: Dictionary mapping service IDs to service information
        """
        # If storage is available, try to get all services from storage
        if self._storage:
            try:
                services = await self._storage.get_all_heartbeats()
                # Update in-memory services
                self._services.update(services)
            except Exception as e:
                logger.error("Error retrieving services from storage: %s", str(e))

        return self._services

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
