#!/usr/bin/env python
"""
Simple test script for the LaneSwap heartbeat system.
"""

import asyncio
import logging
from laneswap.core.heartbeat import HeartbeatManager, HeartbeatStatus

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("test_heartbeat")

async def main():
    # Create a heartbeat manager
    logger.info("Creating heartbeat manager")
    manager = HeartbeatManager()
    
    # Register a service
    logger.info("Registering service")
    service_id = await manager.register_service(
        service_name="Test Service",
        metadata={"version": "1.0.0"}
    )
    logger.info(f"Service registered with ID: {service_id}")
    
    # Send a heartbeat
    logger.info("Sending heartbeat")
    await manager.send_heartbeat(
        service_id=service_id,
        status=HeartbeatStatus.HEALTHY,
        message="Service running normally"
    )
    
    # Get service status
    logger.info("Getting service status")
    service = await manager.get_service(service_id)
    logger.info(f"Service status: {service}")
    
    # Start the monitor
    logger.info("Starting heartbeat monitor")
    await manager.start_monitor()
    
    # Wait a bit
    logger.info("Waiting...")
    await asyncio.sleep(5)
    
    # Stop the monitor
    logger.info("Stopping heartbeat monitor")
    await manager.stop_monitor()
    
    logger.info("Test completed successfully")

if __name__ == "__main__":
    asyncio.run(main()) 