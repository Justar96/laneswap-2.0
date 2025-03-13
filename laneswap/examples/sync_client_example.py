#!/usr/bin/env python
"""
Example of using the synchronous LaneSwap client.

This example demonstrates how to use the synchronous client in a
traditional Python application without async/await.
"""

import time
import random
import logging
from datetime import datetime

from laneswap.client.sync_client import LaneswapSyncClient
from laneswap.core.types import HeartbeatStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("sync-client-example")


def main():
    """Main entry point for the example."""
    logger.info("Starting synchronous client example")
    
    # Create the client
    client = LaneswapSyncClient(
        api_url="http://localhost:8000",
        service_name="Sync Client Example",
        auto_heartbeat=True,  # Enable automatic heartbeats
        heartbeat_interval=30  # Send heartbeats every 30 seconds
    )
    
    try:
        # Connect to the API
        logger.info("Connecting to API...")
        service_id = client.connect()
        logger.info(f"Connected with service ID: {service_id}")
        
        # Simulate a long-running process with progress tracking
        total_items = 20
        logger.info(f"Starting to process {total_items} items")
        
        # Start a progress task
        task_id = client.start_progress(
            task_name="Data Processing",
            total_steps=total_items,
            description="Processing sample data"
        )
        logger.info(f"Created progress task with ID: {task_id}")
        
        # Process items
        for i in range(total_items):
            # Simulate processing an item
            logger.info(f"Processing item {i+1}/{total_items}")
            process_time = random.uniform(0.5, 2.0)
            time.sleep(process_time)
            
            # Update progress
            client.update_progress(
                task_id=task_id,
                current_step=i+1,
                status="running",
                message=f"Processing item {i+1}/{total_items}",
                metadata={
                    "item_number": i+1,
                    "process_time": process_time,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Simulate occasional warnings or errors
            if random.random() < 0.2:  # 20% chance
                if random.random() < 0.5:  # 50% of those are warnings
                    logger.warning("Processing slower than expected")
                    client.send_heartbeat(
                        status=HeartbeatStatus.WARNING,
                        message="Processing slower than expected",
                        metadata={"process_time": process_time}
                    )
                else:
                    logger.error("Error processing item")
                    client.send_heartbeat(
                        status=HeartbeatStatus.ERROR,
                        message=f"Error processing item {i+1}",
                        metadata={"item_number": i+1}
                    )
        
        # Complete the progress task
        client.complete_progress(
            task_id=task_id,
            status="completed",
            message="All items processed successfully"
        )
        logger.info("Completed processing all items")
        
        # Send a final heartbeat
        client.send_heartbeat(
            status=HeartbeatStatus.HEALTHY,
            message="Example completed successfully",
            metadata={"completed_at": datetime.now().isoformat()}
        )
        
    except Exception as e:
        logger.error(f"Error in example: {str(e)}")
        
        # Send error heartbeat
        try:
            client.send_heartbeat(
                status=HeartbeatStatus.ERROR,
                message=f"Example failed: {str(e)}",
                metadata={"error": str(e)}
            )
        except Exception:
            pass
        
        raise
    finally:
        # Close the client
        logger.info("Closing client")
        client.close()
        logger.info("Client closed")


def using_context_manager():
    """Example using the context manager."""
    logger.info("Starting example with context manager")
    
    # Use the client as a context manager
    with LaneswapSyncClient(
        api_url="http://localhost:8000",
        service_name="Sync Context Manager Example",
        auto_heartbeat=True
    ) as client:
        logger.info(f"Connected with service ID: {client.service_id}")
        
        # Do some work
        for i in range(5):
            logger.info(f"Working... {i+1}/5")
            time.sleep(1)
            
            # Send custom heartbeats
            client.send_heartbeat(
                status=HeartbeatStatus.HEALTHY,
                message=f"Work in progress: {i+1}/5",
                metadata={"progress": (i+1)/5}
            )
    
    logger.info("Context manager example completed")


if __name__ == "__main__":
    try:
        # Run the main example
        main()
        
        # Run the context manager example
        using_context_manager()
        
        logger.info("All examples completed successfully")
    except Exception as e:
        logger.error(f"Example failed: {str(e)}", exc_info=True)
        exit(1) 