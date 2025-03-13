#!/usr/bin/env python
"""
LaneSwap Terminal Monitor Example

This script demonstrates how to use the LaneSwap terminal monitor
to display real-time service status information.

Usage:
    python -m laneswap.examples.terminal_monitor_example --api-url http://localhost:8000
    python -m laneswap.examples.terminal_monitor_example --api-url http://localhost:8000 --no-terminal
"""

import argparse
import asyncio
import logging
import sys
import traceback
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_terminal_monitor(api_url: str, refresh_interval: Optional[float] =
    2.0, use_terminal: Optional[bool] = None, start_paused: bool = False):
    """
    Run the terminal monitor with the specified API URL.

    Args:
        api_url: URL of the LaneSwap API server
        refresh_interval: How often to refresh the display (in seconds)
        use_terminal: Whether to use terminal UI (auto-detect if None)
        start_paused: Whether to start the monitor in paused mode
    """
    try:
        from laneswap.client.async_client import LaneswapAsyncClient
        from laneswap.terminal.monitor import TerminalMonitor

        logger.info("Starting terminal monitor with API URL: %s", api_url)

        # Create client and monitor
        # For the monitor, we don't need to send heartbeats, just read service data
        client = LaneswapAsyncClient(
            api_url=api_url,
            service_name="terminal-monitor"  # Adding service_name parameter
        )

        logger.debug("Client created successfully")

        # Test API connection
        try:
            logger.debug("Testing API connection...")
            services = await client.get_all_services()
            logger.debug(f"API connection successful. Found {len(services.get('services', {}))} services")
        except Exception as e:
            logger.error("Failed to connect to API: %s", e)
            logger.debug(traceback.format_exc())
            sys.exit(1)

        # Create and start monitor
        logger.debug("Creating terminal monitor...")
        monitor = TerminalMonitor(client, refresh_interval=refresh_interval, use_terminal=use_terminal)

        # Set initial paused state if requested
        if start_paused:
            monitor.paused = True
            logger.info("Starting monitor in paused mode (no auto-refresh)")

        logger.debug("Starting terminal monitor...")
        await monitor.start()

    except ImportError as e:
        logger.error("Failed to import required modules: %s", e)
        logger.debug(traceback.format_exc())
        sys.exit(1)
    except Exception as e:
        logger.error("Error running terminal monitor: %s", e)
        logger.debug(traceback.format_exc())
        sys.exit(1)

def main():
    """Parse arguments and run the terminal monitor."""
    parser = argparse.ArgumentParser(description="LaneSwap Terminal Monitor Example")
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000",
        help="URL of the LaneSwap API server"
    )
    parser.add_argument(
        "--refresh",
        type=float,
        default=2.0,
        help="Refresh interval in seconds"
    )
    parser.add_argument(
        "--no-terminal",
        action="store_true",
        help="Run in non-terminal mode (logging only, no UI)"
    )
    parser.add_argument(
        "--force-terminal",
        action="store_true",
        help="Force terminal mode even if no terminal is detected"
    )
    parser.add_argument(
        "--paused", "-p",
        action="store_true",
        help="Start the monitor in paused mode (no auto-refresh)"
    )

    args = parser.parse_args()

    # Determine terminal mode
    use_terminal = None  # Auto-detect by default
    if args.no_terminal:
        use_terminal = False
    elif args.force_terminal:
        use_terminal = True

    try:
        asyncio.run(run_terminal_monitor(args.api_url, args.refresh, use_terminal, args.paused))
    except KeyboardInterrupt:
        print("\nTerminal monitor stopped by user.")
        sys.exit(0)

if __name__ == "__main__":
    main()
