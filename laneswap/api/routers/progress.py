"""
API routes for progress tracking and function execution monitoring.
"""

# Import directly from core modules
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from ...core.progress import ProgressStatus, ProgressTracker, get_tracker
from ...models.progress import ExecutionDetail, ExecutionStatistics, ExecutionSummary

router = APIRouter()

@router.get(
    "/executions",
    response_model=Dict[str, Any],
    summary="Get all function executions"
)
async def get_all_executions(
    status: Optional[ProgressStatus] = Query(None, description="Filter by execution status"),
    function: Optional[str] = Query(None, description="Filter by function name"),
    limit: int = Query(100, description="Maximum number of executions to return"),
    tracker: ProgressTracker = Depends(get_tracker)
):
    """
    Get information about all tracked function executions.

    Args:
        status: Optional filter by execution status
        function: Optional filter by function name
        limit: Maximum number of executions to return

    Returns:
        Dict with executions and summary statistics
    """
    executions = tracker.get_all_executions()

    # Apply filters
    filtered_executions = {}
    for exec_id, exec_data in executions.items():
        if status and exec_data.get("status") != status:
            continue

        if function and exec_data.get("function") != function:
            continue

        filtered_executions[exec_id] = exec_data

        if len(filtered_executions) >= limit:
            break

    # Calculate statistics
    total_executions = len(executions)
    status_counts = {}
    function_counts = {}
    avg_duration = 0
    completed_count = 0

    for exec_data in executions.values():
        status = exec_data.get("status")
        function = exec_data.get("function")
        duration = exec_data.get("duration")

        status_counts[status] = status_counts.get(status, 0) + 1
        function_counts[function] = function_counts.get(function, 0) + 1

        if status == ProgressStatus.COMPLETED and duration is not None:
            avg_duration += duration
            completed_count += 1

    if completed_count > 0:
        avg_duration /= completed_count

    return {
        "executions": filtered_executions,
        "statistics": {
            "total": total_executions,
            "status_counts": status_counts,
            "function_counts": function_counts,
            "avg_duration": avg_duration
        }
    }

@router.get(
    "/executions/{execution_id}",
    response_model=ExecutionDetail,
    summary="Get execution details"
)
async def get_execution_details(
    execution_id: str = Path(..., description="Execution identifier"),
    tracker: ProgressTracker = Depends(get_tracker)
):
    """
    Get detailed information about a specific function execution.

    Args:
        execution_id: Execution identifier

    Returns:
        Detailed execution information
    """
    execution = tracker.get_execution(execution_id)

    if not execution:
        raise HTTPException(status_code=404, detail=f"Execution with ID {execution_id} not found")

    return execution

@router.get(
    "/statistics",
    response_model=ExecutionStatistics,
    summary="Get execution statistics"
)
async def get_execution_statistics(
    tracker: ProgressTracker = Depends(get_tracker)
):
    """
    Get statistics about function executions.

    Returns:
        Execution statistics
    """
    executions = tracker.get_all_executions()

    # Calculate statistics
    total_executions = len(executions)
    status_counts = {}
    function_counts = {}
    avg_duration = 0
    completed_count = 0

    for exec_data in executions.values():
        status = exec_data.get("status")
        function = exec_data.get("function")
        duration = exec_data.get("duration")

        status_counts[status] = status_counts.get(status, 0) + 1
        function_counts[function] = function_counts.get(function, 0) + 1

        if status == ProgressStatus.COMPLETED and duration is not None:
            avg_duration += duration
            completed_count += 1

    if completed_count > 0:
        avg_duration /= completed_count

    return {
        "total": total_executions,
        "status_counts": status_counts,
        "function_counts": function_counts,
        "avg_duration": avg_duration,
        "success_rate": (status_counts.get(ProgressStatus.COMPLETED, 0) / total_executions) if total_executions > 0 else 0
    }
