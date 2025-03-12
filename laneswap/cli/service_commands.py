"""
Service management commands for LaneSwap CLI.

This module provides commands for managing services via the command line.
"""

import asyncio
import logging
import json
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import time
import click
from tabulate import tabulate
import os
import signal

from ..core.heartbeat import (
    HeartbeatStatus, register_service, send_heartbeat, 
    get_service, get_all_services, initialize
)
from ..client.async_client import LaneswapAsyncClient
from ..core.config import API_URL
from ..adapters.discord import DiscordWebhookAdapter

logger = logging.getLogger("laneswap.cli.service")


@click.group()
def service():
    """Manage LaneSwap services."""
    pass


@service.command()
@click.option('--name', required=True, help='Service name')
@click.option('--id', help='Service ID (optional, will be generated if not provided)')
@click.option('--metadata', help='JSON metadata for the service')
@click.option('--api-url', default=API_URL, help='API URL')
@click.option('--webhook-url', help='Discord webhook URL for this service')
def register(name, id, metadata, api_url, webhook_url):
    """Register a new service."""
    meta_dict = None
    if metadata:
        try:
            meta_dict = json.loads(metadata)
        except json.JSONDecodeError:
            click.echo("Error: Metadata must be valid JSON")
            sys.exit(1)
    
    async def run():
        client = None
        try:
            # Initialize the client with the service name
            logger.debug(f"Initializing client with API URL: {api_url}")
            client = LaneswapAsyncClient(
                api_url=api_url,
                service_name=name  # Pass the service name here
            )
            
            # Connect to the API
            logger.debug("Connecting to API...")
            await client.connect()
            
            # Register the service
            logger.debug(f"Registering service '{name}' with metadata: {meta_dict}")
            service_id = await client.register_service(
                service_name=name,
                service_id=id,
                metadata=meta_dict
            )
            
            click.echo(f"Service registered successfully!")
            click.echo(f"Service ID: {service_id}")
            click.echo(f"Service Name: {name}")
            
            # Register Discord webhook if provided
            if webhook_url:
                logger.debug(f"Configuring Discord webhook for service {service_id}")
                adapter = DiscordWebhookAdapter(webhook_url=webhook_url)
                adapter.register_service_webhook(
                    service_id=service_id,
                    webhook_url=webhook_url
                )
                click.echo(f"Discord webhook registered for service")
                
            return service_id
        except Exception as e:
            logger.error(f"Error registering service: {str(e)}", exc_info=True)
            click.echo(f"Error registering service: {str(e)}", err=True)
            sys.exit(1)
        finally:
            if client:
                logger.debug("Disconnecting client...")
                await client.close()  # Use close() instead of disconnect()
    
    return asyncio.run(run())


@service.command()
@click.option('--id', required=True, help='Service ID')
@click.option('--status', type=click.Choice(['healthy', 'warning', 'error']), 
              default='healthy', help='Service status')
@click.option('--message', help='Status message')
@click.option('--metadata', help='JSON metadata to include with heartbeat')
@click.option('--api-url', default=API_URL, help='API URL')
def heartbeat(id, status, message, metadata, api_url):
    """Send a heartbeat for a service."""
    status_map = {
        'healthy': HeartbeatStatus.HEALTHY,
        'warning': HeartbeatStatus.WARNING,
        'error': HeartbeatStatus.ERROR
    }
    
    meta_dict = None
    if metadata:
        try:
            meta_dict = json.loads(metadata)
        except json.JSONDecodeError:
            click.echo("Error: Metadata must be valid JSON")
            sys.exit(1)
    
    async def run():
        client = None
        try:
            client = LaneswapAsyncClient(api_url=api_url, service_id=id)
            await client.connect()
            
            # Add retry logic for connection issues
            max_retries = 3
            retry_delay = 1  # seconds
            
            for attempt in range(max_retries):
                try:
                    result = await client.send_heartbeat(
                        status=status_map[status],
                        message=message,
                        metadata=meta_dict
                    )
                    
                    click.echo(f"Heartbeat sent successfully for service {id}")
                    click.echo(f"Status: {status}")
                    if message:
                        click.echo(f"Message: {message}")
                    
                    return result
                except Exception as e:
                    if attempt < max_retries - 1:
                        click.echo(f"Attempt {attempt + 1} failed, retrying in {retry_delay} seconds...")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        raise
        except Exception as e:
            click.echo(f"Error sending heartbeat: {str(e)}")
            sys.exit(1)
        finally:
            if client:
                await client.disconnect()
    
    return asyncio.run(run())


@service.command()
@click.option('--id', help='Service ID (optional, lists all services if not provided)')
@click.option('--api-url', default=API_URL, help='API URL')
@click.option('--format', type=click.Choice(['table', 'json']), default='table', 
              help='Output format')
