"""
FastAPI application for the LaneSwap service.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import health_check, heartbeat

app = FastAPI(
    title="LaneSwap API",
    description="API for service heartbeat monitoring and health checks",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with prefix
app.include_router(heartbeat.router, prefix="/api", tags=["heartbeat"])
app.include_router(health_check.router, prefix="/api", tags=["health"])

# Root endpoint
@app.get("/api")
async def root():
    """Root endpoint that returns basic API information."""
    return {
        "name": "LaneSwap API",
        "version": "2.0.0",
        "status": "operational"
    }
