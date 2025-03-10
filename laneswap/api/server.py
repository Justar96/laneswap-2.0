#!/usr/bin/env python
"""
Standalone script to start the LaneSwap API server.
This script ensures the API server is running and accessible.
"""

import os
import sys
import time
import asyncio
import argparse
import webbrowser
import threading
import logging
import uvicorn
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("laneswap.api")

def start_web_monitor(api_url, port=8080, open_browser=True):
    """Start the web monitor in a separate process."""
    try:
        from laneswap.examples.start_monitor import start_monitor
        
        # Start the monitor in a separate thread
        monitor_thread = threading.Thread(
            target=lambda: start_monitor(port, api_url, open_browser),
            daemon=True
        )
        monitor_thread.start()
        
        logger.info(f"Web monitor started on port {port}")
        logger.info(f"You can access it at: http://localhost:{port}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to start web monitor: {str(e)}")
        return False

def start_server(host="0.0.0.0", port=8000, debug=False, start_monitor=True, monitor_port=8080, open_browser=True):
    """
    Start the LaneSwap API server.
    
    Args:
        host: Host to bind the server to
        port: Port to run the server on
        debug: Whether to run in debug mode
        start_monitor: Whether to start the web monitor
        monitor_port: Port to run the web monitor on
        open_browser: Whether to open a browser window
    """
    from laneswap.api.main import app
    
    # Print startup message
    logger.info(f"Starting LaneSwap API server on {host}:{port}")
    
    # Start the web monitor if requested
    if start_monitor:
        api_url = f"http://localhost:{port}"
        monitor_started = start_web_monitor(api_url, monitor_port, open_browser)
        
        if monitor_started:
            logger.info(f"Web monitor available at: http://localhost:{monitor_port}")
        else:
            logger.warning("Web monitor could not be started automatically")
            logger.info(f"You can start it manually with: python -m laneswap.examples.start_monitor --api-url {api_url}")
    
    # Start the API server
    uvicorn.run(app, host=host, port=port, log_level="info")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Start the LaneSwap API server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    parser.add_argument("--no-monitor", action="store_true", help="Don't start the web monitor")
    parser.add_argument("--monitor-port", type=int, default=8080, help="Port to run the web monitor on")
    parser.add_argument("--no-browser", action="store_true", help="Don't open a browser window")
    
    args = parser.parse_args()
    
    start_server(
        host=args.host,
        port=args.port,
        debug=args.debug,
        start_monitor=not args.no_monitor,
        monitor_port=args.monitor_port,
        open_browser=not args.no_browser
    )

if __name__ == "__main__":
    main() 