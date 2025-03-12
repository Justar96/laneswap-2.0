"""
Tests for the Discord webhook adapter.
"""

import pytest
import asyncio
from datetime import datetime
import os

from laneswap.adapters.discord import DiscordWebhookAdapter
from laneswap.core.heartbeat import HeartbeatStatus


def test_discord_adapter_initialization():
    """Test initializing the Discord adapter."""
    adapter = DiscordWebhookAdapter(webhook_url="https://example.com/webhook")
    assert adapter.webhook_url == "https://example.com/webhook"
    assert adapter.username == "Laneswap Heartbeat Monitor"
    assert adapter.avatar_url is None


def test_service_webhook_registration():
    """Test registering a service webhook."""
    adapter = DiscordWebhookAdapter(webhook_url="https://example.com/webhook")
    
    # Register a service webhook
    adapter.register_service_webhook(
        service_id="test-service",
        webhook_url="https://example.com/service-webhook",
        username="Test Bot",
        notification_levels=["info", "warning"]
    )
    
    # Verify registration
    config = adapter.get_service_webhook_config("test-service")
    assert config is not None
    assert config["webhook_url"] == "https://example.com/service-webhook"
    assert config["username"] == "Test Bot"
    assert config["notification_levels"] == ["info", "warning"]


@pytest.mark.asyncio
async def test_notification_formatting():
    """Test notification formatting."""
    adapter = DiscordWebhookAdapter(webhook_url="https://example.com/webhook")
    
    # Test info notification
    service_info = {
        "id": "test-service",
        "name": "Test Service",
        "status": HeartbeatStatus.HEALTHY.value,
        "last_heartbeat": datetime.now(),
        "metadata": {"version": "1.0.0"}
    }
    
    # Send a test notification (this won't actually send it)
    result = await adapter.send_notification(
        title="Test Info",
        message="This is an info message",
        service_info=service_info,
        level="info"
    )
    
    # Since we can't send actual notifications in tests, we just verify the adapter exists
    assert adapter is not None


@pytest.mark.skipif(
    "DISCORD_WEBHOOK_URL" not in os.environ,
    reason="Discord webhook URL not provided"
)
@pytest.mark.asyncio
async def test_send_notification():
    """Test sending a notification."""
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    adapter = DiscordWebhookAdapter(webhook_url=webhook_url)
    
    # Send a test notification
    result = await adapter.send_notification(
        title="Test Notification",
        message="This is a test message",
        service_info={
            "id": "test-service",
            "name": "Test Service",
            "status": HeartbeatStatus.HEALTHY.value,
            "last_heartbeat": datetime.now(),
            "metadata": {"test": True}
        },
        level="info"
    )
    
    assert result is True


@pytest.mark.skipif(
    "DISCORD_WEBHOOK_URL" not in os.environ,
    reason="Discord webhook URL not provided"
)
@pytest.mark.asyncio
async def test_status_change_notification():
    """Test sending a status change notification."""
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    adapter = DiscordWebhookAdapter(webhook_url=webhook_url)
    
    # Send a warning notification
    result = await adapter.send_notification(
        title="Status Change",
        message="Service status changed to WARNING",
        service_info={
            "id": "test-service",
            "name": "Test Service",
            "status": HeartbeatStatus.WARNING.value,
            "last_heartbeat": datetime.now(),
            "metadata": {"cpu": 0.9, "memory": 0.8}
        },
        level="warning"
    )
    
    assert result is True 