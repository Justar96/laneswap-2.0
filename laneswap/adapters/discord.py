from typing import Dict, Any, Optional, List
import logging
import aiohttp
from datetime import datetime, UTC

from .base import NotifierAdapter
from ..models.heartbeat import HeartbeatStatus

logger = logging.getLogger("laneswap")


class DiscordWebhookAdapter(NotifierAdapter):
    """Discord webhook adapter for sending notifications."""
    
    def __init__(
        self,
        webhook_url: str = None,
        username: Optional[str] = "Laneswap Heartbeat Monitor",
        avatar_url: Optional[str] = None
    ):
        """
        Initialize the Discord webhook adapter.
        
        Args:
            webhook_url: Default Discord webhook URL
            username: Display name for the webhook
            avatar_url: Avatar image URL for the webhook
        """
        self.webhook_url = webhook_url
        self.username = username
        self.avatar_url = avatar_url
        # Dictionary to store service-specific webhook configurations
        self.service_webhooks: Dict[str, Dict[str, Any]] = {}
        
    def register_service_webhook(
        self,
        service_id: str,
        webhook_url: str,
        username: Optional[str] = None,
        avatar_url: Optional[str] = None,
        notification_levels: Optional[List[str]] = None
    ) -> None:
        """
        Register a webhook configuration for a specific service.
        
        Args:
            service_id: Service identifier
            webhook_url: Discord webhook URL for this service
            username: Display name for the webhook (defaults to adapter's username)
            avatar_url: Avatar image URL for the webhook (defaults to adapter's avatar_url)
            notification_levels: List of levels to notify for (defaults to all: info, success, warning, error)
        """
        self.service_webhooks[service_id] = {
            "webhook_url": webhook_url,
            "username": username or self.username,
            "avatar_url": avatar_url or self.avatar_url,
            "notification_levels": notification_levels or ["info", "success", "warning", "error"]
        }
        logger.info(f"Registered Discord webhook for service {service_id}")
        
    def remove_service_webhook(self, service_id: str) -> bool:
        """
        Remove a service-specific webhook configuration.
        
        Args:
            service_id: Service identifier
            
        Returns:
            bool: True if the webhook was removed, False if it didn't exist
        """
        if service_id in self.service_webhooks:
            del self.service_webhooks[service_id]
            logger.info(f"Removed Discord webhook for service {service_id}")
            return True
        return False
        
    def get_service_webhook_config(self, service_id: str) -> Optional[Dict[str, Any]]:
        """
        Get webhook configuration for a specific service.
        
        Args:
            service_id: Service identifier
            
        Returns:
            Optional[Dict[str, Any]]: Webhook configuration or None if not found
        """
        return self.service_webhooks.get(service_id)
        
    def list_service_webhooks(self) -> Dict[str, Dict[str, Any]]:
        """
        List all service-specific webhook configurations.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary mapping service IDs to webhook configurations
        """
        return self.service_webhooks
        
    async def send_notification(
        self,
        title: str,
        message: str,
        service_info: Optional[Dict[str, Any]] = None,
        level: str = "info"
    ) -> bool:
        """
        Send a notification via Discord webhook.
        
        Args:
            title: Notification title
            message: Message body
            service_info: Additional service information
            level: Notification level (info, warning, error)
            
        Returns:
            bool: True if notification was sent successfully
        """
        # Determine which webhook URL to use
        webhook_url = self.webhook_url
        username = self.username
        avatar_url = self.avatar_url
        
        # If service_info is provided and has an ID, check for service-specific webhook
        if service_info and "id" in service_info:
            service_id = service_info["id"]
            service_config = self.service_webhooks.get(service_id)
            
            if service_config:
                # Check if this notification level should be sent for this service
                if level.lower() not in service_config.get("notification_levels", []):
                    logger.debug(f"Skipping {level} notification for service {service_id} (not in notification levels)")
                    return True  # Return True as this is an intentional skip
                    
                webhook_url = service_config["webhook_url"]
                username = service_config.get("username", self.username)
                avatar_url = service_config.get("avatar_url", self.avatar_url)
        
        if not webhook_url:
            logger.error("Discord webhook URL not provided")
            return False
            
        # Map notification level to Discord embed color
        colors = {
            "info": 0x3498db,     # Blue
            "success": 0x2ecc71,  # Green
            "warning": 0xf39c12,  # Orange
            "error": 0xe74c3c     # Red
        }
        color = colors.get(level.lower(), colors["info"])
        
        # Create Discord embed
        embed = {
            "title": title,
            "description": message,
            "color": color,
            "timestamp": datetime.now(UTC).isoformat(),
            "fields": []
        }
        
        # Add service info if provided
        if service_info:
            service_name = service_info.get("name", "Unknown Service")
            service_status = service_info.get("status", "unknown")
            
            # Add status field
            embed["fields"].append({
                "name": "Service Name",
                "value": service_name,
                "inline": True
            })
            
            embed["fields"].append({
                "name": "Status",
                "value": service_status,
                "inline": True
            })
            
            # Add last heartbeat timestamp if available
            if "last_heartbeat" in service_info and service_info["last_heartbeat"]:
                last_heartbeat = service_info["last_heartbeat"]
                if isinstance(last_heartbeat, datetime):
                    last_heartbeat_str = last_heartbeat.strftime("%Y-%m-%d %H:%M:%S UTC")
                else:
                    last_heartbeat_str = str(last_heartbeat)
                    
                embed["fields"].append({
                    "name": "Last Heartbeat",
                    "value": last_heartbeat_str,
                    "inline": True
                })
                
            # Add additional metadata if available
            if "metadata" in service_info and service_info["metadata"]:
                metadata = service_info["metadata"]
                if isinstance(metadata, dict):
                    metadata_str = "\n".join([f"**{k}**: {v}" for k, v in metadata.items()
                                             if k not in ("password", "token", "secret", "key")])
                    if metadata_str:
                        embed["fields"].append({
                            "name": "Metadata",
                            "value": metadata_str,
                            "inline": False
                        })
        
        # Prepare webhook payload
        payload = {
            "username": username,
            "embeds": [embed]
        }
        
        if avatar_url:
            payload["avatar_url"] = avatar_url
            
        # Send webhook request
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    timeout=10  # 10-second timeout
                ) as response:
                    success = 200 <= response.status < 300
                    
                    if not success:
                        response_text = await response.text()
                        logger.error(
                            f"Failed to send Discord notification. "
                            f"Status: {response.status}, Response: {response_text}"
                        )
                        
                    return success
        except Exception as e:
            logger.error(f"Error sending Discord notification: {str(e)}")
            return False