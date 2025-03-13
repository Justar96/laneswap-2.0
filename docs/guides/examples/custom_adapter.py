#!/usr/bin/env python3
"""
Custom LaneSwap Adapter Example

This example demonstrates how to create a custom adapter for LaneSwap
that can connect to an external system and translate between LaneSwap's
protocol and the external system's protocol.
"""

import asyncio
import logging
import json
from typing import Dict, Any, Optional, Callable, Awaitable

from laneswap.adapters import BaseAdapter
from laneswap.core.models import Message, ServiceConfig, ServiceType
from laneswap.client import LaneSwapClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("custom-adapter-example")

class ExternalSystemClient:
    """
    A mock client for an external system that our adapter will connect to.
    In a real implementation, this would be replaced with an actual client
    for your external system.
    """
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connected = False
        self.callbacks = {}
        logger.info(f"Initialized external system client with connection: {connection_string}")
    
    async def connect(self) -> None:
        """Connect to the external system."""
        # In a real implementation, this would establish a connection
        await asyncio.sleep(0.5)  # Simulate connection delay
        self.connected = True
        logger.info("Connected to external system")
    
    async def disconnect(self) -> None:
        """Disconnect from the external system."""
        # In a real implementation, this would close the connection
        await asyncio.sleep(0.2)  # Simulate disconnection delay
        self.connected = False
        logger.info("Disconnected from external system")
    
    async def send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send a command to the external system and get a response."""
        if not self.connected:
            raise RuntimeError("Not connected to external system")
        
        # In a real implementation, this would send the command to the external system
        logger.info(f"Sending command to external system: {command}")
        await asyncio.sleep(0.3)  # Simulate processing delay
        
        # Simulate a response from the external system
        response = {
            "status": "success",
            "command_id": command.get("id", "unknown"),
            "result": f"Processed {command.get('action', 'unknown')} command",
            "timestamp": "2023-09-01T12:30:00Z"
        }
        
        logger.info(f"Received response from external system: {response}")
        return response
    
    def register_event_callback(self, event_type: str, callback: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        """Register a callback for a specific event type."""
        self.callbacks[event_type] = callback
        logger.info(f"Registered callback for event type: {event_type}")
    
    # For demonstration purposes, we'll add a method to simulate an event from the external system
    async def simulate_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Simulate an event from the external system."""
        if event_type in self.callbacks:
            logger.info(f"External system generated event: {event_type} - {event_data}")
            await self.callbacks[event_type](event_data)
        else:
            logger.warning(f"No callback registered for event type: {event_type}")


