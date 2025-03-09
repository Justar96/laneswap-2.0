from typing import Dict, Any, Optional, List
import os
import logging
from functools import lru_cache
from pydantic import BaseModel, Field, validator, field_validator
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Configure logging
logger = logging.getLogger("laneswap")

# Add this to the configuration
MONITOR_URL = os.getenv("MONITOR_URL", "http://localhost:8080")

# API configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# MongoDB configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "laneswap")

# Discord webhook configuration
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
DISCORD_WEBHOOK_USERNAME = os.getenv("DISCORD_WEBHOOK_USERNAME", "LaneSwap Monitor")

# Heartbeat configuration
HEARTBEAT_CHECK_INTERVAL = int(os.getenv("HEARTBEAT_CHECK_INTERVAL", "30"))
HEARTBEAT_STALE_THRESHOLD = int(os.getenv("HEARTBEAT_STALE_THRESHOLD", "60"))

# URL configuration for client and web monitor
API_URL = os.getenv("API_URL", "http://localhost:8000")

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
    check_interval: int = 30  # seconds
    stale_threshold: int = 60  # seconds
    
    @field_validator('check_interval')
    @classmethod
    def validate_check_interval(cls, v: int) -> int:
        """Validate check_interval is positive."""
        if v <= 0:
            raise ValueError("check_interval must be positive")
        return v
    
    @field_validator('stale_threshold')
    @classmethod
    def validate_stale_threshold(cls, v: int) -> int:
        """Validate stale_threshold is positive."""
        if v <= 0:
            raise ValueError("stale_threshold must be positive")
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
        check_interval=parse_env_int("HEARTBEAT_CHECK_INTERVAL", 30),
        stale_threshold=parse_env_int("HEARTBEAT_STALE_THRESHOLD", 60)
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
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        force=True
    )
    
    # Set level for our logger
    logger.setLevel(numeric_level)
    
    logger.debug(f"Logging configured with level: {log_level_upper}")


def parse_env_int(name: str, default: int) -> int:
    """
    Parse an integer environment variable with proper error handling.
    
    Args:
        name: Name of the environment variable
        default: Default value if not found or invalid
        
    Returns:
        int: The parsed value or default
    """
    value = os.getenv(name)
    if value is None:
        return default
    
    # Strip any comments
    if '#' in value:
        value = value.split('#')[0].strip()
        
    try:
        return int(value)
    except ValueError:
        logger.warning(f"Invalid value for {name}: '{value}', using default: {default}")
        return default

# Get all configuration as a dictionary
def get_config() -> Dict[str, Any]:
    """Get all configuration as a dictionary."""
    return {
        "host": HOST,
        "port": PORT,
        "debug": DEBUG,
        "cors_origins": CORS_ORIGINS,
        "mongodb_url": MONGODB_URL,
        "mongodb_database": MONGODB_DATABASE,
        "discord_webhook_url": DISCORD_WEBHOOK_URL,
        "discord_webhook_username": DISCORD_WEBHOOK_USERNAME,
        "heartbeat_check_interval": HEARTBEAT_CHECK_INTERVAL,
        "heartbeat_stale_threshold": HEARTBEAT_STALE_THRESHOLD,
        "api_url": API_URL,
        "monitor_url": MONITOR_URL,
    }