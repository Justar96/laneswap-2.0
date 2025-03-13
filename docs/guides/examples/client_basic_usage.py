#!/usr/bin/env python3
"""
Basic LaneSwap Client Usage Example

This example demonstrates how to initialize and use the LaneSwap client
to interact with a LaneSwap network.
"""

import asyncio
import logging
from laneswap.client import LaneSwapClient
from laneswap.core.models import ServiceConfig, ServiceType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("laneswap-client-example")

async def main():
    # Initialize the LaneSwap client
    client = LaneSwapClient(
        api_url="http://localhost:8000",
        api_key="your-api-key",  # Replace with your actual API key
        service_name="example-client",
        service_type=ServiceType.CLIENT
    )
    
    # Connect to the LaneSwap network
    await client.connect()
    logger.info("Connected to LaneSwap network")
    
    try:
        # Register a new service
        service_config = ServiceConfig(
            name="my-custom-service",
            type=ServiceType.ADAPTER,
            description="A custom adapter service for demonstration",
            config={
                "adapter_type": "custom",
                "connection_string": "custom://localhost:9000"
            }
        )
        
        service_id = await client.register_service(service_config)
        logger.info(f"Registered new service with ID: {service_id}")
        
        # Get all available services
        services = await client.get_services()
        logger.info(f"Found {len(services)} services in the network:")
        for service in services:
            logger.info(f"  - {service.name} ({service.type}): {service.status}")
        
        # Send a message to a specific service
        target_service_id = services[0].id if services else service_id
        message = {
            "action": "ping",
            "timestamp": "2023-09-01T12:00:00Z"
        }
        
        response = await client.send_message(target_service_id, message)
        logger.info(f"Received response: {response}")
        
        # Subscribe to events from a service
        async def event_handler(event):
            logger.info(f"Received event: {event}")
        
        await client.subscribe(target_service_id, event_handler)
        logger.info(f"Subscribed to events from service {target_service_id}")
        
        # Wait for some events (in a real application, this would be part of your main loop)
        await asyncio.sleep(10)
        
        # Unsubscribe from events
        await client.unsubscribe(target_service_id)
        logger.info(f"Unsubscribed from events for service {target_service_id}")
        
        # Deregister the service we created
        await client.deregister_service(service_id)
        logger.info(f"Deregistered service {service_id}")
        
    except Exception as e:
        logger.error(f"Error during client operations: {e}")
    
    finally:
        # Disconnect from the LaneSwap network
        await client.disconnect()
        logger.info("Disconnected from LaneSwap network")

if __name__ == "__main__":
    asyncio.run(main()) 