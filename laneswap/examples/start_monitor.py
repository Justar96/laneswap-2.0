#!/usr/bin/env python
"""
Standalone script to start the LaneSwap web monitor.
This script ensures the web monitor is running and accessible.
"""

import os
import sys
import time
import argparse
import subprocess
import threading
import logging
import socket
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("laneswap.monitor")

def is_port_in_use(port):
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def wait_for_server(port, timeout=10):
    """Wait for the server to start listening on the specified port."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_port_in_use(port):
            return True
        time.sleep(0.5)
    return False

def start_monitor(port=8080, api_url="http://localhost:8000", open_browser=True):
    """
    Start the web monitor on the specified port.
    
    Args:
        port: Port to run the web monitor on
        api_url: API URL for the backend
        open_browser: Whether to open a browser window
    """
    # Check if the port is already in use
    if is_port_in_use(port):
        logger.info(f"Port {port} is already in use. The web monitor might already be running.")
        return True
    
    # Get the path to the web monitor directory
    try:
        from laneswap.examples.web_monitor.launch import start_dashboard
        logger.info(f"Starting web monitor on port {port}...")
        logger.info(f"API URL: {api_url}")
        
        # Print network interfaces for debugging
        try:
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            logger.info(f"Hostname: {hostname}")
            logger.info(f"Local IP: {local_ip}")
            logger.info(f"You can access the monitor at: http://{local_ip}:{port}")
        except Exception as e:
            logger.warning(f"Could not determine local IP: {e}")
        
        # Start the dashboard in a separate thread
        thread = threading.Thread(
            target=start_dashboard,
            args=(port, api_url, open_browser),
            daemon=True
        )
        thread.start()
        
        # Wait for the server to start
        if wait_for_server(port):
            logger.info(f"Web monitor started successfully on port {port}")
            logger.info(f"You can access it at: http://localhost:{port}")
            return True
        else:
            logger.error(f"Failed to start web monitor on port {port}")
            return False
    except ImportError as e:
        logger.error(f"Failed to import start_dashboard: {e}")
        logger.error("Make sure LaneSwap is installed correctly.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error starting monitor: {e}")
        return False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Start the LaneSwap web monitor")
    parser.add_argument("--port", type=int, default=8080, help="Port to run the web monitor on")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API URL")
    parser.add_argument("--no-browser", action="store_true", help="Don't open a browser window")
    
    args = parser.parse_args()
    
    success = start_monitor(
        port=args.port,
        api_url=args.api_url,
        open_browser=not args.no_browser
    )
    
    if success:
        # Keep the script running to maintain the server
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main() 