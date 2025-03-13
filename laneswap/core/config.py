import logging
import os
from functools import lru_cache
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, validator

# Configure logging
logger = logging.getLogger("laneswap")

# Default configuration values
DEFAULT_CONFIG = {
    # API configuration
    "HOST": "0.0.0.0",
    "PORT": 8000,
    "DEBUG": False,
    "CORS_ORIGINS": ["*"],

    # MongoDB configuration
    "MONGODB_URL": os.getenv("LANESWAP_MONGODB_URI", "mongodb://localhost:27017"),
    "MONGODB_DATABASE": os.getenv("LANESWAP_MONGODB_NAME", "laneswap"),
    "MONGODB_HEARTBEATS_COLLECTION": "heartbeats",
    "MONGODB_ERRORS_COLLECTION": "errors",

    # Discord webhook configuration
    "DISCORD_WEBHOOK_URL": os.getenv("LANESWAP_DISCORD_WEBHOOK", ""),
    "DISCORD_WEBHOOK_USERNAME": "LaneSwap Monitor",
    "DISCORD_WEBHOOK_AVATAR_URL": None,

    # Heartbeat configuration
    "HEARTBEAT_CHECK_INTERVAL": int(os.getenv("LANESWAP_CHECK_INTERVAL", "30")),
    "HEARTBEAT_STALE_THRESHOLD": int(os.getenv("LANESWAP_STALE_THRESHOLD", "60")),

    # URL configuration for client and web monitor
    "API_URL": "http://localhost:8000",
    "MONITOR_URL": "http://localhost:8080",

    # Logging configuration
    "LOG_LEVEL": "INFO"
}

# Global configuration dictionary that can be modified programmatically
CONFIG = DEFAULT_CONFIG.copy()

# Expose common configuration values as module-level variables for backward compatibility
HOST = CONFIG["HOST"]
PORT = CONFIG["PORT"]
DEBUG = CONFIG["DEBUG"]
CORS_ORIGINS = CONFIG["CORS_ORIGINS"]
MONGODB_URL = CONFIG["MONGODB_URL"]
MONGODB_DATABASE = CONFIG["MONGODB_DATABASE"]
DISCORD_WEBHOOK_URL = CONFIG["DISCORD_WEBHOOK_URL"]
DISCORD_WEBHOOK_USERNAME = CONFIG["DISCORD_WEBHOOK_USERNAME"]
HEARTBEAT_CHECK_INTERVAL = CONFIG["HEARTBEAT_CHECK_INTERVAL"]
HEARTBEAT_STALE_THRESHOLD = CONFIG["HEARTBEAT_STALE_THRESHOLD"]
API_URL = CONFIG["API_URL"]
MONITOR_URL = CONFIG["MONITOR_URL"]


class MongoDBSettings(BaseModel):
    """MongoDB connection settings."""
    connection_string: str = Field(..., description="MongoDB connection string")
    database_name: str = Field("laneswap", description="Database name")
    heartbeats_collection: str = Field("heartbeats", description="Heartbeats collection name")
    errors_collection: str = Field("errors", description="Errors collection name")

    @field_validator("connection_string")
    @classmethod
    def validate_connection_string(cls, v: str) -> str:
        if not v or not v.startswith(("mongodb://", "mongodb+srv://")):
            raise ValueError("Invalid MongoDB connection string format")
        return v


class DiscordSettings(BaseModel):
    """Discord webhook settings."""
    webhook_url: str = Field(..., description="Discord webhook URL")
    username: str = Field("Laneswap Heartbeat Monitor", description="Webhook username")
    avatar_url: Optional[str] = Field(None, description="Webhook avatar URL")

    @field_validator("webhook_url")
    @classmethod
    def validate_webhook_url(cls, v: str) -> str:
        if v and not v.startswith(("https://discord.com/api/webhooks/", "https://discordapp.com/api/webhooks/")):
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
    api_url: str = Field("http://localhost:8000", description="API URL for clients")
    monitor_url: str = Field("http://localhost:8080", description="Web monitor URL")


class Settings(BaseModel):
    """Global application settings."""
    mongodb: Optional[MongoDBSettings] = None
    discord: Optional[DiscordSettings] = None
    heartbeat: HeartbeatSettings = Field(default_factory=HeartbeatSettings)
    api: APISettings = Field(default_factory=APISettings)
    log_level: str = Field("INFO", description="Logging level")


# Initialize settings cache
_settings_instance = None


