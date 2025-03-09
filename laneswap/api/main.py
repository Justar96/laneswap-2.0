from typing import Dict, Any, Optional, List
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..core.heartbeat import HeartbeatManager, get_manager
from ..core.config import setup_logging
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
    
    # Configure MongoDB storage if URL is provided
    mongodb_url = os.getenv("MONGODB_URL")
    if mongodb_url:
        logger.info("Configuring MongoDB storage")
        mongodb = MongoDBAdapter(
            connection_string=mongodb_url,
            database_name=os.getenv("MONGODB_DATABASE", "laneswap")
        )
        manager.storage = mongodb
    
    # Configure Discord webhook if URL is provided
    discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if discord_webhook_url:
        logger.info("Configuring Discord webhook notifications")
        discord = DiscordWebhookAdapter(
            webhook_url=discord_webhook_url,
            username=os.getenv("DISCORD_WEBHOOK_USERNAME", "LaneSwap Monitor")
        )
        manager.notifiers.append(discord)
    
    # Start the heartbeat monitor
    logger.debug("Starting heartbeat monitor")
    try:
        await manager.start_monitor()
        logger.info("Heartbeat monitor started")
    except Exception as e:
        logger.error(f"Failed to start heartbeat monitor: {str(e)}")
        # Continue without the monitor
    
    yield
    
    # Stop the heartbeat monitor
    try:
        if manager.monitor_task:
            await manager.stop_monitor()
            logger.info("Heartbeat monitor stopped")
    except Exception as e:
        logger.error(f"Error stopping heartbeat monitor: {str(e)}")


def add_error_handlers(app: FastAPI):
    """Add global error handlers to the FastAPI application."""
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "type": str(type(exc).__name__)}
        )


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Laneswap Heartbeat API",
        description="""
        A heartbeat monitoring system for distributed services.
        
        ## Features
        
        * Register services for monitoring
        * Send heartbeats to update service status
        * Get status information for services
        * Receive notifications when service status changes
        
        ## Example Usage
        
        ```python
        import requests
        
        # Register a service
        response = requests.post(
            "http://localhost:8000/api/services",
            json={
                "service_name": "My Service",
                "metadata": {"version": "1.0.0"}
            }
        )
        service_id = response.json()["service_id"]
        
        # Send a heartbeat
        requests.post(
            f"http://localhost:8000/api/services/{service_id}/heartbeat",
            json={
                "status": "healthy",
                "message": "Service running normally"
            }
        )
        ```
        """,
        version="0.1.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware with more permissive settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for testing
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Type", "X-Process-Time"],
    )
    
    # Add error handlers
    add_error_handlers(app)
    
    # Include routers
    app.include_router(health_check.router, prefix="/api", tags=["health"])
    app.include_router(heartbeat.router, prefix="/api", tags=["heartbeat"])
    app.include_router(progress.router, prefix="/api/progress", tags=["progress"])
    
    return app


# Create the FastAPI application
app = create_app()


def get_server_urls(host: str, port: int) -> Dict[str, Dict[str, str]]:
    """Generate URLs for accessing the server."""
    # Determine if we're using localhost or a specific IP
    is_localhost = host == "0.0.0.0" or host == "::" or host == "0:0:0:0:0:0:0:0"
    
    # Generate base URLs
    if is_localhost:
        base_urls = [
            f"http://localhost:{port}",
            f"http://127.0.0.1:{port}"
        ]
        
        # Try to get the machine's local IP address
        try:
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            if local_ip and local_ip not in ["127.0.0.1", "::1"]:
                base_urls.append(f"http://{local_ip}:{port}")
        except Exception:
            pass
    else:
        base_urls = [f"http://{host}:{port}"]
    
    # Generate specific URLs
    urls = {}
    for base_url in base_urls:
        urls[base_url] = {
            "api": f"{base_url}/api/services",
            "docs": f"{base_url}/docs",
            "web_monitor": f"file://{os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'examples', 'web_monitor', 'index.html'))}"
        }
    
    return urls


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