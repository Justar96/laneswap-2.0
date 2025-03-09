#!/usr/bin/env python
"""
Simple example of using the progress tracking system.
"""

import asyncio
import logging
from laneswap.core.progress import with_async_progress_tracking, get_tracker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("simple_progress")

@with_async_progress_tracking()
async def simple_task(iterations: int = 5):
    """A simple task that demonstrates progress tracking."""
    tracker = get_tracker()
    execution_id = asyncio.current_task().get_name()
    
    logger.info(f"Starting task with execution ID: {execution_id}")
    
    for i in range(iterations):
        # Update progress
        progress_pct = (i / iterations) * 100
        await tracker.update_progress(
            execution_id=execution_id,
            step=f"Step {i+1}/{iterations}",
            progress=progress_pct
        )
        
        # Simulate work
        logger.info(f"Working on step {i+1}/{iterations}...")
        await asyncio.sleep(1)
    
    # Final progress update
    await tracker.update_progress(
        execution_id=execution_id,
        step="Completed",
        progress=100
    )
    
    logger.info("Task completed successfully")
    return "Success"

async def main():
    """Run the example."""
    logger.info("Starting simple progress tracking example")
    
    # Run the task
    result = await simple_task(iterations=5)
    
    logger.info(f"Task result: {result}")
    
    # Get execution statistics
    tracker = get_tracker()
    executions = tracker.get_all_executions()
    
    logger.info(f"Tracked {len(executions)} executions")
    for exec_id, exec_data in executions.items():
        logger.info(f"Execution {exec_id}: {exec_data['status']} in {exec_data.get('duration', 'N/A')}s")

if __name__ == "__main__":
    asyncio.run(main()) 