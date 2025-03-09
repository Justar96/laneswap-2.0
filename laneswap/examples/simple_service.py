import asyncio
import random
import logging
from datetime import datetime

import aiohttp
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("example-service")


async def register_service(api_url: str, service_name: str) -> str:
    """
    Register the service with the Laneswap API.
    
    Args:
        api_url: Laneswap API URL
        service_name: Name of the service
        
    Returns:
        str: Service ID
    """
    logger.info(f"Registering service: {service_name}")
    
    registration_data = {
        "service_name": service_name,
        "metadata": {
            "version": "1.0.0",
            "started_at": datetime.utcnow().isoformat(),
            "environment": "development"
        }
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{api_url}/api/services",
            json=registration_data
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(f"Failed to register service: {error_text}")
                
            response_data = await response.json()
            service_id = response_data.get("service_id")
            
            if not service_id:
                raise ValueError("No service_id in response")
                
            logger.info(f"Service registered with ID: {service_id}")
            return service_id


async def send_heartbeat(
    api_url: str,
    service_id: str,
    status: str = "healthy",
    message: str = None
) -> None:
    """
    Send a heartbeat to the Laneswap API.
    
    Args:
        api_url: Laneswap API URL
        service_id: Service ID
        status: Heartbeat status
        message: Optional message
    """
    heartbeat_data = {
        "status": status,
        "message": message,
        "metadata": {
            "memory_usage_mb": random.randint(50, 200),
            "cpu_usage_percent": random.randint(1, 95),
            "active_connections": random.randint(1, 100)
        }
    }
    
    logger.debug(f"Sending heartbeat for service {service_id}: {status}")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{api_url}/api/services/{service_id}/heartbeat",
            json=heartbeat_data
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"Failed to send heartbeat: {error_text}")
            else:
                logger.debug("Heartbeat sent successfully")


async def simulate_service(api_url: str, service_name: str, heartbeat_interval: int = 10):
    """
    Simulate a service with periodic heartbeats.
    
    Args:
        api_url: Laneswap API URL
        service_name: Name of the service
        heartbeat_interval: Interval in seconds between heartbeats
    """
    # Register the service
    service_id = await register_service(api_url, service_name)
    
    # Simulation states
    states = ["healthy", "healthy", "healthy", "healthy", "degraded", "error"]
    operation_count = 0
    error_count = 0
    
    # Main service loop
    while True:
        try:
            operation_count += 1
            
            # Randomly choose a status
            status = random.choice(states)
            message = None
            
            if status == "healthy":
                message = f"Service running normally. Processed {operation_count} operations."
            elif status == "degraded":
                message = f"Service experiencing slowdowns. Response time increased."
            elif status == "error":
                error_count += 1
                message = f"Error occurred in operation. Total errors: {error_count}"
                
            # Send heartbeat
            await send_heartbeat(api_url, service_id, status, message)
            
            # Random work simulation with potential failure
            if random.random() < 0.05:  # 5% chance of failure
                logger.warning("Simulating a service error...")
                await asyncio.sleep(random.randint(1, 3))
                if random.random() < 0.5:  # 50% chance of recovery
                    logger.info("Service recovered from error")
                else:
                    logger.error("Service failed to recover")
            
            # Wait for next heartbeat
            await asyncio.sleep(heartbeat_interval)
            
        except Exception as e:
            logger.error(f"Error in service simulation: {str(e)}")
            await asyncio.sleep(5)  # Wait before retry


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Laneswap Example Service")
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="Laneswap API URL"
    )
    parser.add_argument(
        "--service-name",
        default=f"example-service-{random.randint(1000, 9999)}",
        help="Service name"
    )
    parser.add_argument(
        "--heartbeat-interval",
        type=int,
        default=10,
        help="Heartbeat interval in seconds"
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting example service: {args.service_name}")
    logger.info(f"Laneswap API URL: {args.api_url}")
    logger.info(f"Heartbeat interval: {args.heartbeat_interval} seconds")
    
    try:
        await simulate_service(
            api_url=args.api_url,
            service_name=args.service_name,
            heartbeat_interval=args.heartbeat_interval
        )
    except KeyboardInterrupt:
        logger.info("Service shutting down...")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())