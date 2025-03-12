"""
Tests for the heartbeat models.
"""

import pytest
from datetime import datetime

from laneswap.models.heartbeat import (
    ServiceRegistration,
    ServiceHeartbeat,
    ServiceStatus,
    HeartbeatEvent
)
from laneswap.core.heartbeat import HeartbeatStatus


def test_service_registration():
    """Test the ServiceRegistration model."""
    # Create a service registration
    registration = ServiceRegistration(
        service_name="Test Service",
        metadata={"version": "1.0.0"}
    )
    
    # Verify the model
    assert registration.service_name == "Test Service"
    assert registration.metadata == {"version": "1.0.0"}
    
    # Test serialization
    data = registration.model_dump()
    assert data["service_name"] == "Test Service"
    assert data["metadata"] == {"version": "1.0.0"}
    
    # Test deserialization
    registration2 = ServiceRegistration.model_validate(data)
    assert registration2.service_name == registration.service_name
    assert registration2.metadata == registration.metadata


def test_service_heartbeat():
    """Test the ServiceHeartbeat model."""
    # Create a service heartbeat
    heartbeat = ServiceHeartbeat(
        status=HeartbeatStatus.HEALTHY,
        message="Service running normally",
        metadata={"cpu": 0.5, "memory": 0.3}
    )
    
    # Verify the model
    assert heartbeat.status == HeartbeatStatus.HEALTHY
    assert heartbeat.message == "Service running normally"
    assert heartbeat.metadata == {"cpu": 0.5, "memory": 0.3}
    
    # Test serialization
    data = heartbeat.model_dump()
    assert data["status"] == HeartbeatStatus.HEALTHY.value
    assert data["message"] == "Service running normally"
    assert data["metadata"] == {"cpu": 0.5, "memory": 0.3}
    
    # Test deserialization
    heartbeat2 = ServiceHeartbeat.model_validate(data)
    assert heartbeat2.status == heartbeat.status
    assert heartbeat2.message == heartbeat.message
    assert heartbeat2.metadata == heartbeat.metadata


def test_service_status():
    """Test the ServiceStatus model."""
    # Create a service status
    status = ServiceStatus(
        id="test-service-id",
        name="Test Service",
        status=HeartbeatStatus.HEALTHY,
        last_heartbeat=datetime.now(),
        message="Service running normally",
        metadata={"version": "1.0.0"},
        events=[{
            "type": "heartbeat",
            "timestamp": datetime.now(),
            "status": HeartbeatStatus.HEALTHY.value,
            "message": "Service running normally",
            "metadata": {"cpu": 0.5, "memory": 0.3}
        }]
    )
    
    # Verify the model
    assert status.id == "test-service-id"
    assert status.name == "Test Service"
    assert status.status == HeartbeatStatus.HEALTHY
    assert status.message == "Service running normally"
    assert status.metadata == {"version": "1.0.0"}
    assert len(status.events) == 1
    
    # Test serialization
    data = status.model_dump()
    assert data["id"] == "test-service-id"
    assert data["name"] == "Test Service"
    assert data["status"] == HeartbeatStatus.HEALTHY.value
    assert data["message"] == "Service running normally"
    assert data["metadata"] == {"version": "1.0.0"}
    assert len(data["events"]) == 1
    
    # Test deserialization
    status2 = ServiceStatus.model_validate(data)
    assert status2.id == status.id
    assert status2.name == status.name
    assert status2.status == status.status
    assert status2.message == status.message
    assert status2.metadata == status.metadata
    assert len(status2.events) == len(status.events)


def test_heartbeat_event():
    """Test the HeartbeatEvent model."""
    # Create a heartbeat event
    event = HeartbeatEvent(
        status=HeartbeatStatus.WARNING,
        message="High CPU usage detected",
        metadata={"cpu": 0.9, "memory": 0.3}
    )
    
    # Verify the model
    assert event.status == HeartbeatStatus.WARNING
    assert event.message == "High CPU usage detected"
    assert event.metadata == {"cpu": 0.9, "memory": 0.3}
    assert event.timestamp is not None
    
    # Test serialization
    data = event.model_dump()
    assert data["status"] == HeartbeatStatus.WARNING.value
    assert data["message"] == "High CPU usage detected"
    assert data["metadata"] == {"cpu": 0.9, "memory": 0.3}
    assert "timestamp" in data
    
    # Test deserialization
    event2 = HeartbeatEvent.model_validate(data)
    assert event2.status == event.status
    assert event2.message == event.message
    assert event2.metadata == event.metadata 