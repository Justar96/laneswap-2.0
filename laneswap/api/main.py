from typing import Dict, Any, Optional, List
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from ..core.heartbeat import HeartbeatManager, get_manager
from ..core.config import setup_logging, get_settings, configure
from ..adapters.discord import DiscordWebhookAdapter
from ..adapters.mongodb import MongoDBAdapter
from .routers import health_check, heartbeat, progress

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("laneswap")

# Get the default heartbeat manager
manager = get_manager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Setup logging
    setup_logging()
    
    # Get the manager
    logger.debug("Getting heartbeat manager")
    mgr = get_manager()
    if mgr is None:
        logger.error("Failed to get heartbeat manager - creating new instance")
        from ..core.heartbeat import HeartbeatManager
        global manager
        manager = HeartbeatManager()
    else:
        logger.debug("Heartbeat manager retrieved successfully")
    
    # Get settings
    settings = get_settings()
    
    # Configure MongoDB storage if URL is provided
    if settings.mongodb:
        logger.info("Configuring MongoDB storage")
        mongodb = MongoDBAdapter(
            connection_string=settings.mongodb.connection_string,
            database_name=settings.mongodb.database_name,
            heartbeats_collection=settings.mongodb.heartbeats_collection,
            errors_collection=settings.mongodb.errors_collection
        )
        
        # Initialize MongoDB connection
        try:
            await mongodb.initialize()
            logger.info("MongoDB connection initialized")
            
            # Add MongoDB adapter to manager
            manager.add_storage_adapter(mongodb)
            logger.info("MongoDB adapter added to manager")
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB connection: {str(e)}")
    
    # Configure Discord webhook if URL is provided
    if settings.discord:
        logger.info("Configuring Discord webhook")
        discord = DiscordWebhookAdapter(
            webhook_url=settings.discord.webhook_url,
            username=settings.discord.username,
            avatar_url=settings.discord.avatar_url
        )
        
        # Add Discord adapter to manager
        manager.add_notifier_adapter(discord)
        logger.info("Discord adapter added to manager")
    
    # Start the heartbeat monitor
    logger.info("Starting heartbeat monitor")
    await manager.start_monitor(
        check_interval=settings.heartbeat.check_interval,
        stale_threshold=settings.heartbeat.stale_threshold
    )
    logger.info("Heartbeat monitor started")
    
    # Yield control back to FastAPI
    yield
    
    # Shutdown the heartbeat monitor
    logger.info("Stopping heartbeat monitor")
    await manager.stop_monitor()
    logger.info("Heartbeat monitor stopped")
    
    # Close MongoDB connection if it was initialized
    if settings.mongodb and hasattr(mongodb, 'close'):
        logger.info("Closing MongoDB connection")
        await mongodb.close()
        logger.info("MongoDB connection closed")

def add_error_handlers(app: FastAPI):
    """Add global error handlers to the FastAPI application."""
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler for all unhandled exceptions."""
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Get settings
    settings = get_settings()
    
    # Create FastAPI app
    app = FastAPI(
        title="LaneSwap API",
        description="API for LaneSwap heartbeat monitoring",
        version="0.1.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add error handlers
    add_error_handlers(app)
    
    # Include routers
    app.include_router(health_check.router, prefix="/api", tags=["health"])
    app.include_router(heartbeat.router, prefix="/api", tags=["heartbeat"])
    app.include_router(progress.router, prefix="/api", tags=["progress"])
    
    # Add OpenAPI servers
    if settings.api.host and settings.api.port:
        app.servers = get_server_urls(settings.api.host, settings.api.port)
    
    return app

def get_server_urls(host: str, port: int) -> Dict[str, Dict[str, str]]:
    """
    Generate server URLs for OpenAPI documentation.
    
    Args:
        host: Server host
        port: Server port
        
    Returns:
        Dict[str, Dict[str, str]]: Server URLs
    """
    # If host is 0.0.0.0, use localhost for documentation
    doc_host = "localhost" if host == "0.0.0.0" else host
    
    return {
        f"http://{doc_host}:{port}": {
            "api": f"http://{doc_host}:{port}/api",
            "docs": f"http://{doc_host}:{port}/docs",
            "web_monitor": f"http://{doc_host}:{port}/web-monitor"
        }
    }

# Create the FastAPI app
app = create_app()

# Programmatic configuration example
def configure_api(config_dict: Dict[str, Any] = None):
    """
    Configure the API with the provided configuration dictionary.
    
    Args:
        config_dict: Dictionary containing configuration values
    """
    # Configure the application
    configure(config_dict)
    
    # Recreate the FastAPI app
    global app
    app = create_app()
    
    return app

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    # Generate and display URLs
    urls = get_server_urls(host, port)
    
    print("\n" + "=" * 50)
    print("LaneSwap Server is starting...")
    print("=" * 50)
    
    for base_url, endpoints in urls.items():
        print(f"\nAccess points for {base_url}:")
        print(f"  API Endpoint: {endpoints['api']}")
        print(f"  API Documentation: {endpoints['docs']}")
        print(f"  Web Monitor: {endpoints['web_monitor']}")
    
    print("\n" + "=" * 50)
    
    # Start the server
    uvicorn.run(
        "laneswap.api.main:app",
        host=host,
        port=port,
        reload=debug
    )