def list(id, api_url, format):
    """List services or get details for a specific service."""
    async def run():
        client = None
        try:
            # Initialize the client with a temporary name if no ID is provided
            client = LaneswapAsyncClient(
                api_url=api_url,
                service_id=id if id else None,
                service_name="cli-list-command" if not id else None
            )
            await client.connect()
            
            if id:
                # Get specific service
                service_info = await client.get_service()
                
                if format == 'json':
                    click.echo(json.dumps(service_info, default=str, indent=2))
                else:
                    # Display service details in a table
                    click.echo(f"Service Details for {id}:")
                    click.echo(f"Name: {service_info.get('name', 'Unknown')}")
                    click.echo(f"Status: {service_info.get('status', 'Unknown')}")
                    
                    # Format last heartbeat
                    last_heartbeat = service_info.get('last_heartbeat')
                    if last_heartbeat:
                        if isinstance(last_heartbeat, str):
                            last_heartbeat_str = last_heartbeat
                        else:
                            last_heartbeat_str = last_heartbeat.strftime("%Y-%m-%d %H:%M:%S")
                        click.echo(f"Last Heartbeat: {last_heartbeat_str}")
                    
                    # Display metadata
                    metadata = service_info.get('metadata', {})
                    if metadata:
                        click.echo("\nMetadata:")
                        for key, value in metadata.items():
                            click.echo(f"  {key}: {value}")
                    
                    # Display events if available
                    events = service_info.get('events', [])
                    if events:
                        click.echo("\nRecent Events:")
                        event_table = []
                        for event in events[:10]:  # Show last 10 events
                            timestamp = event.get('timestamp')
                            if isinstance(timestamp, datetime):
                                timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                            else:
                                timestamp_str = str(timestamp)
                            
                            event_table.append([
                                timestamp_str,
                                event.get('type', 'Unknown'),
                                event.get('status', 'Unknown'),
                                event.get('message', '')
                            ])
                        
                        click.echo(tabulate(
                            event_table,
                            headers=['Timestamp', 'Type', 'Status', 'Message'],
                            tablefmt='simple'
                        ))
            else:
                # List all services
                services = await client.get_all_services()
                
                if format == 'json':
                    click.echo(json.dumps(services, default=str, indent=2))
                else:
                    # Display services in a table
                    service_table = []
                    for service_id, service_info in services.items():
                        # Format last heartbeat
                        last_heartbeat = service_info.get('last_heartbeat')
                        if last_heartbeat:
                            if isinstance(last_heartbeat, str):
                                last_heartbeat_str = last_heartbeat
                            elif isinstance(last_heartbeat, datetime):
                                last_heartbeat_str = last_heartbeat.strftime("%Y-%m-%d %H:%M:%S")
                            else:
                                last_heartbeat_str = str(last_heartbeat)
                        else:
                            last_heartbeat_str = "Never"
                        
                        service_table.append([
                            service_id,
                            service_info.get('name', 'Unknown'),
                            service_info.get('status', 'Unknown'),
                            last_heartbeat_str
                        ])
                    
                    click.echo(tabulate(
                        service_table,
                        headers=['ID', 'Name', 'Status', 'Last Heartbeat'],
                        tablefmt='simple'
                    ))
                    click.echo(f"\nTotal services: {len(services)}")
            
        except Exception as e:
            logger.error(f"Error retrieving services: {str(e)}", exc_info=True)
            click.echo(f"Error retrieving services: {str(e)}", err=True)
            sys.exit(1)
        finally:
            if client:
                await client.close()
    
    return asyncio.run(run())


@service.command()
@click.option('--id', required=True, help='Service ID')
@click.option('--interval', default=60, help='Heartbeat interval in seconds')
@click.option('--status', type=click.Choice(['healthy', 'warning', 'error']), 
              default='healthy', help='Initial service status')
