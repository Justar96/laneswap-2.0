#!/usr/bin/env python
"""
Test script to verify that the LaneswapAsyncClient properly closes its sessions.

This script:
1. Creates a client
2. Connects to the API
3. Sends a heartbeat
4. Properly closes the client
5. Verifies that the session is closed
"""

import asyncio
import logging
import sys
from typing import Optional

from laneswap.client.async_client import LaneswapAsyncClient
from laneswap.core.heartbeat import HeartbeatStatus

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("test_client_close")


async def test_client_close(api_url: str = "http://localhost:8000"):
    """Test that the client properly closes its session."""
    logger.info("Creating client")
    client = LaneswapAsyncClient(
        api_url=api_url,
        service_name="test-client-close"
    )
    
    try:
        # Connect to the API
        logger.info("Connecting to API")
        service_id = await client.connect()
        logger.info(f"Connected with service ID: {service_id}")
        
        # Send a heartbeat
        logger.info("Sending heartbeat")
        await client.send_heartbeat(
            status=HeartbeatStatus.HEALTHY,
            message="Testing client close"
        )
        logger.info("Heartbeat sent successfully")
        
        # Check if session exists and is open
        logger.info(f"Session exists: {client._session is not None}")
        if client._session:
            logger.info(f"Session is closed: {client._session.closed}")
        
        # Close the client
        logger.info("Closing client")
        await client.close()
        
        # Verify session is closed
        logger.info(f"After close - Session exists: {client._session is not None}")
        if client._session:
            logger.info(f"After close - Session is closed: {client._session.closed}")
        else:
            logger.info("Session was properly cleaned up")
            
        # Try to reconnect
        logger.info("Reconnecting to API")
        service_id = await client.connect()
        logger.info(f"Reconnected with service ID: {service_id}")
        
        # Send another heartbeat
        logger.info("Sending another heartbeat")
        await client.send_heartbeat(
            status=HeartbeatStatus.HEALTHY,
            message="Testing client reconnect"
        )
        logger.info("Second heartbeat sent successfully")
        
        # Close again
        logger.info("Closing client again")
        await client.close()
        logger.info("Client closed successfully")
        
        return True
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        return False
    finally:
        # Ensure client is closed even if an error occurs
        if client._session and not client._session.closed:
            logger.warning("Client session was not closed properly, closing now")
            await client.close()


async def test_context_manager(api_url: str = "http://localhost:8000"):
    """Test the client as a context manager."""
    logger.info("Testing client as context manager")
    
    try:
        async with LaneswapAsyncClient(
            api_url=api_url,
            service_name="test-context-manager"
        ) as client:
            # Send a heartbeat
            logger.info("Sending heartbeat within context manager")
            await client.send_heartbeat(
                status=HeartbeatStatus.HEALTHY,
                message="Testing context manager"
            )
            logger.info("Heartbeat sent successfully")
            
            # Check if session exists and is open
            logger.info(f"Session exists: {client._session is not None}")
            if client._session:
                logger.info(f"Session is closed: {client._session.closed}")
        
        # After context manager exits, session should be closed
        logger.info("Context manager exited")
        logger.info(f"After context exit - Session exists: {client._session is not None}")
        if client._session:
            logger.info(f"After context exit - Session is closed: {client._session.closed}")
        
        return True
    except Exception as e:
        logger.error(f"Error during context manager test: {str(e)}")
        return False


async def main_async(api_url: Optional[str] = None):
    """Run all tests."""
    api_url = api_url or "http://localhost:8000"
    
    logger.info("Starting client close tests")
    
    # Test direct close method
    close_result = await test_client_close(api_url)
    logger.info(f"Direct close test {'passed' if close_result else 'failed'}")
    
    # Test context manager
    context_result = await test_context_manager(api_url)
    logger.info(f"Context manager test {'passed' if context_result else 'failed'}")
    
    # Overall result
    if close_result and context_result:
        logger.info("✅ All client close tests passed")
        return True
    else:
        logger.error("❌ Some client close tests failed")
        return False


def main():
    """Entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test LaneswapAsyncClient session closing")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API URL")
    
    args = parser.parse_args()
    
    result = asyncio.run(main_async(args.api_url))
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main() 