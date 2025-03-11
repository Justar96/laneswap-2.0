#!/usr/bin/env python
"""
Test module for LaneSwap Discord webhook functionality.

This module tests:
1. Discord webhook adapter initialization
2. Service-specific webhook configuration
3. Sending notifications with different levels
4. Status change notifications
"""

import asyncio
import argparse
import logging
import sys
import time
from datetime import datetime

from laneswap.core.heartbeat import (
    HeartbeatStatus, register_service, send_heartbeat, 
    get_service, initialize, stop_monitor
)
from laneswap.adapters.discord import DiscordWebhookAdapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("discord_test")


async def test_discord_adapter(webhook_url):
    """Test the Discord webhook adapter directly."""
    print("\n=== Testing Discord Webhook Adapter ===\n")
    
    # Initialize the adapter
    adapter = DiscordWebhookAdapter(webhook_url=webhook_url)
    
    # Test sending a basic notification
    print("Sending test notification...")
    success = await adapter.send_notification(
        title="Discord Adapter Test",
        message="This is a test notification from LaneSwap test_discord.py",
        level="info"
    )
    
    if success:
        print("✅ Basic notification sent successfully")
    else:
        print("❌ Failed to send basic notification")
        return False
    
    # Test sending notifications with different levels
    levels = ["info", "success", "warning", "error"]
    for level in levels:
        print(f"Sending {level} notification...")
        success = await adapter.send_notification(
            title=f"Discord {level.capitalize()} Test",
            message=f"This is a test {level} notification from LaneSwap",
            level=level
        )
        
        if success:
            print(f"✅ {level.capitalize()} notification sent successfully")
        else:
            print(f"❌ Failed to send {level} notification")
            return False
        
        # Brief pause between notifications
        await asyncio.sleep(1)
    
    print("✅ All direct adapter tests passed")
    return True


async def test_service_notifications(webhook_url):
    """Test service-specific notifications."""
    print("\n=== Testing Service-Specific Notifications ===\n")
    
    # Initialize the adapter
    adapter = DiscordWebhookAdapter(webhook_url=webhook_url)
    
    try:
        # Initialize the heartbeat system with the adapter
        await initialize(notifiers=[adapter])
        
        # Register a test service
        service_name = "Discord Test Service"
        service_id = await register_service(
            service_name=service_name,
            metadata={
                "test": True,
                "type": "discord_test",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        print(f"✅ Registered service: {service_name} (ID: {service_id})")
        
        # Configure service-specific webhook
        adapter.register_service_webhook(
            service_id=service_id,
            webhook_url=webhook_url,
            username="Discord Test Bot",
            notification_levels=["info", "warning", "error"]
        )
        
        print("✅ Configured service-specific webhook")
        
        # Send heartbeats with different statuses
        await send_heartbeat(
            service_id=service_id,
            status=HeartbeatStatus.HEALTHY,
            message="Service is running normally"
        )
        print("✅ Sent heartbeat with healthy status")
        
        await asyncio.sleep(1)
        
        await send_heartbeat(
            service_id=service_id,
            status=HeartbeatStatus.WARNING,
            message="High resource usage detected"
        )
        print("✅ Sent heartbeat with warning status")
        
        await asyncio.sleep(1)
        
        await send_heartbeat(
            service_id=service_id,
            status=HeartbeatStatus.ERROR,
            message="Service encountered an error"
        )
        print("✅ Sent heartbeat with error status")
        
        await asyncio.sleep(1)
        
        # Send a direct notification
        await adapter.send_notification(
            title="Test Direct Notification",
            message="This is a test notification sent directly via the adapter",
            service_info={"id": service_id, "name": service_name},
            level="info"
        )
        
        print("✅ Sent direct notification")
        
        print("✅ All service notification tests passed")
        return True
    except Exception as e:
        print(f"❌ Error during service notification tests: {str(e)}")
        return False
    finally:
        # Clean up resources
        try:
            await stop_monitor()
        except Exception as e:
            print(f"Warning: Error during cleanup: {str(e)}")


async def main_async(webhook_url):
    """Run all Discord webhook tests."""
    try:
        # Test the Discord adapter directly
        adapter_ok = await test_discord_adapter(webhook_url)
        
        # Test service notifications
        service_ok = False
        if adapter_ok:
            service_ok = await test_service_notifications(webhook_url)
        
        return adapter_ok and service_ok
    except Exception as e:
        print(f"❌ Error during tests: {str(e)}")
        return False
    finally:
        # Ensure heartbeat monitor is stopped
        try:
            await stop_monitor()
        except Exception as e:
            print(f"Warning: Error during final cleanup: {str(e)}")


def main():
    """Main entry point for the Discord webhook tests."""
    parser = argparse.ArgumentParser(description="Test LaneSwap Discord webhook functionality")
    parser.add_argument("--webhook-url", required=True, help="Discord webhook URL for testing")
    
    try:
        args = parser.parse_args()
        
        if not args.webhook_url:
            print("Error: Discord webhook URL is required")
            return 1
        
        print("Testing LaneSwap Discord webhook functionality...")
        
        success = asyncio.run(main_async(args.webhook_url))
        
        if success:
            print("\n✅ All Discord webhook tests passed!")
            return 0
        else:
            print("\n❌ Some Discord webhook tests failed.")
            return 1
    except SystemExit as e:
        # Handle the case where argparse exits due to --help or error
        if e.code == 0:  # --help was called
            return 0
        print("\n❌ Error parsing arguments")
        return 1
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error during tests: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 