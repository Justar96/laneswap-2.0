"""Test the API server endpoints."""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from laneswap.api.app import app
from laneswap.models.heartbeat import HeartbeatStatus


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def service_id(client):
    """Create a test service and return its ID."""
    service_data = {
        "service_name": "Test Service",
        "metadata": {
            "test": True,
            "timestamp": datetime.now().isoformat()
        }
    }

    response = client.post("/api/services", json=service_data)
    assert response.status_code == 200
    data = response.json()
    return data["service_id"]


def test_api_root(client):
    """Test the API root endpoint."""
    response = client.get("/api")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "LaneSwap API"
    assert data["version"] == "2.0.0"
    assert data["status"] == "operational"


def test_api_health(client):
    """Test the API health endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert data["service"] == "LaneSwap API"


def test_register_service(client):
    """Test registering a service."""
    service_data = {
        "service_name": "Test Service",
        "metadata": {
            "test": True,
            "timestamp": datetime.now().isoformat()
        }
    }

    response = client.post("/api/services", json=service_data)
    assert response.status_code == 200
    data = response.json()
    assert "service_id" in data


def test_send_heartbeat(client, service_id):
    """Test sending a heartbeat."""
    heartbeat_data = {
        "status": HeartbeatStatus.HEALTHY.value,
        "message": "Service is running normally"
    }

    response = client.post(f"/api/services/{service_id}/heartbeat", json=heartbeat_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == HeartbeatStatus.HEALTHY.value
    assert data["message"] == "Service is running normally"


def test_get_service(client, service_id):
    """Test getting a service."""
    response = client.get(f"/api/services/{service_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == service_id
    assert "status" in data
    assert "last_heartbeat" in data


def test_get_all_services(client):
    """Test getting all services."""
    response = client.get("/api/services")
    assert response.status_code == 200
    data = response.json()
    assert "services" in data
    assert "summary" in data
    assert isinstance(data["summary"]["total"], int)


def test_service_not_found(client):
    """Test getting a non-existent service."""
    response = client.get("/api/services/non-existent-id")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_invalid_heartbeat(client):
    """Test sending an invalid heartbeat."""
    # Missing service_id
    heartbeat_data = {
        "status": "INVALID_STATUS",
        "message": "This should fail"
    }

    response = client.post("/api/services/some-id/heartbeat", json=heartbeat_data)
    assert response.status_code == 422  # Validation error 