def configure(config_dict: Dict[str, Any] = None, env_prefix: str = "LANESWAP_") -> None:
    """
    Configure the application with the provided configuration dictionary and/or environment variables.

    Args:
        config_dict: Dictionary containing configuration values
        env_prefix: Prefix for environment variables to consider
    """
    global CONFIG, _settings_instance
    global HOST, PORT, DEBUG, CORS_ORIGINS, MONGODB_URL, MONGODB_DATABASE
    global DISCORD_WEBHOOK_URL, DISCORD_WEBHOOK_USERNAME
    global HEARTBEAT_CHECK_INTERVAL, HEARTBEAT_STALE_THRESHOLD
    global API_URL, MONITOR_URL

    # Reset configuration to defaults
    CONFIG = DEFAULT_CONFIG.copy()

    # Update from environment variables if env_prefix is provided
    if env_prefix:
        for key in CONFIG.keys():
            env_var = f"{env_prefix}{key}"
            if env_var in os.environ:
                value = os.environ[env_var]

                # Convert to appropriate type
                if isinstance(CONFIG[key], bool):
                    CONFIG[key] = value.lower() in ("true", "1", "yes", "y")
                elif isinstance(CONFIG[key], int):
                    try:
                        CONFIG[key] = int(value)
                    except ValueError:
                        logger.warning("Invalid value for %s: '%s', using default: %s", env_var, value, CONFIG[key])
                elif isinstance(CONFIG[key], list):
                    CONFIG[key] = value.split(",")
                else:
                    CONFIG[key] = value

    # Update from provided configuration dictionary
    if config_dict:
        for key, value in config_dict.items():
            if key in CONFIG:
                CONFIG[key] = value

    # Update module-level variables for backward compatibility
    HOST = CONFIG["HOST"]
    PORT = CONFIG["PORT"]
    DEBUG = CONFIG["DEBUG"]
    CORS_ORIGINS = CONFIG["CORS_ORIGINS"]
    MONGODB_URL = CONFIG["MONGODB_URL"]
    MONGODB_DATABASE = CONFIG["MONGODB_DATABASE"]
    DISCORD_WEBHOOK_URL = CONFIG["DISCORD_WEBHOOK_URL"]
    DISCORD_WEBHOOK_USERNAME = CONFIG["DISCORD_WEBHOOK_USERNAME"]
    HEARTBEAT_CHECK_INTERVAL = CONFIG["HEARTBEAT_CHECK_INTERVAL"]
    HEARTBEAT_STALE_THRESHOLD = CONFIG["HEARTBEAT_STALE_THRESHOLD"]
    API_URL = CONFIG["API_URL"]
    MONITOR_URL = CONFIG["MONITOR_URL"]

    # Reset settings instance to force recreation with new config
    _settings_instance = None

    # Set up logging with the new configuration
    setup_logging(CONFIG["LOG_LEVEL"])

    logger.debug("Configuration updated: %s", CONFIG)


def get_settings() -> Settings:
    """
    Get application settings.

    Returns:
        Settings: Application settings
    """
    global _settings_instance

    if _settings_instance is None:
        # Create MongoDB settings if URL is provided
        mongodb_settings = None
        mongodb_url = os.getenv("LANESWAP_MONGODB_URI")
        if mongodb_url:
            mongodb_settings = MongoDBSettings(
                connection_string=mongodb_url,
                database_name=os.getenv("LANESWAP_MONGODB_NAME", "laneswap"),
                heartbeats_collection=CONFIG["MONGODB_HEARTBEATS_COLLECTION"],
                errors_collection=CONFIG["MONGODB_ERRORS_COLLECTION"]
            )

        # Create Discord settings if webhook URL is provided
        discord_settings = None
        discord_url = os.getenv("LANESWAP_DISCORD_WEBHOOK")
        if discord_url:
            discord_settings = DiscordSettings(
                webhook_url=discord_url,
                username=CONFIG["DISCORD_WEBHOOK_USERNAME"],
                avatar_url=CONFIG["DISCORD_WEBHOOK_AVATAR_URL"]
            )

        # Create heartbeat settings
        heartbeat_settings = HeartbeatSettings(
            check_interval=int(os.getenv("LANESWAP_CHECK_INTERVAL", "30")),
            stale_threshold=int(os.getenv("LANESWAP_STALE_THRESHOLD", "60"))
        )

        # Create API settings
        api_settings = APISettings(
            host=CONFIG["HOST"],
            port=CONFIG["PORT"],
            debug=CONFIG["DEBUG"],
            cors_origins=CONFIG["CORS_ORIGINS"],
            api_url=CONFIG["API_URL"],
            monitor_url=CONFIG["MONITOR_URL"]
        )

        # Create settings instance
        _settings_instance = Settings(
            mongodb=mongodb_settings,
            discord=discord_settings,
            heartbeat=heartbeat_settings,
            api=api_settings,
            log_level=CONFIG["LOG_LEVEL"]
        )

    return _settings_instance


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

    logger.debug("Logging configured with level: %s", log_level_upper)


def get_config() -> Dict[str, Any]:
    """Get all configuration as a dictionary."""
    return CONFIG.copy()


# Initialize configuration from environment variables
configure()
