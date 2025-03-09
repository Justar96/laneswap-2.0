from typing import Dict, Any, Optional, List
import os
import logging
from functools import lru_cache
from pydantic import BaseModel, Field, validator

# Configure logging
logger = logging.getLogger("laneswap")


class MongoDBSettings(BaseModel):
    """MongoDB connection settings."""
    connection_string: str = Field(..., description="MongoDB connection string")
    database_name: str = Field("laneswap", description="Database name")
    heartbeats_collection: str = Field("heartbeats", description="Heartbeats collection name")
    errors_collection: str = Field("errors", description="Errors collection name")
    
    @validator("connection_string")
    def validate_connection_string(cls, v):
        if not v or not v.startswith(("mongodb://", "mongodb+srv://")):
            raise ValueError("Invalid MongoDB connection string format")
        return v


class DiscordSettings(BaseModel):
    """Discord webhook settings."""
    webhook_url: str = Field(..., description="Discord webhook URL")
    username: str = Field("Laneswap Heartbeat Monitor", description="Webhook username")
    avatar_url: Optional[str] = Field(None, description="Webhook avatar URL")
    
    @validator("webhook_url")
    def validate_webhook_url(cls, v):
        if not v or not v.startswith(("https://discord.com/api/webhooks/", "https://discordapp.com/api/webhooks/")):
            raise ValueError("Invalid Discord webhook URL format")
        return v


class HeartbeatSettings(BaseModel):
    """Heartbeat monitoring settings."""
    check_interval: int = Field(30, description="Interval in seconds to check for stale heartbeats")
    stale_threshold: int = Field(60, description="Time in seconds after which a heartbeat is considered stale")
    
    @validator("check_interval", "stale_threshold")
    def validate_positive_int(cls, v, field):
        if v <= 0:
            raise ValueError(f"{field.name} must be a positive integer")
        return v


class APISettings(BaseModel):
    """API server settings."""
    host: str = Field("0.0.0.0", description="API server host")
    port: int = Field(8000, description="API server port")
    debug: bool = Field(False, description="Enable debug mode")
    cors_origins: List[str] = Field(["*"], description="Allowed CORS origins")


class Settings(BaseModel):
    """Global application settings."""
    mongodb: Optional[MongoDBSettings] = None
    discord: Optional[DiscordSettings] = None
    heartbeat: HeartbeatSettings = Field(default_factory=HeartbeatSettings)
    api: APISettings = Field(default_factory=APISettings)
    log_level: str = Field("INFO", description="Logging level")
    
    class Config:
        env_prefix = "LANESWAP_"


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings, with environment variable overrides.
    
    Returns:
        Settings: Application settings
    """
    # Load settings from environment variables
    mongodb_settings = None
    if os.getenv("MONGODB_URL"):
        mongodb_settings = MongoDBSettings(
            connection_string=os.getenv("MONGODB_URL"),
            database_name=os.getenv("MONGODB_DATABASE", "laneswap"),
            heartbeats_collection=os.getenv("MONGODB_HEARTBEATS_COLLECTION", "heartbeats"),
            errors_collection=os.getenv("MONGODB_ERRORS_COLLECTION", "errors")
        )
        
    discord_settings = None
    if os.getenv("DISCORD_WEBHOOK_URL"):
        discord_settings = DiscordSettings(
            webhook_url=os.getenv("DISCORD_WEBHOOK_URL"),
            username=os.getenv("DISCORD_WEBHOOK_USERNAME", "Laneswap Heartbeat Monitor"),
            avatar_url=os.getenv("DISCORD_WEBHOOK_AVATAR_URL")
        )
        
    heartbeat_settings = HeartbeatSettings(
        check_interval=int(os.getenv("HEARTBEAT_CHECK_INTERVAL", "30")),
        stale_threshold=int(os.getenv("HEARTBEAT_STALE_THRESHOLD", "60"))
    )
    
    api_settings = APISettings(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        debug=os.getenv("DEBUG", "false").lower() == "true",
        cors_origins=os.getenv("CORS_ORIGINS", "*").split(",")
    )
    
    return Settings(
        mongodb=mongodb_settings,
        discord=discord_settings,
        heartbeat=heartbeat_settings,
        api=api_settings,
        log_level=os.getenv("LOG_LEVEL", "INFO")
    )


def setup_logging(log_level: str = "INFO") -> None:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (INFO, DEBUG, etc.)
    """
    log_level_upper = log_level.upper()
    numeric_level = getattr(logging, log_level_upper, logging.INFO)
    
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )