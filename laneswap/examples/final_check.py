#!/usr/bin/env python
"""
Final system check for LaneSwap.
This script verifies that all components of the system are working correctly.
"""

import os
import sys
import time
import asyncio
import argparse
from pathlib import Path

def print_header(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

async def run_all_tests():
    """Run all tests and return the results."""
    from laneswap.examples.test_all import main as test_all_main
    
    print_header("Running All Tests")
    
    # Run the test_all script
    result = test_all_main()
    
    return result == 0

async def check_web_monitor():
    """Check that the web monitor is working correctly."""
    import requests
    
    print_header("Checking Web Monitor")
    
    try:
        # Try to access the web monitor
        response = requests.get("http://localhost:8080", timeout=2)
        if response.status_code == 200:
            print("✅ Web monitor is accessible")
            return True
        else:
            print(f"❌ Web monitor returned status code {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing web monitor: {str(e)}")
        return False

async def check_api():
    """Check that the API is working correctly."""
    import requests
    
    print_header("Checking API")
    
    try:
        # Try to access the API health endpoint
        response = requests.get("http://localhost:8000/api/health", timeout=2)
        if response.status_code == 200:
            print("✅ API is accessible")
            return True
        else:
            print(f"❌ API returned status code {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing API: {str(e)}")
        return False

async def main():
    """Run the final system check."""
    print_header("Final System Check")
    
    # Run all tests
    tests_ok = await run_all_tests()
    
    # Check web monitor
    web_monitor_ok = await check_web_monitor()
    
    # Check API
    api_ok = await check_api()
    
    # Print summary
    print_header("Final Check Summary")
    print(f"Tests: {'✅' if tests_ok else '❌'}")
    print(f"Web Monitor: {'✅' if web_monitor_ok else '❌'}")
    print(f"API: {'✅' if api_ok else '❌'}")
    
    # Overall result
    all_ok = tests_ok and web_monitor_ok and api_ok
    
    print_header("Final Result")
    if all_ok:
        print("✅ All checks passed! LaneSwap is ready to use.")
    else:
        print("❌ Some checks failed. Please fix the issues before using LaneSwap.")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 