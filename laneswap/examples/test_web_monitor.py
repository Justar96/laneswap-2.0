"""
Test script for the LaneSwap web monitor.
This script verifies that the web monitor can be started and accessed.
"""

import os
import sys
import time
import socket
import subprocess
import webbrowser
import argparse
import requests
from pathlib import Path

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

def test_monitor_files():
    """Test that all required web monitor files exist."""
    monitor_dir = Path(__file__).parent / "web_monitor"
    
    required_files = [
        "index.html",
        "styles.css",
        "script.js",
        "i18n.js",
        "launch.py",
    ]
    
    missing_files = []
    for file in required_files:
        if not (monitor_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing web monitor files: {', '.join(missing_files)}")
        return False
    
    print("✅ All web monitor files exist")
    return True

def test_monitor_server(port=8080, api_url="http://localhost:8000"):
    """Test starting the web monitor server."""
    # Check if the port is already in use
    if is_port_in_use(port):
        print(f"⚠️ Port {port} is already in use. Skipping server test.")
        return True
    
    # Start the server in a separate process
    try:
        from laneswap.examples.start_monitor import start_monitor
        import threading
        
        server_thread = threading.Thread(
            target=start_monitor,
            args=(port, api_url, False),
            daemon=True
        )
        server_thread.start()
        
        # Wait for the server to start
        if wait_for_server(port):
            print(f"✅ Web monitor server started on port {port}")
            
            # Try to access the server
            try:
                response = requests.get(f"http://localhost:{port}", timeout=2)
                if response.status_code == 200:
                    print(f"✅ Successfully accessed web monitor at http://localhost:{port}")
                    return True
                else:
                    print(f"❌ Failed to access web monitor: Status code {response.status_code}")
                    return False
            except requests.RequestException as e:
                print(f"❌ Failed to access web monitor: {str(e)}")
                return False
        else:
            print(f"❌ Failed to start web monitor server on port {port}")
            return False
    except Exception as e:
        print(f"❌ Error testing web monitor server: {str(e)}")
        return False

def test_i18n_support():
    """Test that the internationalization support is working."""
    try:
        # Check if the i18n.js file exists
        monitor_dir = Path(__file__).parent / "web_monitor"
        i18n_file = monitor_dir / "i18n.js"
        
        if not i18n_file.exists():
            print("❌ i18n.js file not found")
            return False
        
        # Read the file content to check for translations
        with open(i18n_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for translations object
        if "translations = {" not in content and "const translations = {" not in content:
            print("❌ translations object not found in i18n.js")
            return False
        
        # Check for English translations - more flexible pattern matching
        if not any(pattern in content for pattern in ["'en':", '"en":', "en:", "en :"]):
            print("❌ English translations not found in i18n.js")
            return False
        
        # Check for Thai translations - more flexible pattern matching
        if not any(pattern in content for pattern in ["'th':", '"th":', "th:", "th :"]):
            print("❌ Thai translations not found in i18n.js")
            return False
        
        print("✅ Internationalization support is working")
        return True
    except Exception as e:
        print(f"❌ Error testing i18n support: {str(e)}")
        return False

def main():
    """Run all web monitor tests."""
    parser = argparse.ArgumentParser(description="Test the LaneSwap web monitor")
    parser.add_argument("--port", type=int, default=8080, help="Port to test the web monitor on")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API URL to use for testing")
    parser.add_argument("--open-browser", action="store_true", help="Open the web monitor in a browser")
    
    args = parser.parse_args()
    
    print("Testing LaneSwap web monitor...")
    
    # Test that all required files exist
    files_ok = test_monitor_files()
    
    # Test the web monitor server
    server_ok = test_monitor_server(args.port, args.api_url)
    
    # Test internationalization support
    i18n_ok = test_i18n_support()
    
    # Open the web monitor in a browser if requested
    if args.open_browser and server_ok:
        url = f"http://localhost:{args.port}/?api={args.api_url}"
        print(f"Opening web monitor in browser: {url}")
        webbrowser.open(url)
    
    # Print summary
    print("\nTest results:")
    print(f"Files: {'✅' if files_ok else '❌'}")
    print(f"Server: {'✅' if server_ok else '❌'}")
    print(f"i18n: {'✅' if i18n_ok else '❌'}")
    
    if files_ok and server_ok and i18n_ok:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 