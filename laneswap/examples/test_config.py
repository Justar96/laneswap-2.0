"""
Test script for the LaneSwap configuration module.
This script verifies that the configuration is loaded correctly.
"""

import os
import sys
from pathlib import Path

def test_config():
    """Test the configuration module."""
    try:
        from laneswap.core.config import (
            API_URL, MONITOR_URL, HOST, PORT, DEBUG, 
            MONGODB_URL, MONGODB_DATABASE,
            HEARTBEAT_CHECK_INTERVAL, HEARTBEAT_STALE_THRESHOLD,
            get_config
        )
        
        print("Configuration values:")
        print(f"API_URL: {API_URL}")
        print(f"MONITOR_URL: {MONITOR_URL}")
        print(f"HOST: {HOST}")
        print(f"PORT: {PORT}")
        print(f"DEBUG: {DEBUG}")
        print(f"MONGODB_URL: {MONGODB_URL}")
        print(f"MONGODB_DATABASE: {MONGODB_DATABASE}")
        print(f"HEARTBEAT_CHECK_INTERVAL: {HEARTBEAT_CHECK_INTERVAL}")
        print(f"HEARTBEAT_STALE_THRESHOLD: {HEARTBEAT_STALE_THRESHOLD}")
        
        # Test get_config function
        config = get_config()
        if not isinstance(config, dict):
            print("❌ get_config() did not return a dictionary")
            return False
        
        print("\nget_config() returned:")
        for key, value in config.items():
            print(f"  {key}: {value}")
        
        print("\n✅ Configuration module is working correctly")
        return True
    except Exception as e:
        print(f"❌ Error testing configuration module: {str(e)}")
        return False

def main():
    """Run the configuration test."""
    print("Testing LaneSwap configuration module...\n")
    
    success = test_config()
    
    if success:
        print("\n✅ All configuration tests passed!")
        return 0
    else:
        print("\n❌ Configuration tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 