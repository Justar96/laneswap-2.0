"""
Command-line interface for LaneSwap.

This module provides a command-line interface for managing LaneSwap
services and monitoring.
"""

import asyncio
import argparse
import logging
import sys
import os
from typing import Dict, Any, Optional, List
import json
from datetime import datetime

import uvicorn
from tabulate import tabulate
import click
import webbrowser
import requests

from ..core.heartbeat import (
    HeartbeatStatus, generate_monitor_url, register_service, 
    send_heartbeat, get_service, get_all_services, initialize
)
from ..client.async_client import LaneswapAsyncClient
from ..core.config import API_URL, MONITOR_URL

logger = logging.getLogger("laneswap.cli")


def setup_logging(log_level: str = "INFO"):
    """Set up logging configuration."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


async def register_service_cmd(args):
    """Register a new service."""
    client = LaneswapAsyncClient(api_url=args.api_url)
    
    try:
        # Parse metadata if provided
        metadata = None
        if args.metadata:
            try:
                metadata = json.loads(args.metadata)
            except json.JSONDecodeError:
                logger.error("Invalid JSON metadata")
                sys.exit(1)
        
        # Register service
        service_id = await client.register_service(
            service_name=args.name,
            service_id=args.id,
            metadata=metadata
        )
        
        print(f"Service registered with ID: {service_id}")
    except Exception as e:
        logger.error(f"Error registering service: {str(e)}")
        sys.exit(1)
    finally:
        await client.disconnect()


async def send_heartbeat_cmd(args):
    """Send a heartbeat for a service."""
    client = LaneswapAsyncClient(
        api_url=args.api_url,
        service_id=args.id
    )
    
    metadata = {}
    if args.metadata:
        try:
            metadata = json.loads(args.metadata)
        except json.JSONDecodeError:
            logger.error("Invalid JSON metadata")
            sys.exit(1)
            
    try:
        status = HeartbeatStatus(args.status)
        result = await client.send_heartbeat(
            status=status,
            message=args.message,
            metadata=metadata
        )
        print(f"Heartbeat sent successfully. Current status: {result['status']}")
    except Exception as e:
        logger.error(f"Failed to send heartbeat: {str(e)}")
        sys.exit(1)
    finally:
        await client.disconnect()


async def list_services_cmd(args):
    """List all registered services."""
    client = LaneswapAsyncClient(api_url=args.api_url)
    
    try:
        result = await client.get_all_services()
        services = result.get("services", {})
        
        if not services:
            print("No services registered")
            return
            
        # Prepare table data
        table_data = []
        for service_id, service in services.items():
            last_heartbeat = service.get("last_heartbeat", "Never")
            if last_heartbeat and last_heartbeat != "Never":
                last_heartbeat = datetime.fromisoformat(last_heartbeat.replace("Z", "+00:00"))
                last_heartbeat = last_heartbeat.strftime("%Y-%m-%d %H:%M:%S")
                
            table_data.append([
                service_id,
                service.get("name", "Unknown"),
                service.get("status", "unknown"),
                last_heartbeat,
                service.get("last_message", "")
            ])
            
        # Print table
        headers = ["ID", "Name", "Status", "Last Heartbeat", "Last Message"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        # Print summary
        summary = result.get("summary", {})
        if summary:
            print("\nSummary:")
            print(f"Total services: {summary.get('total', 0)}")
            status_counts = summary.get("status_counts", {})
            for status, count in status_counts.items():
                if count > 0:
                    print(f"  {status}: {count}")
    except Exception as e:
        logger.error(f"Failed to list services: {str(e)}")
        sys.exit(1)
    finally:
        await client.disconnect()


async def get_service_cmd(args):
    """Get details for a specific service."""
    client = LaneswapAsyncClient(
        api_url=args.api_url,
        service_id=args.id
    )
    
    try:
        service = await client.get_status()
        
        # Print service details
        print(f"Service ID: {service['id']}")
        print(f"Name: {service['name']}")
        print(f"Status: {service['status']}")
        
        last_heartbeat = service.get("last_heartbeat", "Never")
        if last_heartbeat and last_heartbeat != "Never":
            last_heartbeat = datetime.fromisoformat(last_heartbeat.replace("Z", "+00:00"))
            last_heartbeat = last_heartbeat.strftime("%Y-%m-%d %H:%M:%S")
        print(f"Last Heartbeat: {last_heartbeat}")
        
        if service.get("last_message"):
            print(f"Last Message: {service['last_message']}")
            
        # Print metadata
        metadata = service.get("metadata", {})
        if metadata:
            print("\nMetadata:")
            for key, value in metadata.items():
                print(f"  {key}: {value}")
                
        # Print recent events
        events = service.get("events", [])
        if events:
            print("\nRecent Events:")
            for event in events[:10]:  # Show only the 10 most recent events
                timestamp = datetime.fromisoformat(event['timestamp'].replace("Z", "+00:00"))
                timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                print(f"  [{timestamp}] {event['status']}: {event.get('message', '')}")
    except Exception as e:
        logger.error(f"Failed to get service details: {str(e)}")
        sys.exit(1)
    finally:
        await client.disconnect()


def start_server(args):
    """Start the LaneSwap API server."""
    # Set environment variables from arguments
    os.environ["HOST"] = args.host
    os.environ["PORT"] = str(args.port)
    os.environ["DEBUG"] = str(args.debug).lower()
    
    if args.mongodb_url:
        os.environ["MONGODB_URL"] = args.mongodb_url
        
    if args.discord_webhook:
        os.environ["DISCORD_WEBHOOK_URL"] = args.discord_webhook
    
    # Generate and display URLs
    from laneswap.api.main import get_server_urls
    urls = get_server_urls(args.host, args.port)
    
    print("\n" + "=" * 50)
    print("LaneSwap Server is starting...")
    print("=" * 50)
    
    for base_url, endpoints in urls.items():
        print(f"\nAccess points for {base_url}:")
        print(f"  API Endpoint: {endpoints['api']}")
        print(f"  API Documentation: {endpoints['docs']}")
        print(f"  Web Monitor: {endpoints['web_monitor']}")
    
    print("\n" + "=" * 50)
        
    # Start the server
    uvicorn.run(
        "laneswap.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.debug
    )


async def monitor_services(args):
    """Monitor services in real-time."""
    client = LaneswapAsyncClient(api_url=args.api_url)
    
    try:
        print("Monitoring services (press Ctrl+C to stop)...")
        while True:
            result = await client.get_all_services()
            services = result.get("services", {})
            
            # Clear screen
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # Print header
            print(f"LaneSwap Service Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 80)
            
            if not services:
                print("No services registered")
            else:
                # Prepare table data
                table_data = []
                for service_id, service in services.items():
                    last_heartbeat = service.get("last_heartbeat", "Never")
                    if last_heartbeat and last_heartbeat != "Never":
                        last_heartbeat = datetime.fromisoformat(last_heartbeat.replace("Z", "+00:00"))
                        last_heartbeat = last_heartbeat.strftime("%Y-%m-%d %H:%M:%S")
                        
                    table_data.append([
                        service.get("name", "Unknown"),
                        service_id,
                        service.get("status", "unknown"),
                        last_heartbeat,
                        service.get("last_message", "")
                    ])
                
                # Print table
                print(tabulate(
                    table_data,
                    headers=["Name", "ID", "Status", "Last Heartbeat", "Message"],
                    tablefmt="simple"
                ))
            
            # Wait before refreshing
            await asyncio.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nMonitoring stopped")
    except Exception as e:
        logger.error(f"Error monitoring services: {str(e)}")
        sys.exit(1)
    finally:
        await client.disconnect()


def launch_web_monitor(args):
    """Launch the web monitor in a browser."""
    from laneswap.examples.web_monitor.launch import start_dashboard
    
    # Launch the web monitor
    start_dashboard(
        port=args.port,
        api_url=args.api_url,
        open_browser=not args.no_browser
    )


@click.group()
def cli():
    """LaneSwap CLI commands."""
    pass

@cli.command()
@click.option('--service-id', help='Service ID to focus on')
@click.option('--api-url', default='http://localhost:8000', help='API URL')
@click.option('--monitor-url', default='http://localhost:8080', help='Web monitor URL')
@click.option('--open-browser', is_flag=True, default=True, help='Open URL in browser')
@click.option('--start-if-needed', is_flag=True, default=True, help='Start the monitor if not running')
def monitor_link(service_id, api_url, monitor_url, open_browser, start_if_needed):
    """Generate a link to the web monitor for a service."""
    async def generate():
        try:
            # Generate the URL - simplified to avoid potential issues
            url = f"{monitor_url}"
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url
                
            if not url.endswith("/"):
                url += "/"
                
            # Add query parameters
            params = []
            if api_url:
                if not api_url.startswith(('http://', 'https://')):
                    api_url = 'http://' + api_url
                params.append(f"api={api_url}")
            if service_id:
                params.append(f"service={service_id}")
                
            if params:
                url += "?" + "&".join(params)
            
            print(f"Monitor URL: {url}")
            
            # Check if the monitor is running
            if start_if_needed:
                try:
                    import requests
                    response = requests.get(url, timeout=1)
                    if response.status_code != 200:
                        print("Web monitor is not responding correctly. Starting it...")
                        await start_monitor(monitor_url, api_url)
                except Exception:
                    print("Web monitor is not running. Starting it...")
                    await start_monitor(monitor_url, api_url)
            
            if open_browser:
                print("Opening browser...")
                webbrowser.open(url)
                
        except Exception as e:
            logger.error(f"Error generating monitor URL: {str(e)}")
            sys.exit(1)
            
    asyncio.run(generate())

@cli.command()
def start_monitor():
    """Start the web monitor dashboard in a robust way."""
    from ..core.config import API_URL, MONITOR_URL
    import re
    import socket
    import sys
    import os
    from pathlib import Path
    
    # Function to check if port is in use
    def is_port_in_use(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    
    # Extract port from monitor URL
    port_match = re.search(r':(\d+)', MONITOR_URL)
    port = 8080  # Default port
    if port_match:
        port = int(port_match.group(1))
    
    # Check if the monitor is already running
    if is_port_in_use(port):
        print(f"Web monitor is already running on port {port}")
        print(f"Access it at: {MONITOR_URL}")
        return
    
    print(f"Starting web monitor on port {port}...")
    print(f"API URL: {API_URL}")
    print(f"Monitor URL: {MONITOR_URL}")
    
    # Use the standalone script for better reliability
    monitor_script = Path(__file__).parent.parent / "examples" / "start_monitor.py"
    
    if monitor_script.exists():
        # Run the script directly
        os.execl(sys.executable, sys.executable, str(monitor_script), 
                 "--port", str(port), "--api-url", API_URL)
    else:
        # Fall back to the module approach
        from ..examples.web_monitor.launch import start_dashboard
        start_dashboard(port=port, api_url=API_URL)

@cli.command()
@click.option('--port', default=8080, help='Port to run the web monitor on')
@click.option('--api-url', default='http://localhost:8000', help='API URL')
def dashboard(port, api_url):
    """Start the web monitor dashboard."""
    from ..examples.web_monitor.launch import start_dashboard
    
    try:
        print(f"Starting dashboard on port {port}, connecting to API at {api_url}")
        print(f"Access the dashboard at: http://localhost:{port}/")
        start_dashboard(port=port, api_url=api_url)
    except Exception as e:
        logger.error(f"Error starting dashboard: {str(e)}")
        sys.exit(1)

@cli.command()
def check_servers():
    """Check if both API and web monitor servers are running."""
    print("Checking LaneSwap servers...")
    
    # Check API server
    try:
        response = requests.get(f"{API_URL}/api/health")
        if response.status_code == 200:
            print(f"✅ API server is running at {API_URL}")
        else:
            print(f"❌ API server returned status code {response.status_code}")
    except Exception as e:
        print(f"❌ API server is not running at {API_URL}: {str(e)}")
    
    # Check web monitor server
    try:
        response = requests.get(MONITOR_URL)
        if response.status_code == 200:
            print(f"✅ Web monitor is running at {MONITOR_URL}")
        else:
            print(f"❌ Web monitor returned status code {response.status_code}")
    except Exception as e:
        print(f"❌ Web monitor is not running at {MONITOR_URL}: {str(e)}")
    
    print("\nTo start the servers:")
    print(f"  API server:    laneswap server --port {API_URL.split(':')[-1]}")
    print(f"  Web monitor:   laneswap dashboard --port {MONITOR_URL.split(':')[-1]} --api-url {API_URL}")

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="LaneSwap CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Common arguments
    api_url_arg = lambda p: p.add_argument("--api-url", default="http://localhost:8000", help="LaneSwap API URL")
    
    # Register service command
    register_parser = subparsers.add_parser("register", help="Register a new service")
    api_url_arg(register_parser)
    register_parser.add_argument("--name", required=True, help="Service name")
    register_parser.add_argument("--id", help="Service ID (optional)")
    register_parser.add_argument("--metadata", help="Service metadata (JSON)")
    
    # Send heartbeat command
    heartbeat_parser = subparsers.add_parser("heartbeat", help="Send a heartbeat")
    api_url_arg(heartbeat_parser)
    heartbeat_parser.add_argument("--id", required=True, help="Service ID")
    heartbeat_parser.add_argument("--status", default="healthy", choices=[s.value for s in HeartbeatStatus], help="Heartbeat status")
    heartbeat_parser.add_argument("--message", help="Heartbeat message")
    heartbeat_parser.add_argument("--metadata", help="Heartbeat metadata (JSON)")
    
    # List services command
    list_parser = subparsers.add_parser("list", help="List all services")
    api_url_arg(list_parser)
    
    # Get service command
    get_parser = subparsers.add_parser("get", help="Get service details")
    api_url_arg(get_parser)
    get_parser.add_argument("--id", required=True, help="Service ID")
    
    # Start server command
    server_parser = subparsers.add_parser("server", help="Start the LaneSwap API server")
    server_parser.add_argument("--host", default="0.0.0.0", help="Server host")
    server_parser.add_argument("--port", type=int, default=8000, help="Server port")
    server_parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    server_parser.add_argument("--mongodb-url", help="MongoDB connection URL")
    server_parser.add_argument("--discord-webhook", help="Discord webhook URL")
    
    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Monitor services in real-time")
    api_url_arg(monitor_parser)
    monitor_parser.add_argument("--interval", type=int, default=5, help="Refresh interval in seconds")
    
    # Web monitor command
    web_monitor_parser = subparsers.add_parser("web", help="Launch the web monitor")
    web_monitor_parser.add_argument("--port", type=int, default=8080, help="Port for the web server")
    api_url_arg(web_monitor_parser)
    web_monitor_parser.add_argument("--no-browser", action="store_true", help="Don't open a browser window")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set up logging
    setup_logging()
    
    # Run command
    if args.command == "register":
        asyncio.run(register_service_cmd(args))
    elif args.command == "heartbeat":
        asyncio.run(send_heartbeat_cmd(args))
    elif args.command == "list":
        asyncio.run(list_services_cmd(args))
    elif args.command == "get":
        asyncio.run(get_service_cmd(args))
    elif args.command == "server":
        start_server(args)
    elif args.command == "monitor":
        asyncio.run(monitor_services(args))
    elif args.command == "web":
        launch_web_monitor(args)
    elif args.command == "monitor_link":
        asyncio.run(monitor_link(args.service_id, args.api_url, args.monitor_url, args.open_browser, args.start_if_needed))
    elif args.command == "dashboard":
        asyncio.run(dashboard(args.port, args.api_url))
    elif args.command == "check_servers":
        asyncio.run(check_servers())
    elif args.command == "start_monitor":
        asyncio.run(start_monitor())
    else:
        parser.print_help()


if __name__ == "__main__":
    cli() 