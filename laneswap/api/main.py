import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import os

# Import the new LaneSwap facade and necessary types/exceptions
from ..laneswap import LaneSwap
from ..core.types import HeartbeatStatus # Keep if needed by routes directly
from ..core.exceptions import ServiceNotFoundError # Keep if handled here
from ..core.config import get_settings, setup_logging # Keep settings import
from .routers import health_check, heartbeat, progress

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("laneswap")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events using the LaneSwap facade.
    """
    # Setup logging
    setup_logging()
    logger.info("API Lifespan starting...")

    # Get settings
    settings = get_settings()

    # Prepare adapter specifications from settings
    storage_spec = None
    if settings.mongodb:
        storage_spec = settings.mongodb.connection_string # Pass URI directly
        # Alternatively, construct URI if settings are separate fields:
        # storage_spec = f"mongodb://{settings.mongodb.host}:{settings.mongodb.port}/{settings.mongodb.database_name}"

    notifier_specs = []
    if settings.discord:
        # Assuming webhook_url is the connection string
        notifier_specs.append(settings.discord.webhook_url)
        # Add other notifiers if configured...

    # Instantiate the LaneSwap facade
    try:
        laneswap_instance = LaneSwap(
            storage=storage_spec,
            notifiers=notifier_specs,
            check_interval=settings.heartbeat.check_interval,
            stale_threshold=settings.heartbeat.stale_threshold
        )
        # Store the instance in app state for dependency injection in routes
        app.state.laneswap = laneswap_instance
        logger.info("LaneSwap instance created and stored in app state.")

        # Start the LaneSwap monitor
        await laneswap_instance.start()
        logger.info("LaneSwap monitor started via lifespan.")

    except Exception as e:
        logger.critical(f"Failed to initialize LaneSwap in API lifespan: {e}", exc_info=True)
        # Prevent the app from starting if core system fails
        app.state.laneswap = None # Ensure state is None if failed
        # Optionally raise the exception to halt FastAPI startup
        raise RuntimeError(f"LaneSwap initialization failed: {e}") from e

    # Yield control back to FastAPI
    yield

    # --- Shutdown Phase ---
    logger.info("API Lifespan shutting down...")
    laneswap_instance = getattr(app.state, 'laneswap', None)
    if laneswap_instance:
        # Stop the LaneSwap monitor
        try:
            await laneswap_instance.stop()
            logger.info("LaneSwap monitor stopped via lifespan.")
        except Exception as e:
             logger.error(f"Error stopping LaneSwap monitor: {e}", exc_info=True)
    else:
        logger.warning("No LaneSwap instance found in app state during shutdown.")

def add_error_handlers(app: FastAPI):
    """Add global error handlers to the FastAPI application."""

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler for all unhandled exceptions."""
        logger.error("Unhandled exception: %s", str(exc), exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Get settings
    settings = get_settings()

    # Create FastAPI app with the new lifespan
    app = FastAPI(
        title="LaneSwap API",
        description="API for LaneSwap heartbeat monitoring",
        version="0.2.0", # Reflect version bump
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
        }
    }

# Create the FastAPI app
app = create_app()

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

    print("\n" + "=" * 50)

    # Start the server
    uvicorn.run(
        "laneswap.api.main:app",
        host=host,
        port=port,
        reload=debug
    )
