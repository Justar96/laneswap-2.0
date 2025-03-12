#!/usr/bin/env python
"""
Test script to verify that circular imports are resolved.
"""

import logging
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_imports")

async def main():
    """Test imports."""
    logger.info("Testing imports...")
    
    # Import types first
    from laneswap.core.types import HeartbeatStatus, ProgressStatus
    logger.info("Types imported successfully")
    
    # Import core modules
    from laneswap.core.heartbeat import HeartbeatManager, get_manager
    logger.info("Heartbeat module imported successfully")
    
    from laneswap.core.progress import ProgressTracker, get_tracker
    logger.info("Progress module imported successfully")
    
    # Test creating instances
    heartbeat_manager = get_manager()
    progress_tracker = get_tracker()
    
    logger.info("HeartbeatManager: %s", heartbeat_manager)
    logger.info("ProgressTracker: %s", progress_tracker)
    
    logger.info("All imports successful!")

if __name__ == "__main__":
    asyncio.run(main()) 