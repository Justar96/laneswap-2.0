#!/usr/bin/env python
"""
Standalone script to start the LaneSwap terminal monitor.
This script provides a convenient way to launch the terminal-based monitor.
"""

import sys
import argparse
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("laneswap.monitor")

async def start_terminal_monitor(api_url="http://localhost:8000", refresh_interval=2.0):
    """
    Start the terminal monitor.
    
    Args:
        api_url: API URL for the backend
        refresh_interval: How often to refresh the display (in seconds)
    """
    try:
        from laneswap.terminal import start_monitor
        
        logger.info(f"Starting terminal monitor...")
        logger.info(f"API URL: {api_url}")
        logger.info(f"Refresh interval: {refresh_interval} seconds")
        logger.info("Press Ctrl+C to exit")
        
        # Start the terminal monitor
        await start_monitor(api_url, refresh_interval)
        return True
    except ImportError as e:
        logger.error(f"Failed to import terminal monitor: {e}")
        logger.error("Make sure LaneSwap is installed correctly.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error starting monitor: {e}")
        return False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Start the LaneSwap terminal monitor")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API URL")
    parser.add_argument("--refresh", type=float, default=2.0, help="Refresh interval in seconds")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(start_terminal_monitor(
            api_url=args.api_url,
            refresh_interval=args.refresh
        ))
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 