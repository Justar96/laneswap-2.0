"""
Progress tracking module for monitoring function execution.

This module provides tools for tracking the progress of function execution,
collecting performance metrics, and reporting issues.
"""

import asyncio
import functools
import inspect
import logging
import time
import traceback
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

from .exceptions import LaneSwapError
from .types import HeartbeatStatus, ProgressStatus

logger = logging.getLogger("laneswap.progress")

# Type variables for function decorators
F = TypeVar('F', bound=Callable[..., Any])
AsyncF = TypeVar('AsyncF', bound=Callable[..., Any])

class ProgressTracker:
    """Tracks the progress of function execution."""

    def __init__(
        self,
        service_id: Optional[str] = None,
        heartbeat_manager = None,
        report_heartbeats: bool = True
    ):
        """
        Initialize the progress tracker.

        Args:
            service_id: Service ID to associate with progress tracking
            heartbeat_manager: HeartbeatManager instance to use for reporting
            report_heartbeats: Whether to report progress as heartbeats
        """
        self.service_id = service_id
        self.heartbeat_manager = heartbeat_manager
        if heartbeat_manager is None:
            # Lazy import to avoid circular imports
            from .heartbeat import get_manager
            self.heartbeat_manager = get_manager()

        self.report_heartbeats = report_heartbeats
        self.executions: Dict[str, Dict[str, Any]] = {}

    async def start_execution(
        self,
        function_name: str,
        execution_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start tracking a function execution.

        Args:
            function_name: Name of the function being executed
            execution_id: Optional ID for the execution (generated if not provided)
            metadata: Additional information about the execution

        Returns:
            execution_id: ID for the execution
        """
        if not execution_id:
            execution_id = str(uuid.uuid4())

        start_time = datetime.now(UTC)

        self.executions[execution_id] = {
            "id": execution_id,
            "function": function_name,
            "status": ProgressStatus.RUNNING,
            "start_time": start_time,
            "end_time": None,
            "duration": None,
            "metadata": metadata or {},
            "steps": [],
            "error": None
        }

        if self.report_heartbeats and self.service_id:
            await self.heartbeat_manager.send_heartbeat(
                service_id=self.service_id,
                status=HeartbeatStatus.BUSY,
                message=f"Started execution of {function_name}",
                metadata={
                    "execution_id": execution_id,
                    "function": function_name,
                    "progress": {
                        "status": ProgressStatus.RUNNING,
                        "start_time": start_time.isoformat()
                    }
                }
            )

        return execution_id

    async def update_progress(
        self,
        execution_id: str,
        step: str,
        progress: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update the progress of a function execution.

        Args:
            execution_id: ID of the execution to update
            step: Description of the current step
            progress: Optional progress percentage (0-100)
            metadata: Additional information about the step

        Returns:
            bool: Whether the update was successful
        """
        if execution_id not in self.executions:
            logger.warning("Execution ID %s not found", execution_id)
            # Create a new execution record if it doesn't exist
            function_name = "unknown"
            await self.start_execution(
                function_name=function_name,
                execution_id=execution_id,
                metadata={"auto_created": True}
            )

        timestamp = datetime.now(UTC)

        step_info = {
            "timestamp": timestamp,
            "description": step,
            "progress": progress,
            "metadata": metadata or {}
        }

        self.executions[execution_id]["steps"].append(step_info)

        if self.report_heartbeats and self.service_id:
            try:
                await self.heartbeat_manager.send_heartbeat(
                    service_id=self.service_id,
                    status=HeartbeatStatus.BUSY,
                    message=f"Progress update: {step}",
                    metadata={
                        "execution_id": execution_id,
                        "progress": {
                            "step": step,
                            "progress": progress,
                            "timestamp": timestamp.isoformat()
                        }
                    }
                )
            except Exception as e:
                logger.error("Failed to send heartbeat: %s", str(e))

        return True

    async def complete_execution(
        self,
        execution_id: str,
        result: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Mark a function execution as completed.

        Args:
            execution_id: ID of the execution to complete
            result: Optional result of the execution
            metadata: Additional information about the completion

        Returns:
            Dict with execution details
        """
        if execution_id not in self.executions:
            logger.warning("Execution ID %s not found", execution_id)
            return {}

        end_time = datetime.now(UTC)
        start_time = self.executions[execution_id]["start_time"]
        duration = (end_time - start_time).total_seconds()

        self.executions[execution_id].update({
            "status": ProgressStatus.COMPLETED,
            "end_time": end_time,
            "duration": duration,
            "result": result,
            "metadata": {**self.executions[execution_id]["metadata"], **(metadata or {})}
        })

        if self.report_heartbeats and self.service_id:
            function_name = self.executions[execution_id]["function"]
            await self.heartbeat_manager.send_heartbeat(
                service_id=self.service_id,
                status=HeartbeatStatus.HEALTHY,
                message=f"Completed execution of {function_name} in {duration:.2f}s",
                metadata={
                    "execution_id": execution_id,
                    "function": function_name,
                    "progress": {
                        "status": ProgressStatus.COMPLETED,
                        "duration": duration,
                        "end_time": end_time.isoformat()
                    }
                }
            )

        return self.executions[execution_id]

    async def fail_execution(
        self,
        execution_id: str,
        error: Union[str, Exception],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Mark a function execution as failed.

        Args:
            execution_id: ID of the execution that failed
            error: Error information
            metadata: Additional information about the failure

        Returns:
            Dict with execution details
        """
        if execution_id not in self.executions:
            logger.warning("Execution ID %s not found", execution_id)
            return {}

        end_time = datetime.now(UTC)
        start_time = self.executions[execution_id]["start_time"]
        duration = (end_time - start_time).total_seconds()

        error_info = {
            "message": str(error),
            "type": error.__class__.__name__ if isinstance(error, Exception) else "Error",
            "traceback": traceback.format_exc() if isinstance(error, Exception) else None
        }

        self.executions[execution_id].update({
            "status": ProgressStatus.FAILED,
            "end_time": end_time,
            "duration": duration,
            "error": error_info,
            "metadata": {**self.executions[execution_id]["metadata"], **(metadata or {})}
        })

        if self.report_heartbeats and self.service_id:
            function_name = self.executions[execution_id]["function"]
            await self.heartbeat_manager.send_heartbeat(
                service_id=self.service_id,
                status=HeartbeatStatus.ERROR,
                message=f"Failed execution of {function_name}: {str(error)}",
                metadata={
                    "execution_id": execution_id,
                    "function": function_name,
                    "progress": {
                        "status": ProgressStatus.FAILED,
                        "duration": duration,
                        "error": error_info,
                        "end_time": end_time.isoformat()
                    }
                }
            )

        return self.executions[execution_id]

    def get_execution(self, execution_id: str) -> Dict[str, Any]:
        """
        Get details about a function execution.

        Args:
            execution_id: ID of the execution to retrieve

        Returns:
            Dict with execution details
        """
        return self.executions.get(execution_id, {})

    def get_all_executions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get details about all tracked executions.

        Returns:
            Dict mapping execution IDs to execution details
        """
        return self.executions

# Global instance for simple usage
_default_tracker = None

def get_tracker() -> "ProgressTracker":
    """Get or create the default progress tracker instance."""
    global _default_tracker
    if _default_tracker is None:
        logger.debug("Creating new ProgressTracker instance")
        _default_tracker = ProgressTracker()
    return _default_tracker

def with_progress_tracking(
    tracker: Optional[ProgressTracker] = None,
    execution_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Callable[[F], F]:
    """
    Decorator to track the progress of a function execution.

    Args:
        tracker: ProgressTracker instance to use
        execution_id: Optional ID for the execution
        metadata: Additional information about the execution

    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get the tracker
            progress_tracker = tracker or get_tracker()

            # Get function name
            function_name = func.__qualname__

            # Create execution context
            exec_id = execution_id or str(uuid.uuid4())

            # Start execution tracking
            loop = asyncio.get_event_loop()
            loop.run_until_complete(
                progress_tracker.start_execution(
                    function_name=function_name,
                    execution_id=exec_id,
                    metadata=metadata
                )
            )

            try:
                # Execute the function
                result = func(*args, **kwargs)

                # Complete execution tracking
                loop.run_until_complete(
                    progress_tracker.complete_execution(
                        execution_id=exec_id,
                        result=None  # Don't store the actual result
                    )
                )

                return result
            except Exception as e:
                # Handle failure
                loop.run_until_complete(
                    progress_tracker.fail_execution(
                        execution_id=exec_id,
                        error=e
                    )
                )
                raise

        return wrapper  # type: ignore

    return decorator

def with_async_progress_tracking(function_name=None):
    """Decorator for tracking progress of async functions."""
    def decorator(func):
        nonlocal function_name
        if function_name is None:
            function_name = func.__name__

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            progress_tracker = get_tracker()

            # Generate a unique execution ID
            exec_id = str(uuid.uuid4())

            # Store the execution ID in the task's context
            task = asyncio.current_task()
            if not hasattr(task, '_execution_ids'):
                task._execution_ids = {}
            task._execution_ids[func.__name__] = exec_id

            # Start execution tracking
            await progress_tracker.start_execution(
                function_name=function_name,
                execution_id=exec_id,
                metadata={"args": str(args), "kwargs": str(kwargs)}
            )

            try:
                # Execute the function
                result = await func(*args, **kwargs)

                # Complete execution tracking
                await progress_tracker.complete_execution(
                    execution_id=exec_id,
                    result=None  # Don't store the actual result
                )

                return result
            except Exception as e:
                # Handle failure
                await progress_tracker.fail_execution(
                    execution_id=exec_id,
                    error=e
                )
                raise

        return wrapper

    return decorator
