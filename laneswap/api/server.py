#!/usr/bin/env python
"""
Standalone script to start the LaneSwap API server.
This script ensures the API server is running and accessible (web monitor removed).
"""

import argparse
import asyncio
import logging

import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("laneswap.api")

def start_server(host="0.0.0.0", port=8000, debug=False):
    """
    Start the LaneSwap API server.
    Args:
        host: Host to bind the server to
        port: Port to run the server on
        debug: Whether to run in debug mode (enables reload & debug logs)
    """
    from laneswap.api.main import app

    # Print startup message
    logger.info("Starting LaneSwap API server on %s:%s (debug=%s)", host, port, debug)

    # Start the API server with optional reload
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="debug" if debug else "info",
        reload=debug
    )

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Start the LaneSwap API server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")

    args = parser.parse_args()

    start_server(
        host=args.host,
        port=args.port,
        debug=args.debug
    )

if __name__ == "__main__":
    main()
