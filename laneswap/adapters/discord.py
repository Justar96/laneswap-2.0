from typing import Dict, Any, Optional, List
import logging
import aiohttp
from datetime import datetime

from .base import NotifierAdapter
from ..models.heartbeat import HeartbeatStatus

logger = logging.getLogger("laneswap")


class DiscordWebhookAdapter(NotifierAdapter):
    """Discord webhook adapter for sending notifications."""
    
    def __init__(
        self,
        webhook_url: str,
        username: Optional[str] = "Laneswap Heartbeat Monitor",
        avatar_url: Optional[str] = None
    ):
        """
        Initialize the Discord webhook adapter.
        
        Args:
            webhook_url: Discord webhook URL
            username: Display name for the webhook
            avatar_url: Avatar image URL for the webhook
        """
        self.webhook_url = webhook_url
        self.username = username
        self.avatar_url = avatar_url
        
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
        if not self.webhook_url:
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
            "timestamp": datetime.utcnow().isoformat(),
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
            "username": self.username,
            "embeds": [embed]
        }
        
        if self.avatar_url:
            payload["avatar_url"] = self.avatar_url
            
        # Send webhook request
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
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