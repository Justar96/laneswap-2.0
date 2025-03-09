#!/usr/bin/env python
"""
Example service demonstrating progress tracking.

This script shows how to use the progress tracking functionality
to monitor function execution and report progress.
"""

import asyncio
import random
import logging
import argparse
from typing import Dict, Any, List

from laneswap.client.async_client import LaneswapAsyncClient
from laneswap.core.progress import with_async_progress_tracking, ProgressTracker
from laneswap.core.heartbeat import HeartbeatStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("progress_service")

class DataProcessor:
    """Example data processor with progress tracking."""
    
    def __init__(self, client: LaneswapAsyncClient):
        """Initialize the data processor."""
        self.client = client
        
        # Try to get heartbeat_manager from client, or use a fallback
        heartbeat_manager = getattr(client, 'heartbeat_manager', None)
        
        self.tracker = ProgressTracker(
            service_id=client.service_id,
            heartbeat_manager=heartbeat_manager,
            report_heartbeats=True
        )
        
    @with_async_progress_tracking()
    async def process_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a list of data items with progress tracking.
        
        Args:
            data: List of data items to process
            
        Returns:
            Processed data items
        """
        total_items = len(data)
        processed_data = []
        
        # Get the execution ID from the task context
        task = asyncio.current_task()
        execution_id = getattr(task, '_execution_ids', {}).get(self.process_data.__name__, 'unknown')
        logger.debug(f"Using execution ID: {execution_id}")
        logger.debug(f"Task execution IDs: {getattr(task, '_execution_ids', {})}")
        
        # Small delay to ensure execution ID is registered
        await asyncio.sleep(0.1)
        
        # Step 1: Validate data
        await self.tracker.update_progress(
            execution_id=execution_id,
            step="Validating data",
            progress=0
        )
        
        await asyncio.sleep(1)  # Simulate work
        
        # Step 2: Process each item
        for i, item in enumerate(data):
            progress_pct = (i / total_items) * 100
            
            await self.tracker.update_progress(
                execution_id=execution_id,
                step=f"Processing item {i+1}/{total_items}",
                progress=progress_pct,
                metadata={"item_id": item.get("id")}
            )
            
            # Simulate processing work
            await asyncio.sleep(random.uniform(0.1, 0.5))
            
            # Simulate occasional errors
            if random.random() < 0.1:
                if random.random() < 0.5:
                    # Recoverable error
                    logger.warning(f"Recoverable error processing item {item.get('id')}")
                    await self.client.send_heartbeat(
                        status=HeartbeatStatus.DEGRADED,
                        message=f"Recoverable error processing item {item.get('id')}"
                    )
                    continue
                else:
                    # Non-recoverable error (1% chance)
                    if random.random() < 0.1:
                        logger.error(f"Fatal error processing item {item.get('id')}")
                        raise RuntimeError(f"Fatal error processing item {item.get('id')}")
            
            # Process the item
            processed_item = {
                **item,
                "processed": True,
                "timestamp": "2023-01-01T00:00:00Z"
            }
            
            processed_data.append(processed_item)
        
        # Step 3: Finalize processing
        await self.tracker.update_progress(
            execution_id=execution_id,
            step="Finalizing processing",
            progress=100
        )
        
        await asyncio.sleep(0.5)  # Simulate work
        
        return processed_data

async def main():
    """Main entry point for the example service."""
    parser = argparse.ArgumentParser(description="Example service with progress tracking")
    parser.add_argument("--api-url", default="http://localhost:8000", help="LaneSwap API URL")
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger('laneswap').setLevel(logging.DEBUG)
        logging.getLogger('progress_service').setLevel(logging.DEBUG)
    
    # Create a client with automatic heartbeats
    async with LaneswapAsyncClient(
        api_url=args.api_url,
        service_name="Progress Example Service",
        auto_heartbeat=True
    ) as client:
        # Set metadata
        client.set_metadata({
            "version": "1.0.0",
            "type": "example"
        })
        
        # Create a data processor
        processor = DataProcessor(client)
        
        # Generate some test data
        test_data = [
            {"id": f"item-{i}", "value": random.randint(1, 100)}
            for i in range(20)
        ]
        
        # Process the data
        try:
            logger.info("Starting data processing")
            result = await processor.process_data(test_data)
            logger.info(f"Processing completed: {len(result)} items processed")
        except Exception as e:
            logger.error(f"Processing failed: {str(e)}")
            await client.send_heartbeat(
                status=HeartbeatStatus.ERROR,
                message=f"Processing failed: {str(e)}"
            )
        
        # Wait a bit before exiting
        logger.info("Service will exit in 5 seconds...")
        await asyncio.sleep(5)

        # Generate the correct monitor URL and ensure the monitor is running
        monitor_url = await client.get_monitor_url(start_if_needed=True)
        logger.info(f"Monitor URL: {monitor_url}")

if __name__ == "__main__":
    asyncio.run(main()) 