@click.option('--message', help='Status message')
@click.option('--metadata', help='JSON metadata to include with heartbeat')
@click.option('--api-url', default=API_URL, help='API URL')
def daemon(id, interval, status, message, metadata, api_url):
    """Run a daemon process that sends heartbeats at regular intervals."""
    status_map = {
        'healthy': HeartbeatStatus.HEALTHY,
        'warning': HeartbeatStatus.WARNING,
        'error': HeartbeatStatus.ERROR
    }
    
    meta_dict = None
    if metadata:
        try:
            meta_dict = json.loads(metadata)
        except json.JSONDecodeError:
            click.echo("Error: Metadata must be valid JSON")
            sys.exit(1)
    
    # Set up signal handling for graceful shutdown
    running = True
    
    def signal_handler(sig, frame):
        nonlocal running
        click.echo("\nShutting down heartbeat daemon...")
        running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    async def run():
        try:
            # Get service info
            service_info = await get_service(id)
            click.echo(f"Starting heartbeat daemon for service: {service_info.get('name', id)}")
            click.echo(f"Interval: {interval} seconds")
            click.echo(f"Initial status: {status}")
            click.echo("Press Ctrl+C to stop")
            
            # Send initial heartbeat
            await send_heartbeat(
                service_id=id,
                status=status_map[status],
                message=message,
                metadata=meta_dict
            )
            click.echo(f"Initial heartbeat sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Main loop
            while running:
                # Wait for the interval
                for _ in range(interval):
                    if not running:
                        break
                    await asyncio.sleep(1)
                
                if not running:
                    break
                
                # Send heartbeat
                await send_heartbeat(
                    service_id=id,
                    status=status_map[status],
                    message=message,
                    metadata=meta_dict
                )
                click.echo(f"Heartbeat sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Send final heartbeat with status update
            await send_heartbeat(
                service_id=id,
                status=HeartbeatStatus.WARNING,
                message="Service daemon stopped",
                metadata=meta_dict
            )
            click.echo("Final heartbeat sent with status: WARNING")
            
        except Exception as e:
            click.echo(f"Error in heartbeat daemon: {str(e)}")
            sys.exit(1)
    
    return asyncio.run(run())


@service.command()
@click.option('--id', required=True, help='Service ID')
@click.option('--webhook-url', required=True, help='Discord webhook URL')
@click.option('--username', help='Display name for the webhook')
@click.option('--levels', default='warning,error', 
              help='Comma-separated list of notification levels (info,success,warning,error)')
@click.option('--api-url', default=API_URL, help='API URL')
def webhook(id, webhook_url, username, levels, api_url):
    """Configure a Discord webhook for a service."""
    notification_levels = [level.strip().lower() for level in levels.split(',')]
    
    async def run():
        client = None
        try:
            # Initialize the client and connect
            client = LaneswapAsyncClient(api_url=api_url, service_id=id)
            await client.connect()
            
            # Verify service exists
            service_info = await client.get_service()
            
            # Initialize Discord adapter with the webhook URL
            adapter = DiscordWebhookAdapter(webhook_url=webhook_url)
            
            # Configure webhook for the service
            adapter.register_service_webhook(
                service_id=id,
                webhook_url=webhook_url,
                username=username,
                notification_levels=notification_levels
            )
            
            click.echo(f"Discord webhook configured for service: {service_info.get('name', id)}")
            click.echo(f"Notification levels: {', '.join(notification_levels)}")
            
            # Send test notification
            success = await adapter.send_notification(
                title=f"Webhook Configuration - {service_info.get('name', id)}",
                message="This is a test notification to confirm your webhook is configured correctly.",
                service_info=service_info,
                level="info"
            )
            
            if success:
                click.echo("Test notification sent successfully")
            else:
                click.echo("Failed to send test notification")
            
        except Exception as e:
            click.echo(f"Error configuring webhook: {str(e)}")
            sys.exit(1)
        finally:
            if client:
                await client.disconnect()
    
    return asyncio.run(run())


@service.command()
@click.option('--id', required=True, help='Service ID')
@click.option('--interval', default=60, help='Check interval in seconds')
@click.option('--webhook-url', required=True, help='Discord webhook URL')
def monitor(id, interval, webhook_url):
    """Monitor a service and send Discord notifications on status changes."""
    from .commands import get_discord_adapter
    
    # Set up signal handling for graceful shutdown
    running = True
    
    def signal_handler(sig, frame):
        nonlocal running
        click.echo("\nShutting down service monitor...")
        running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    async def run():
        try:
            # Configure webhook
            adapter = get_discord_adapter()
            adapter.register_service_webhook(
                service_id=id,
                webhook_url=webhook_url,
                notification_levels=["warning", "error"]
            )
            
            # Get initial service info
            service_info = await get_service(id)
            service_name = service_info.get('name', id)
            last_status = service_info.get('status', 'unknown')
            
            click.echo(f"Starting monitor for service: {service_name}")
            click.echo(f"Interval: {interval} seconds")
            click.echo(f"Initial status: {last_status}")
            click.echo("Press Ctrl+C to stop")
            
            # Send initial notification
            await adapter.send_notification(
                title=f"Service Monitoring Started - {service_name}",
                message=f"Monitoring service with ID: {id}\nCurrent status: {last_status}",
                service_info=service_info,
                level="info"
            )
            
            # Main loop
            while running:
                # Wait for the interval
                for _ in range(interval):
                    if not running:
                        break
                    await asyncio.sleep(1)
                
                if not running:
                    break
                
                # Get current service info
                try:
                    service_info = await get_service(id)
                    current_status = service_info.get('status', 'unknown')
                    
                    # Check if status changed
                    if current_status != last_status:
                        click.echo(f"Status changed: {last_status} -> {current_status}")
                        
                        # Determine notification level
                        level = "info"
                        if current_status == "warning":
                            level = "warning"
                        elif current_status == "error":
                            level = "error"
                        elif current_status == "healthy" and last_status in ["warning", "error"]:
                            level = "success"
                        
                        # Send notification
                        await adapter.send_notification(
                            title=f"Service Status Change - {service_name}",
                            message=f"Status changed from {last_status} to {current_status}",
                            service_info=service_info,
                            level=level
                        )
                        
                        last_status = current_status
                    
                except Exception as e:
                    click.echo(f"Error checking service: {str(e)}")
            
            # Send final notification
            await adapter.send_notification(
                title=f"Service Monitoring Stopped - {service_name}",
                message="Service monitoring has been stopped",
                service_info=service_info,
                level="info"
            )
            
        except Exception as e:
            click.echo(f"Error in service monitor: {str(e)}")
            sys.exit(1)
    
    return asyncio.run(run())


if __name__ == "__main__":
    service() 