#!/usr/bin/env python
"""
Example script demonstrating how to use LaneSwap's configuration system.

This script shows how to:
1. Configure LaneSwap programmatically without using .env files
2. Start the API server with custom configuration
3. Register a service and send heartbeats
"""

import argparse
import asyncio
import logging
import sys
import threading
import time
from datetime import datetime
from typing import Any

import requests
import uvicorn

from laneswap.api.main import configure_api
from laneswap.client.async_client import LaneswapAsyncClient
from laneswap.core.config import configure, get_config
from laneswap.core.types import HeartbeatStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("config_example")


def start_api_server(port: int = 8000, host: str = "127.0.0.1"):
    """
    Start the API server with custom configuration.

    Args:
        port: Port to run the API server on
        host: Host to bind the API server to
    """
    # Configure the API with custom settings
    custom_config = {
        "HOST": host,
        "PORT": port,
        "DEBUG": True,
        "LOG_LEVEL": "DEBUG",
        "API_URL": f"http://{host}:{port}",
        "MONITOR_URL": f"http://{host}:8080"
    }

    # Apply the configuration
    app = configure_api(custom_config)

    # Start the API server
    uvicorn.run(app, host=host, port=port)


async def test_client(api_url: str):
    """
    Test the LaneSwap client with the configured API.

    Args:
        api_url: URL of the API server
    """
    # Create the client
    client = LaneswapAsyncClient(
        api_url=api_url,
        service_name="Config Example Service"
    )

    try:
        # Connect to the API
        await client.connect()
        logger.info("Connected to API at %s", api_url)

        # Get the service ID
        service_id = client.service_id
        logger.info("Service ID: %s", service_id)

        # Send heartbeats with different statuses
        statuses = [
            HeartbeatStatus.HEALTHY,
            HeartbeatStatus.WARNING,
            HeartbeatStatus.ERROR,
            HeartbeatStatus.HEALTHY
        ]
        messages = [
            "Service is running normally",
            "High resource usage detected",
            "Service encountered an error",
            "Service has recovered"
        ]

        for status, message in zip(statuses, messages):
            # Send heartbeat
            await client.send_heartbeat(
                status=status,
                message=message,
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "example": True
                }
            )

            logger.info("Sent heartbeat with status: %s", status)

            # Wait a bit before sending the next heartbeat
            await asyncio.sleep(2)

        # Get all services
        services = await client.get_all_services()
        logger.info("Services: %s", services)

        # Close the client session
        await client.close()

    except Exception as e:
        logger.error("Error in client test: %s", str(e))
        if hasattr(client, 'close'):
            await client.close()


async def main_async(api_port: int = 8000, api_host: str = "127.0.0.1"):
    """
    Run the example asynchronously.

    Args:
        api_port: Port for the API server
        api_host: Host for the API server
    """
    # Configure LaneSwap programmatically
    custom_config = {
        "HOST": api_host,
        "PORT": api_port,
        "DEBUG": True,
        "LOG_LEVEL": "DEBUG",
        "API_URL": f"http://{api_host}:{api_port}",
        "MONITOR_URL": f"http://{api_host}:8080",

        # Discord webhook configuration (optional)
        "DISCORD_WEBHOOK_URL": "",  # Add your webhook URL here if you have one
        "DISCORD_WEBHOOK_USERNAME": "LaneSwap Config Example",

        # Heartbeat configuration
        "HEARTBEAT_CHECK_INTERVAL": 15,
        "HEARTBEAT_STALE_THRESHOLD": 30
    }

    # Apply the configuration
    configure(custom_config)

    # Print the current configuration
    logger.info("Current configuration:")
    for key, value in get_config().items():
        logger.info("  %s: %s", key, value)

    # Start the API server in a separate thread
    api_thread = threading.Thread(
        target=start_api_server,
        args=(api_port, api_host),
        daemon=True
    )
    api_thread.start()

    # Wait for the API server to start
    logger.info("Waiting for API server to start at http://%s:%s...", api_host, api_port)
    for _ in range(10):
        try:
            response = requests.get(f"http://{api_host}:{api_port}/api/health")
            if response.status_code == 200:
                logger.info("API server started at http://%s:%s", api_host, api_port)
                break
        except Exception:
            pass
        await asyncio.sleep(1)
    else:
        logger.error("Failed to start API server at http://%s:%s", api_host, api_port)
        return

    # Test the client
    await test_client(f"http://{api_host}:{api_port}")

    # Keep the server running for a bit
    logger.info("Example completed. Press Ctrl+C to exit.")
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Exiting...")


def main():
    """Main entry point for the example."""
    parser = argparse.ArgumentParser(description="LaneSwap Configuration Example")
    parser.add_argument("--port", type=int, default=8000, help="API server port")
    parser.add_argument("--host", default="127.0.0.1", help="API server host")

    args = parser.parse_args()

    try:
        asyncio.run(main_async(args.port, args.host))
    except KeyboardInterrupt:
        logger.info("Example stopped by user")
    except Exception as e:
        logger.error("Error in example: %s", str(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
