"""
Command-line interface for LaneSwap.

This module provides a command-line interface for managing LaneSwap
services and monitoring.
"""

import asyncio
import json
import logging
import os
import sys
import time
import webbrowser
from datetime import datetime
from typing import Any, List, Optional

import click
import requests
import uvicorn
from tabulate import tabulate

from ..adapters.discord import DiscordWebhookAdapter
from ..client.async_client import LaneswapAsyncClient
from ..core.config import API_URL, MONITOR_URL
from ..core.heartbeat import (
    HeartbeatStatus,
    generate_monitor_url,
    get_all_services,
    get_service,
    initialize,
    register_service,
    send_heartbeat,
)

# Import validator if available
try:
    from ..core.validator import run_validation
    _validator_available = True
except ImportError:
    _validator_available = False

logger = logging.getLogger("laneswap.cli")

# Global Discord adapter for CLI commands
_discord_adapter = None

def get_discord_adapter() -> DiscordWebhookAdapter:
    """Get or create the Discord adapter singleton."""
    global _discord_adapter
    if _discord_adapter is None:
        _discord_adapter = DiscordWebhookAdapter()
    return _discord_adapter

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
        logger.error("Error registering service: %s", str(e))
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
        logger.error("Failed to send heartbeat: %s", str(e))
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
        logger.error("Failed to list services: %s", str(e))
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
        logger.error("Failed to get service details: %s", str(e))
        sys.exit(1)
    finally:
        await client.disconnect()


def start_server(args):
    """Start the API server."""
    from laneswap.api.server import start_server as start_api_server

    try:
        print(f"Starting API server on {args.host}:{args.port}")
        start_api_server(
            host=args.host,
            port=args.port,
            debug=args.debug,
            start_monitor=not args.no_monitor,
            monitor_port=args.monitor_port,
            open_browser=not args.no_browser
        )
    except Exception as e:
        logger.error("Error starting API server: %s", str(e))
        sys.exit(1)


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
        logger.error("Error monitoring services: %s", str(e))
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
            logger.error("Error generating monitor URL: %s", str(e))
            sys.exit(1)

    asyncio.run(generate())

@cli.command()
def start_monitor():
    """Start the web monitor dashboard in a robust way."""
    import re
    import socket
    from pathlib import Path

    from ..core.config import API_URL, MONITOR_URL

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
        logger.error("Error starting dashboard: %s", str(e))
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

@cli.group()
def discord():
    """Manage Discord webhook notifications."""
    pass

@discord.command()
@click.option('--webhook-url', required=True, help='Discord webhook URL')
@click.option('--username', default='Laneswap Monitor', help='Display name for the webhook')
@click.option('--avatar-url', help='Avatar URL for the webhook')
def setup(webhook_url, username, avatar_url):
    """Set up the default Discord webhook."""
    adapter = get_discord_adapter()
    adapter.webhook_url = webhook_url
    adapter.username = username
    if avatar_url:
        adapter.avatar_url = avatar_url

    click.echo(f"Default Discord webhook configured with URL: {webhook_url}")
    click.echo(f"Username: {username}")
    if avatar_url:
        click.echo(f"Avatar URL: {avatar_url}")

@discord.command()
@click.option('--service-id', required=True, help='Service ID to configure webhook for')
@click.option('--webhook-url', required=True, help='Discord webhook URL')
@click.option('--username', help='Display name for the webhook (defaults to global setting)')
@click.option('--avatar-url', help='Avatar URL for the webhook (defaults to global setting)')
@click.option('--levels', help='Comma-separated list of notification levels (info,success,warning,error)')
def register(service_id, webhook_url, username, avatar_url, levels):
    """Register a Discord webhook for a specific service."""
    adapter = get_discord_adapter()

    notification_levels = None
    if levels:
        notification_levels = [level.strip().lower() for level in levels.split(',')]

    adapter.register_service_webhook(
        service_id=service_id,
        webhook_url=webhook_url,
        username=username,
        avatar_url=avatar_url,
        notification_levels=notification_levels
    )

    click.echo(f"Discord webhook registered for service {service_id}")
    if notification_levels:
        click.echo(f"Notification levels: {', '.join(notification_levels)}")

@discord.command()
@click.option('--service-id', required=True, help='Service ID to remove webhook for')
def unregister(service_id):
    """Remove a Discord webhook for a specific service."""
    adapter = get_discord_adapter()

    if adapter.remove_service_webhook(service_id):
        click.echo(f"Discord webhook removed for service {service_id}")
    else:
        click.echo(f"No Discord webhook found for service {service_id}")

