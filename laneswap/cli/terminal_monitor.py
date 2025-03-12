"""
Command-line interface for the LaneSwap terminal monitor.

This module provides a CLI entry point for launching the terminal-based
service monitor.
"""

import argparse
import asyncio
import sys
from typing import List, Optional

from ..terminal import start_monitor
from ..core.config import get_config


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the terminal monitor CLI.
    
    Args:
        args: Command line arguments (defaults to sys.argv if None)
        
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = argparse.ArgumentParser(
        description="LaneSwap Terminal Monitor - A terminal-based UI for monitoring services"
    )
    
    parser.add_argument(
        "--api-url", "-a",
        type=str,
        help="URL of the LaneSwap API server (default: from config or http://localhost:8000)"
    )
    
    parser.add_argument(
        "--refresh", "-r",
        type=float,
        default=2.0,
        help="Refresh interval in seconds (default: 2.0)"
    )
    
    parser.add_argument(
        "--config", "-c",
        type=str,
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--service-name", "-s",
        type=str,
        default="terminal-monitor",
        help="Service name for the terminal monitor (default: terminal-monitor)"
    )
    
    parser.add_argument(
        "--no-terminal", "-n",
        action="store_true",
        help="Run in non-terminal mode (logging only, no UI)"
    )
    
    parser.add_argument(
        "--force-terminal", "-f",
        action="store_true",
        help="Force terminal mode even if no terminal is detected"
    )
    
    parser.add_argument(
        "--paused", "-p",
        action="store_true",
        help="Start the monitor in paused mode (no auto-refresh)"
    )
    
    parsed_args = parser.parse_args(args)
    
    # Load configuration
    config = get_config(parsed_args.config) if parsed_args.config else get_config()
    
    # Determine API URL (command line > config > default)
    api_url = parsed_args.api_url or config.get("api_url") or "http://localhost:8000"
    
    # Determine terminal mode
    use_terminal = None  # Auto-detect by default
    if parsed_args.no_terminal:
        use_terminal = False
    elif parsed_args.force_terminal:
        use_terminal = True
    
    try:
        # Create client
        from laneswap.client.async_client import LaneswapAsyncClient
        client = LaneswapAsyncClient(
            api_url=api_url,
            service_name=parsed_args.service_name
        )
        
        # Create and start monitor
        from laneswap.terminal.monitor import TerminalMonitor
        monitor = TerminalMonitor(
            client=client,
            refresh_interval=parsed_args.refresh,
            use_terminal=use_terminal
        )
        
        # Set initial paused state if requested
        if parsed_args.paused:
            monitor.paused = True
            
        # Run the monitor
        asyncio.run(monitor.start())
        return 0
    except KeyboardInterrupt:
        print("\nMonitor stopped by user.")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main()) 