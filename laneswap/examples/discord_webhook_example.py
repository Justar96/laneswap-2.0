#!/usr/bin/env python
"""
Example script demonstrating LaneSwap's Discord webhook integration.

This script shows how to:
1. Register a service
2. Configure a Discord webhook for the service
3. Send heartbeats with different statuses
4. Receive Discord notifications when service status changes
"""

import asyncio
import argparse
import logging
import json
import sys
import time
from datetime import datetime

from laneswap.core.heartbeat import (
    HeartbeatStatus, register_service, send_heartbeat, 
    get_service, initialize
)
from laneswap.adapters.discord import DiscordWebhookAdapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("discord_example")


async def main(webhook_url: str, service_name: str, cycle_count: int = 5):
    """
    Run the Discord webhook example.
    
    Args:
        webhook_url: Discord webhook URL
        service_name: Name for the test service
        cycle_count: Number of status cycles to run
    """
    # Initialize the Discord adapter
    discord_adapter = DiscordWebhookAdapter(webhook_url=webhook_url)
    
    # Initialize the heartbeat system with the Discord adapter
    await initialize(notifiers=[discord_adapter])
    
    # Register a service
    service_id = await register_service(
        service_name=service_name,
        metadata={
            "version": "1.0.0",
            "environment": "example",
            "timestamp": datetime.now().isoformat()
        }
    )
    
    logger.info(f"Registered service: {service_name} (ID: {service_id})")
    
    # Configure service-specific webhook (optional)
    discord_adapter.register_service_webhook(
        service_id=service_id,
        webhook_url=webhook_url,
        notification_levels=["info", "warning", "error"]
    )
    
    logger.info(f"Configured Discord webhook for service {service_id}")
    
    # Send initial heartbeat
    await send_heartbeat(
        service_id=service_id,
        status=HeartbeatStatus.HEALTHY,
        message="Service started"
    )
    
    logger.info("Sent initial heartbeat with HEALTHY status")
    
    # Cycle through different statuses
    statuses = [
        (HeartbeatStatus.HEALTHY, "Service is running normally"),
        (HeartbeatStatus.WARNING, "High resource usage detected"),
        (HeartbeatStatus.ERROR, "Service encountered an error"),
        (HeartbeatStatus.WARNING, "Service recovering from error"),
        (HeartbeatStatus.HEALTHY, "Service has recovered")
    ]
    
    # Run through the status cycle multiple times
    for cycle in range(cycle_count):
        logger.info(f"Starting status cycle {cycle + 1}/{cycle_count}")
        
        for status, message in statuses:
            # Wait a bit before changing status
            await asyncio.sleep(5)
            
            # Send heartbeat with new status
            await send_heartbeat(
                service_id=service_id,
                status=status,
                message=message,
                metadata={
                    "cycle": cycle + 1,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            status_name = status.value
            logger.info(f"Sent heartbeat with {status_name} status: {message}")
    
    # Send final heartbeat
    await send_heartbeat(
        service_id=service_id,
        status=HeartbeatStatus.HEALTHY,
        message="Example completed successfully"
    )
    
    logger.info("Discord webhook example completed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LaneSwap Discord Webhook Example")
    parser.add_argument("--webhook-url", required=True, help="Discord webhook URL")
    parser.add_argument("--service-name", default="Discord Example Service", help="Service name")
    parser.add_argument("--cycles", type=int, default=2, help="Number of status cycles to run")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(main(args.webhook_url, args.service_name, args.cycles))
    except KeyboardInterrupt:
        logger.info("Example stopped by user")
    except Exception as e:
        logger.error(f"Error in example: {str(e)}")
        sys.exit(1) 