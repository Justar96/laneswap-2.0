#!/usr/bin/env python
"""
Simple example of a service using LaneSwap for heartbeat monitoring.
"""

import asyncio
import logging
import random
import time
from datetime import datetime

from laneswap.client.async_client import LaneswapAsyncClient
from laneswap.core.heartbeat import HeartbeatStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("simple-service")


async def simulate_service():
    """Simulate a service that sends heartbeats."""
    # Create a client
    client = LaneswapAsyncClient(
        api_url="http://localhost:8000",
        service_name="Simple Example Service",
        auto_heartbeat=True,  # Enable automatic heartbeats
        heartbeat_interval=10  # Send heartbeats every 10 seconds
    )
    
    try:
        # Connect to the API
        logger.info("Connecting to API...")
        await client.connect()
        
        # Register the service
        logger.info("Registering service...")
        service_id = await client.register_service(
            service_name=client.service_name,
            metadata={
                "version": "1.0.0",
                "started_at": datetime.now().isoformat()
            }
        )
        logger.info(f"Service registered with ID: {service_id}")
        
        # Simulate service activity
        for i in range(30):
            # Simulate some work
            work_time = random.uniform(0.5, 2.0)
            logger.info(f"Performing work iteration {i+1}...")
            await asyncio.sleep(work_time)
            
            # Simulate occasional warnings or errors
            status = HeartbeatStatus.HEALTHY
            message = "Service running normally"
            
            if random.random() < 0.2:  # 20% chance of warning
                status = HeartbeatStatus.WARNING
                message = "High resource usage detected"
                logger.warning(message)
            elif random.random() < 0.1:  # 10% chance of error
                status = HeartbeatStatus.ERROR
                message = "Service encountered an error"
                logger.error(message)
            
            # Send a manual heartbeat with the current status
            # This will override the auto heartbeat for this interval
            await client.send_heartbeat(
                status=status,
                message=message,
                metadata={
                    "iteration": i + 1,
                    "work_time": work_time,
                    "timestamp": time.time()
                }
            )
            
            # Wait between iterations
            await asyncio.sleep(random.uniform(3.0, 8.0))
        
        # Final healthy heartbeat
        logger.info("Service completed all work successfully")
        await client.send_heartbeat(
            status=HeartbeatStatus.HEALTHY,
            message="Service completed all work successfully",
            metadata={"completed_at": datetime.now().isoformat()}
        )
    except Exception as e:
        logger.error(f"Service error: {str(e)}")
        # Send error heartbeat
        try:
            await client.send_heartbeat(
                status=HeartbeatStatus.ERROR,
                message=f"Service error: {str(e)}",
                metadata={"error": str(e), "timestamp": time.time()}
            )
        except Exception:
            pass
    finally:
        # Close the client (stops auto heartbeat)
        logger.info("Closing client...")
        await client.close()


if __name__ == "__main__":
    logger.info("Starting simple service example...")
    asyncio.run(simulate_service())
    logger.info("Simple service example completed") 