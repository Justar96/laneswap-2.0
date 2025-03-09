#!/usr/bin/env python
"""
Launch script for the LaneSwap Web Monitor.
This script starts a simple HTTP server and opens the web monitor in a browser.
"""

import os
import sys
import webbrowser
import argparse
import http.server
import socketserver
import threading
import time
from pathlib import Path

def get_monitor_dir():
    """Get the directory containing the web monitor files."""
    return Path(__file__).parent.absolute()

def start_server(port):
    """Start a simple HTTP server for the web monitor."""
    os.chdir(get_monitor_dir())
    
    class CustomHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            # Redirect root to index.html
            if self.path == "/" or self.path == "":
                self.path = "/index.html"
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
    
    # Explicitly bind to all interfaces (0.0.0.0) instead of just localhost
    httpd = socketserver.TCPServer(("0.0.0.0", port), CustomHandler)
    
    print(f"Serving web monitor at http://0.0.0.0:{port}")
    print(f"You can access it at: http://localhost:{port} or http://127.0.0.1:{port}")
    httpd.serve_forever()

def start_dashboard(port=8080, api_url="http://localhost:8000", open_browser=True):
    """
    Start the web monitor dashboard.
    
    Args:
        port: Port to run the web monitor on
        api_url: API URL for the backend
        open_browser: Whether to open a browser window
    """
    # Start the HTTP server in a separate thread
    server_thread = threading.Thread(target=start_server, args=(port,), daemon=True)
    server_thread.start()
    
    # Give the server a moment to start
    time.sleep(0.5)
    
    # Open the browser
    if open_browser:
        # Generate the URL with the API parameter
        url = f"http://localhost:{port}/?api={api_url}"
        print(f"Opening web monitor in browser: {url}")
        print(f"To monitor a specific service, use: http://localhost:{port}/?api={api_url}&service=YOUR_SERVICE_ID")
        webbrowser.open(url)
    
    print("Press Ctrl+C to stop the server")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="Launch the LaneSwap Web Monitor")
    parser.add_argument("--port", type=int, default=8080, help="Port for the web server")
    parser.add_argument("--api-url", default="http://localhost:8000", help="URL of the LaneSwap API")
    parser.add_argument("--no-browser", action="store_true", help="Don't open a browser window")
    
    args = parser.parse_args()
    
    start_dashboard(
        port=args.port,
        api_url=args.api_url,
        open_browser=not args.no_browser
    )

if __name__ == "__main__":
    main() 