class CustomAdapter(BaseAdapter):
    """
    A custom adapter that connects LaneSwap to an external system.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the custom adapter.
        
        Args:
            config: Configuration dictionary for the adapter
        """
        super().__init__(config)
        self.connection_string = config.get("connection_string", "custom://localhost:9000")
        self.external_client = ExternalSystemClient(self.connection_string)
        self.event_handlers = {}
        logger.info(f"Initialized custom adapter with config: {config}")
    
    async def connect(self) -> None:
        """Connect to the external system."""
        await self.external_client.connect()
        
        # Register event callbacks
        self.external_client.register_event_callback("status_update", self._handle_status_event)
        self.external_client.register_event_callback("alert", self._handle_alert_event)
        
        logger.info("Custom adapter connected and event handlers registered")
    
    async def disconnect(self) -> None:
        """Disconnect from the external system."""
        await self.external_client.disconnect()
        logger.info("Custom adapter disconnected")
    
    async def handle_message(self, message: Message) -> Optional[Dict[str, Any]]:
        """
        Handle a message from LaneSwap and translate it to the external system.
        
        Args:
            message: The message from LaneSwap
            
        Returns:
            Optional response to send back to LaneSwap
        """
        logger.info(f"Handling message from LaneSwap: {message.content}")
        
        # Translate the LaneSwap message to an external system command
        external_command = self._translate_to_external_format(message.content)
        
        # Send the command to the external system
        external_response = await self.external_client.send_command(external_command)
        
        # Translate the external system response back to LaneSwap format
        laneswap_response = self._translate_to_laneswap_format(external_response)
        
        return laneswap_response
    
    async def _handle_status_event(self, event_data: Dict[str, Any]) -> None:
        """
        Handle a status update event from the external system.
        
        Args:
            event_data: The event data from the external system
        """
        logger.info(f"Handling status event from external system: {event_data}")
        
        # Translate the external event to LaneSwap format
        laneswap_event = {
            "type": "status_update",
            "source": "external_system",
            "timestamp": event_data.get("timestamp", ""),
            "data": {
                "status": event_data.get("status", "unknown"),
                "details": event_data.get("details", {})
            }
        }
        
        # Publish the event to LaneSwap
        await self.publish_event(laneswap_event)
    
    async def _handle_alert_event(self, event_data: Dict[str, Any]) -> None:
        """
        Handle an alert event from the external system.
        
        Args:
            event_data: The event data from the external system
        """
        logger.info(f"Handling alert event from external system: {event_data}")
        
        # Translate the external event to LaneSwap format
        laneswap_event = {
            "type": "alert",
            "source": "external_system",
            "severity": event_data.get("severity", "info"),
            "timestamp": event_data.get("timestamp", ""),
            "message": event_data.get("message", ""),
            "data": event_data.get("data", {})
        }
        
        # Publish the event to LaneSwap
        await self.publish_event(laneswap_event)
    
    def _translate_to_external_format(self, laneswap_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translate a LaneSwap message to the external system's format.
        
        Args:
            laneswap_message: The message from LaneSwap
            
        Returns:
            The translated message in the external system's format
        """
        # This is a simplified example. In a real implementation, you would
        # have more complex translation logic based on your external system's API.
        
        external_command = {
            "id": laneswap_message.get("id", ""),
            "action": laneswap_message.get("action", ""),
            "parameters": laneswap_message.get("params", {}),
            "timestamp": laneswap_message.get("timestamp", "")
        }
        
        return external_command
    
    def _translate_to_laneswap_format(self, external_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translate an external system response to LaneSwap format.
        
        Args:
            external_response: The response from the external system
            
        Returns:
            The translated response in LaneSwap format
        """
        # This is a simplified example. In a real implementation, you would
        # have more complex translation logic based on your external system's API.
        
        laneswap_response = {
            "status": "success" if external_response.get("status") == "success" else "error",
            "id": external_response.get("command_id", ""),
            "result": external_response.get("result", ""),
            "timestamp": external_response.get("timestamp", "")
        }
        
        return laneswap_response


async def main():
    """Main function to demonstrate the custom adapter."""
    # Create and initialize the custom adapter
    adapter_config = {
        "connection_string": "custom://localhost:9000",
        "timeout": 30,
        "retry_attempts": 3
    }
    
    adapter = CustomAdapter(adapter_config)
    
    # Initialize the LaneSwap client
    client = LaneSwapClient(
        api_url="http://localhost:8000",
        api_key="your-api-key",  # Replace with your actual API key
        service_name="custom-adapter-example",
        service_type=ServiceType.ADAPTER
    )
    
    # Connect the client to LaneSwap
    await client.connect()
    logger.info("Connected to LaneSwap network")
    
    try:
        # Register the adapter as a service
        service_config = ServiceConfig(
            name="custom-external-adapter",
            type=ServiceType.ADAPTER,
            description="Custom adapter for connecting to an external system",
            config=adapter_config
        )
        
        service_id = await client.register_service(service_config)
        logger.info(f"Registered adapter as service with ID: {service_id}")
        
        # Connect the adapter to the external system
        await adapter.connect()
        
        # Set up an event handler for the adapter's events
        async def handle_adapter_event(event):
            logger.info(f"Received event from adapter: {event}")
            # In a real implementation, you might forward this to other services
            # or take some action based on the event
        
        # Register the event handler with the client
        await client.subscribe(service_id, handle_adapter_event)
        
        # Simulate sending a message to the adapter
        test_message = Message(
            source="test-client",
            destination=service_id,
            content={
                "id": "msg-001",
                "action": "get_status",
                "params": {"device_id": "dev-123"},
                "timestamp": "2023-09-01T12:25:00Z"
            }
        )
        
        # Process the message through the adapter
        response = await adapter.handle_message(test_message)
        logger.info(f"Received response from adapter: {response}")
        
        # Simulate an event from the external system
        await adapter.external_client.simulate_event(
            "status_update",
            {
                "status": "online",
                "timestamp": "2023-09-01T12:35:00Z",
                "details": {
                    "cpu": 25,
                    "memory": 150,
                    "connections": 5
                }
            }
        )
        
        # Wait a moment to see the events
        await asyncio.sleep(2)
        
        # Simulate an alert from the external system
        await adapter.external_client.simulate_event(
            "alert",
            {
                "severity": "warning",
                "timestamp": "2023-09-01T12:36:00Z",
                "message": "High CPU usage detected",
                "data": {
                    "cpu": 85,
                    "threshold": 80
                }
            }
        )
        
        # Wait a moment to see the events
        await asyncio.sleep(2)
        
    except Exception as e:
        logger.error(f"Error during adapter operations: {e}")
    
    finally:
        # Clean up
        await adapter.disconnect()
        await client.deregister_service(service_id)
        await client.disconnect()
        logger.info("Cleaned up and disconnected")

if __name__ == "__main__":
    asyncio.run(main()) 