@discord.command()
@click.option('--service-id', help='Service ID to get webhook config for (optional)')
def list(service_id):
    """List Discord webhook configurations."""
    adapter = get_discord_adapter()

    if service_id:
        config = adapter.get_service_webhook_config(service_id)
        if config:
            click.echo(f"Discord webhook configuration for service {service_id}:")
            click.echo(f"  Webhook URL: {config['webhook_url']}")
            click.echo(f"  Username: {config['username']}")
            if config.get('avatar_url'):
                click.echo(f"  Avatar URL: {config['avatar_url']}")
            click.echo(f"  Notification levels: {', '.join(config['notification_levels'])}")
        else:
            click.echo(f"No Discord webhook configuration found for service {service_id}")
    else:
        webhooks = adapter.list_service_webhooks()
        if webhooks:
            click.echo("Service-specific Discord webhook configurations:")
            for service_id, config in webhooks.items():
                click.echo(f"\nService ID: {service_id}")
                click.echo(f"  Webhook URL: {config['webhook_url']}")
                click.echo(f"  Username: {config['username']}")
                if config.get('avatar_url'):
                    click.echo(f"  Avatar URL: {config['avatar_url']}")
                click.echo(f"  Notification levels: {', '.join(config['notification_levels'])}")
        else:
            click.echo("No service-specific Discord webhook configurations found")

        # Also show default webhook if configured
        if adapter.webhook_url:
            click.echo("\nDefault Discord webhook configuration:")
            click.echo(f"  Webhook URL: {adapter.webhook_url}")
            click.echo(f"  Username: {adapter.username}")
            if adapter.avatar_url:
                click.echo(f"  Avatar URL: {adapter.avatar_url}")
        else:
            click.echo("\nNo default Discord webhook configured")

@discord.command()
@click.option('--service-id', required=True, help='Service ID to test notification for')
@click.option('--level', type=click.Choice(['info', 'success', 'warning', 'error']), default='info',
              help='Notification level')
@click.option('--message', default='Test notification from Laneswap CLI', help='Custom message')
def test(service_id, level, message):
    """Test a Discord webhook notification for a service."""
    adapter = get_discord_adapter()

    async def run_test():
        # Get service info
        try:
            service_info = await get_service(service_id)

            # Send test notification
            success = await adapter.send_notification(
                title=f"Test Notification - {service_info.get('name', service_id)}",
                message=message,
                service_info=service_info,
                level=level
            )

            if success:
                click.echo(f"Test notification sent successfully to Discord for service {service_id}")
            else:
                click.echo(f"Failed to send test notification to Discord for service {service_id}")

        except Exception as e:
            click.echo(f"Error testing Discord notification: {str(e)}")

    asyncio.run(run_test())

@cli.command()
@click.option('--no-terminal-monitor', is_flag=True, help='Skip terminal monitor validation')
@click.option('--strict', is_flag=True, help='Treat warnings as errors')
@click.option('--quiet', is_flag=True, help='Don\'t print validation results')
def validate(no_terminal_monitor, strict, quiet):
    """Validate LaneSwap installation."""
    try:
        if not _validator_available:
            click.echo("Validator module not available. Make sure LaneSwap is installed correctly.")
            return 1

        from ..core.validator import run_validation

        # Run validation
        results = run_validation(
            check_terminal_monitor=not no_terminal_monitor,
            print_results=not quiet
        )

        # Return exit code based on validation results
        if results["overall_status"] == "error":
            return 1
        elif results["overall_status"] == "warning" and strict:
            return
        # Removed unnecessary else:
            return 0
    except Exception as e:
        click.echo(f"Error running validation: {str(e)}")
        return 1

def main():
    """Main entry point for the CLI."""
    try:
        # Set up logging
        setup_logging()

        # Run validation on startup if available
        if _validator_available:
            try:
                from ..core.validator import run_validation

                # Run validation but don't print results
                run_validation(check_terminal_monitor=True, print_results=False)
            except Exception as e:
                logger.warning("Validation failed: %s", str(e))

        # Run the CLI
        cli()
    except Exception as e:
        logger.error("Error in CLI: %s", str(e))
        sys.exit(1)


if __name__ == "__main__":
    cli()
