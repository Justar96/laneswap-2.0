#!/usr/bin/env python3
"""
LaneSwap Terminal Interface Example

This example demonstrates how to create a custom terminal interface
for interacting with a LaneSwap network.
"""

import asyncio
import logging
import argparse
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from laneswap.terminal import TerminalApp, Command, CommandResult
from laneswap.client import LaneSwapClient
from laneswap.core.models import ServiceType, ServiceConfig, ServiceStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("terminal-example")

class CustomTerminalApp(TerminalApp):
    """
    A custom terminal application for interacting with LaneSwap.
    """
    
    def __init__(self, api_url: str, api_key: str):
        """
        Initialize the custom terminal application.
        
        Args:
            api_url: URL of the LaneSwap API
            api_key: API key for authentication
        """
        super().__init__(
            name="LaneSwap Custom Terminal",
            description="A custom terminal interface for LaneSwap",
            version="1.0.0"
        )
        
        self.api_url = api_url
        self.api_key = api_key
        self.client = None
        
        # Register commands
        self.register_command(
            Command(
                name="list-services",
                description="List all registered services",
                handler=self.handle_list_services,
                args=[
                    {
                        "name": "--status",
                        "help": "Filter services by status",
                        "choices": ["active", "inactive", "error"],
                        "required": False
                    },
                    {
                        "name": "--type",
                        "help": "Filter services by type",
                        "choices": ["client", "adapter", "core", "api"],
                        "required": False
                    }
                ]
            )
        )
        
        self.register_command(
            Command(
                name="service-info",
                description="Get detailed information about a service",
                handler=self.handle_service_info,
                args=[
                    {
                        "name": "service_id",
                        "help": "ID of the service to get information for",
                        "required": True
                    }
                ]
            )
        )
        
        self.register_command(
            Command(
                name="send-message",
                description="Send a message to a service",
                handler=self.handle_send_message,
                args=[
                    {
                        "name": "service_id",
                        "help": "ID of the service to send the message to",
                        "required": True
                    },
                    {
                        "name": "message",
                        "help": "JSON message to send (as a string)",
                        "required": True
                    }
                ]
            )
        )
        
        self.register_command(
            Command(
                name="register-service",
                description="Register a new service",
                handler=self.handle_register_service,
                args=[
                    {
                        "name": "name",
                        "help": "Name of the service",
                        "required": True
                    },
                    {
                        "name": "type",
                        "help": "Type of the service",
                        "choices": ["client", "adapter", "core", "api"],
                        "required": True
                    },
                    {
                        "name": "description",
                        "help": "Description of the service",
                        "required": True
                    },
                    {
                        "name": "--config",
                        "help": "JSON configuration for the service (as a string)",
                        "required": False,
                        "default": "{}"
                    }
                ]
            )
        )
        
        self.register_command(
            Command(
                name="deregister-service",
                description="Deregister a service",
                handler=self.handle_deregister_service,
                args=[
                    {
                        "name": "service_id",
                        "help": "ID of the service to deregister",
                        "required": True
                    }
                ]
            )
        )
        
        self.register_command(
            Command(
                name="monitor",
                description="Monitor events from a service",
                handler=self.handle_monitor,
                args=[
                    {
                        "name": "service_id",
                        "help": "ID of the service to monitor",
                        "required": True
                    },
                    {
                        "name": "--duration",
                        "help": "Duration to monitor in seconds",
                        "type": int,
                        "required": False,
                        "default": 60
                    }
                ]
            )
        )
    
    async def startup(self) -> None:
        """Initialize the client and connect to LaneSwap."""
        self.client = LaneSwapClient(
            api_url=self.api_url,
            api_key=self.api_key,
            service_name="custom-terminal",
            service_type=ServiceType.CLIENT
        )
        
        await self.client.connect()
        logger.info("Connected to LaneSwap network")
        
        self.print_info("Connected to LaneSwap network")
    
    async def shutdown(self) -> None:
        """Disconnect from LaneSwap."""
        if self.client:
            await self.client.disconnect()
            logger.info("Disconnected from LaneSwap network")
            
            self.print_info("Disconnected from LaneSwap network")
    
    async def handle_list_services(self, args: argparse.Namespace) -> CommandResult:
        """
        Handle the list-services command.
        
        Args:
            args: Command arguments
            
        Returns:
            Command result
        """
        try:
            services = await self.client.get_services()
            
            # Apply filters if provided
            if args.status:
                status_map = {
                    "active": ServiceStatus.ACTIVE,
                    "inactive": ServiceStatus.INACTIVE,
                    "error": ServiceStatus.ERROR
                }
                services = [s for s in services if s.status == status_map.get(args.status)]
            
            if args.type:
                type_map = {
                    "client": ServiceType.CLIENT,
                    "adapter": ServiceType.ADAPTER,
                    "core": ServiceType.CORE,
                    "api": ServiceType.API
                }
                services = [s for s in services if s.type == type_map.get(args.type)]
            
            # Format the output
            if not services:
                return CommandResult(
                    success=True,
                    message="No services found matching the criteria",
                    data=[]
                )
            
            formatted_services = []
            for service in services:
                formatted_services.append({
                    "id": service.id,
                    "name": service.name,
                    "type": service.type.value,
                    "status": service.status.value,
                    "created_at": service.created_at.isoformat() if service.created_at else None,
                    "last_heartbeat": service.last_heartbeat.isoformat() if service.last_heartbeat else None
                })
            
            return CommandResult(
                success=True,
                message=f"Found {len(services)} services",
                data=formatted_services
            )
            
        except Exception as e:
            logger.error(f"Error listing services: {e}")
            return CommandResult(
                success=False,
                message=f"Error listing services: {str(e)}",
                data=None
            )
    
    async def handle_service_info(self, args: argparse.Namespace) -> CommandResult:
        """
        Handle the service-info command.
        
        Args:
            args: Command arguments
            
        Returns:
            Command result
        """
        try:
            service = await self.client.get_service(args.service_id)
            
            if not service:
                return CommandResult(
                    success=False,
                    message=f"Service not found with ID: {args.service_id}",
                    data=None
                )
            
            # Format the output
            formatted_service = {
                "id": service.id,
                "name": service.name,
                "type": service.type.value,
                "description": service.description,
                "status": service.status.value,
                "created_at": service.created_at.isoformat() if service.created_at else None,
                "last_heartbeat": service.last_heartbeat.isoformat() if service.last_heartbeat else None,
                "config": service.config
            }
            
            return CommandResult(
                success=True,
                message=f"Service information for {service.name}",
                data=formatted_service
            )
            
        except Exception as e:
            logger.error(f"Error getting service info: {e}")
            return CommandResult(
                success=False,
                message=f"Error getting service info: {str(e)}",
                data=None
            )
    
    async def handle_send_message(self, args: argparse.Namespace) -> CommandResult:
        """
        Handle the send-message command.
        
        Args:
            args: Command arguments
            
        Returns:
            Command result
        """
        try:
            # Parse the message JSON
            try:
                message_content = json.loads(args.message)
            except json.JSONDecodeError:
                return CommandResult(
                    success=False,
                    message="Invalid JSON message",
                    data=None
                )
            
            # Send the message
            response = await self.client.send_message(args.service_id, message_content)
            
            return CommandResult(
                success=True,
                message=f"Message sent to service {args.service_id}",
                data=response
            )
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return CommandResult(
                success=False,
                message=f"Error sending message: {str(e)}",
                data=None
            )
    
    async def handle_register_service(self, args: argparse.Namespace) -> CommandResult:
        """
        Handle the register-service command.
        
        Args:
            args: Command arguments
            
        Returns:
            Command result
        """
        try:
            # Parse the config JSON
            try:
                config = json.loads(args.config)
            except json.JSONDecodeError:
                return CommandResult(
                    success=False,
                    message="Invalid JSON configuration",
                    data=None
                )
            
            # Map the service type
            type_map = {
                "client": ServiceType.CLIENT,
                "adapter": ServiceType.ADAPTER,
                "core": ServiceType.CORE,
                "api": ServiceType.API
            }
            
            service_type = type_map.get(args.type)
            if not service_type:
                return CommandResult(
                    success=False,
                    message=f"Invalid service type: {args.type}",
                    data=None
                )
            
            # Create the service config
            service_config = ServiceConfig(
                name=args.name,
                type=service_type,
                description=args.description,
                config=config
            )
            
            # Register the service
            service_id = await self.client.register_service(service_config)
            
            return CommandResult(
                success=True,
                message=f"Service registered with ID: {service_id}",
                data={"service_id": service_id}
            )
            
        except Exception as e:
            logger.error(f"Error registering service: {e}")
            return CommandResult(
                success=False,
                message=f"Error registering service: {str(e)}",
                data=None
            )
    
    async def handle_deregister_service(self, args: argparse.Namespace) -> CommandResult:
        """
        Handle the deregister-service command.
        
        Args:
            args: Command arguments
            
        Returns:
            Command result
        """
        try:
            # Deregister the service
            success = await self.client.deregister_service(args.service_id)
            
            if success:
                return CommandResult(
                    success=True,
                    message=f"Service deregistered: {args.service_id}",
                    data=None
                )
            else:
                return CommandResult(
                    success=False,
                    message=f"Failed to deregister service: {args.service_id}",
                    data=None
                )
            
        except Exception as e:
            logger.error(f"Error deregistering service: {e}")
            return CommandResult(
                success=False,
                message=f"Error deregistering service: {str(e)}",
                data=None
            )
    
    async def handle_monitor(self, args: argparse.Namespace) -> CommandResult:
        """
        Handle the monitor command.
        
        Args:
            args: Command arguments
            
        Returns:
            Command result
        """
        try:
            events = []
            
            # Define the event handler
            async def event_handler(event):
                timestamp = datetime.now().isoformat()
                formatted_event = {
                    "timestamp": timestamp,
                    "event": event
                }
                events.append(formatted_event)
                self.print_info(f"[{timestamp}] Event received: {json.dumps(event)}")
            
            # Subscribe to events
            await self.client.subscribe(args.service_id, event_handler)
            self.print_info(f"Monitoring events from service {args.service_id} for {args.duration} seconds...")
            
            # Wait for the specified duration
            await asyncio.sleep(args.duration)
            
            # Unsubscribe from events
            await self.client.unsubscribe(args.service_id)
            
            return CommandResult(
                success=True,
                message=f"Monitored {len(events)} events from service {args.service_id}",
                data=events
            )
            
        except Exception as e:
            logger.error(f"Error monitoring service: {e}")
            return CommandResult(
                success=False,
                message=f"Error monitoring service: {str(e)}",
                data=None
            )


async def main():
    """Main function to run the terminal application."""
    parser = argparse.ArgumentParser(description="LaneSwap Custom Terminal Example")
    parser.add_argument("--api-url", default="http://localhost:8000", help="URL of the LaneSwap API")
    parser.add_argument("--api-key", default="your-api-key", help="API key for authentication")
    
    args = parser.parse_args()
    
    # Create and run the terminal application
    app = CustomTerminalApp(api_url=args.api_url, api_key=args.api_key)
    await app.run()

if __name__ == "__main__":
    asyncio.run(main()) 