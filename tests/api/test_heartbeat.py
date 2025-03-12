"""Test the heartbeat endpoints."""

import pytest
from fastapi.testclient import TestClient
from laneswap.api.app import app
from laneswap.models.heartbeat import HeartbeatStatus

client = TestClient(app)


def test_register_service():
    """Test registering a new service."""
    response = client.post(
        "/api/services",
        json={
            "service_name": "Test Service",
            "metadata": {"version": "1.0.0"}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "service_id" in data
    assert isinstance(data["service_id"], str)


def test_send_heartbeat():
    """Test sending a heartbeat for a service."""
    # First register a service
    register_response = client.post(
        "/api/services",
        json={
            "service_name": "Test Service",
            "metadata": {"version": "1.0.0"}
        }
    )
    assert register_response.status_code == 200
    service_id = register_response.json()["service_id"]

    # Send a heartbeat
    response = client.post(
        f"/api/services/{service_id}/heartbeat",
        json={
            "status": "healthy",
            "message": "Service is running normally"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["message"] == "Service is running normally"


def test_get_service_status():
    """Test getting service status."""
    # First register a service
    register_response = client.post(
        "/api/services",
        json={
            "service_name": "Test Service",
            "metadata": {"version": "1.0.0"}
        }
    )
    assert register_response.status_code == 200
    service_id = register_response.json()["service_id"]

    # Get service status
    response = client.get(f"/api/services/{service_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Service"
    assert "status" in data
    assert "last_heartbeat" in data


def test_get_all_services():
    """Test getting status of all services."""
    # First register a service
    register_response = client.post(
        "/api/services",
        json={
            "service_name": "Test Service",
            "metadata": {"version": "1.0.0"}
        }
    )
    assert register_response.status_code == 200

    # Get all services
    response = client.get("/api/services")
    assert response.status_code == 200
    data = response.json()
    assert "services" in data
    assert "summary" in data
    assert data["summary"]["total"] >= 1


def test_service_not_found():
    """Test getting a non-existent service."""
    response = client.get("/api/services/non-existent-id")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_invalid_heartbeat():
    """Test sending an invalid heartbeat."""
    response = client.post(
        "/api/services/some-id/heartbeat",
        json={
            "status": "INVALID_STATUS",
            "message": "This should fail"
        }
    )
    assert response.status_code in [400, 422]  # Either bad request or validation error 