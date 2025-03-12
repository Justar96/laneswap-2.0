#!/usr/bin/env python
"""
Mock API Server for LaneSwap Terminal Monitor Demo

This script provides a simple mock API server that returns fake service data
for demonstrating the terminal monitor without needing a full LaneSwap setup.

Usage:
    python -m laneswap.examples.mock_api_server
"""

import asyncio
import argparse
import logging
import json
import datetime
import random
import uuid
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("laneswap.examples.mock_api")

# Create FastAPI app
app = FastAPI(title="LaneSwap Mock API", version="0.1.2")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data
SERVICES: Dict[str, Dict[str, Any]] = {}

# Service statuses
STATUSES = ["healthy", "warning", "error", "unknown"]

# Service names
SERVICE_NAMES = [
    "auth-service", "user-service", "payment-service", "notification-service",
    "email-service", "search-service", "recommendation-service", "analytics-service",
    "logging-service", "cache-service", "database-service", "storage-service"
]

# Status messages
STATUS_MESSAGES = {
    "healthy": [
        "Service running normally",
        "All systems operational",
        "No issues detected",
        "Service is healthy",
        "Performance is optimal"
    ],
    "warning": [
        "High CPU usage",
        "Memory usage above threshold",
        "Slow response times",
        "Increased error rate",
        "Database connection pool near capacity"
    ],
    "error": [
        "Service is down",
        "Database connection failed",
        "Critical error in main process",
        "Out of memory",
        "Dependency service unavailable"
    ],
    "unknown": [
        "Status unknown",
        "Cannot determine status",
        "Monitoring data unavailable",
        "Service not responding to status checks"
    ]
}

def generate_mock_services(count: int = 10) -> None:
    """Generate mock service data."""
    global SERVICES
    SERVICES = {}
    
    for i in range(count):
        service_id = str(uuid.uuid4())
        status = random.choice(STATUSES)
        service_name = random.choice(SERVICE_NAMES) + f"-{i+1}"
        
        # Create service data
        SERVICES[service_id] = {
            "id": service_id,
            "name": service_name,
            "status": status,
            "created_at": (datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 30))).isoformat(),
            "last_heartbeat": (datetime.datetime.now() - datetime.timedelta(minutes=random.randint(0, 60))).isoformat(),
            "status_message": random.choice(STATUS_MESSAGES[status]),
            "metadata": {
                "version": f"1.{random.randint(0, 9)}.{random.randint(0, 9)}",
                "environment": random.choice(["production", "staging", "development"]),
                "region": random.choice(["us-east", "us-west", "eu-central", "ap-southeast"])
            }
        }

async def update_services_periodically():
    """Update service statuses periodically to simulate real-time changes."""
    while True:
        for service_id, service in SERVICES.items():
            # Randomly change status (10% chance)
            if random.random() < 0.1:
                new_status = random.choice(STATUSES)
                service["status"] = new_status
                service["status_message"] = random.choice(STATUS_MESSAGES[new_status])
                service["last_heartbeat"] = datetime.datetime.now().isoformat()
                logger.info(f"Updated service {service['name']} status to {new_status}")
        
        # Wait for next update
        await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    """Initialize mock data and start background tasks."""
    generate_mock_services(12)
    asyncio.create_task(update_services_periodically())
    logger.info("Mock API server started with sample data")

@app.get("/api/services")
async def get_services():
    """Get all services."""
    return {"services": SERVICES}

@app.get("/api/services/{service_id}")
async def get_service(service_id: str):
    """Get a specific service."""
    if service_id not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")
    return SERVICES[service_id]

@app.post("/api/services")
async def register_service(service_data: Dict[str, Any]):
    """Register a new service."""
    service_id = str(uuid.uuid4())
    SERVICES[service_id] = {
        "id": service_id,
        "name": service_data.get("service_name", "New Service"),
        "status": "unknown",
        "created_at": datetime.datetime.now().isoformat(),
        "last_heartbeat": None,
        "status_message": "Service registered",
        "metadata": service_data.get("metadata", {})
    }
    return {"service_id": service_id}

@app.post("/api/services/{service_id}/heartbeat")
async def send_heartbeat(service_id: str, heartbeat_data: Dict[str, Any]):
    """Send a heartbeat for a service."""
    if service_id not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")
    
    SERVICES[service_id]["status"] = heartbeat_data.get("status", "healthy")
    SERVICES[service_id]["last_heartbeat"] = datetime.datetime.now().isoformat()
    SERVICES[service_id]["status_message"] = heartbeat_data.get("message", "Heartbeat received")
    
    if heartbeat_data.get("metadata"):
        SERVICES[service_id]["metadata"].update(heartbeat_data["metadata"])
    
    return {"success": True}

def main():
    """Main entry point for the mock API server."""
    parser = argparse.ArgumentParser(description="LaneSwap Mock API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    
    args = parser.parse_args()
    
    logger.info(f"Starting mock API server on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main() 