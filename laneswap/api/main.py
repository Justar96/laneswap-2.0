from typing import Dict, Any, Optional, List
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from ..core.heartbeat import HeartbeatManager, get_manager
from ..adapters.discord import DiscordWebhookAdapter
from ..adapters.mongodb import MongoDBAdapter
from .routers import health_check, heartbeat
from .middleware.error_handler import add_error_handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("laneswap")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for application startup and shutdown events."""
    # Initialize MongoDB adapter if connection string is provided
    mongodb_url = os.getenv("MONGODB_URL")
    mongodb_adapter = None
    
    if mongodb_url:
        logger.info("Initializing MongoDB adapter")
        mongodb_adapter = MongoDBAdapter(
            connection_string=mongodb_url,
            database_name=os.getenv("MONGODB_DATABASE", "laneswap")
        )
        await mongodb_adapter.connect()
    
    # Initialize Discord webhook if URL is provided
    discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    discord_adapter = None
    
    if discord_webhook_url:
        logger.info("Initializing Discord webhook adapter")
        discord_adapter = DiscordWebhookAdapter(
            webhook_url=discord_webhook_url,
            username=os.getenv("DISCORD_WEBHOOK_USERNAME", "Laneswap Heartbeat Monitor")
        )
    
    # Initialize heartbeat manager
    notifiers = [adapter for adapter in [discord_adapter] if adapter is not None]
    
    heartbeat_manager = get_manager()
    heartbeat_manager.notifiers = notifiers
    heartbeat_manager.storage = mongodb_adapter
    heartbeat_manager.check_interval = int(os.getenv("HEARTBEAT_CHECK_INTERVAL", "30"))
    heartbeat_manager.stale_threshold = int(os.getenv("HEARTBEAT_STALE_THRESHOLD", "60"))
    
    # Start monitoring task
    heartbeat_manager.start_monitor()
    
    logger.info("Laneswap API initialized and ready")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down Laneswap API")
    await heartbeat_manager.stop_monitor()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Laneswap Heartbeat API",
        description="A heartbeat monitoring system for services",
        version="0.1.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add error handlers
    add_error_handlers(app)
    
    # Include routers
    app.include_router(health_check.router, prefix="/api", tags=["health"])
    app.include_router(heartbeat.router, prefix="/api", tags=["heartbeat"])
    
    return app


# Create the FastAPI application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "laneswap.api.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("DEBUG", "false").lower() == "true"
    )