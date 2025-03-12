#!/usr/bin/env python
"""
Script to run the client integration test.
This script:
1. Starts the API server in a separate process
2. Sets the MongoDB URI environment variable
3. Runs the client integration test
4. Stops the API server
"""

import os
import sys
import time
import subprocess
import argparse
from multiprocessing import Process


def start_api_server():
    """Start the API server in a separate process."""
    print("Starting API server...")
    # Use the module path to start the server
    subprocess.run(
        [sys.executable, "-m", "laneswap.api.main"],
        env=os.environ.copy()
    )


def run_test(mongodb_uri):
    """Run the client integration test."""
    print("Running client integration test...")
    
    # Set the MongoDB URI environment variable
    env = os.environ.copy()
    env["MONGODB_URI"] = mongodb_uri
    
    # Run the test
    result = subprocess.run(
        [
            sys.executable, 
            "-m", 
            "pytest", 
            "tests/integration/test_full_flow.py::test_client_integration", 
            "-v"
        ],
        env=env
    )
    
    return result.returncode


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run the client integration test")
    parser.add_argument(
        "--mongodb-uri", 
        required=True,
        help="MongoDB URI for the test"
    )
    args = parser.parse_args()
    
    # Start the API server in a separate process
    server_process = Process(target=start_api_server)
    server_process.start()
    
    try:
        # Wait for the server to start
        print("Waiting for API server to start...")
        time.sleep(5)
        
        # Run the test
        exit_code = run_test(args.mongodb_uri)
        
        # Exit with the test's exit code
        sys.exit(exit_code)
    finally:
        # Stop the API server
        print("Stopping API server...")
        server_process.terminate()
        server_process.join(timeout=5)
        if server_process.is_alive():
            print("API server did not stop gracefully, killing...")
            server_process.kill()


if __name__ == "__main__":
    main() 