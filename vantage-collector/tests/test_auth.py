"""
Tests for authentication middleware.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)


def test_health_endpoint_public():
    """Test that health endpoint is public (no auth required)."""
    response = client.get("/health")
    assert response.status_code == 200


def test_root_endpoint_public():
    """Test that root endpoint is public."""
    response = client.get("/")
    assert response.status_code == 200


def test_metrics_ingestion_without_auth_when_disabled():
    """Test metrics ingestion works when auth is disabled."""
    # Auth should be disabled by default
    assert settings.auth_enabled == False
    
    payload = {
        "metrics": [{
            "timestamp": 1701878400000,
            "service_name": "test",
            "metric_name": "test.metric",
            "value": 1.0
        }],
        "service_name": "test"
    }
    
    response = client.post("/v1/metrics", json=payload)
    assert response.status_code == 202


@pytest.mark.skipif(
    not settings.auth_enabled,
    reason="Authentication not enabled"
)
def test_metrics_ingestion_requires_api_key():
    """Test that metrics endpoint requires API key when auth enabled."""
    payload = {
        "metrics": [{
            "timestamp": 1701878400000,
            "service_name": "test",
            "metric_name": "test.metric",
            "value": 1.0
        }],
        "service_name": "test"
    }
    
    # Without API key should fail
    response = client.post("/v1/metrics", json=payload)
    assert response.status_code == 401
    assert "API key" in response.json()["detail"]


@pytest.mark.skipif(
    not settings.auth_enabled,
    reason="Authentication not enabled"
)
def test_metrics_ingestion_with_valid_api_key():
    """Test that metrics endpoint works with valid API key."""
    payload = {
        "metrics": [{
            "timestamp": 1701878400000,
            "service_name": "test",
            "metric_name": "test.metric",
            "value": 1.0
        }],
        "service_name": "test"
    }
    
    # With valid API key should succeed
    response = client.post(
        "/v1/metrics",
        json=payload,
        headers={"X-API-Key": settings.api_key}
    )
    assert response.status_code == 202


@pytest.mark.skipif(
    not settings.auth_enabled,
    reason="Authentication not enabled"
)
def test_metrics_ingestion_with_invalid_api_key():
    """Test that metrics endpoint rejects invalid API key."""
    payload = {
        "metrics": [{
            "timestamp": 1701878400000,
            "service_name": "test",
            "metric_name": "test.metric",
            "value": 1.0
        }],
        "service_name": "test"
    }
    
    # With invalid API key should fail
    response = client.post(
        "/v1/metrics",
        json=payload,
        headers={"X-API-Key": "wrong-key"}
    )
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]


def test_stats_endpoint_public():
    """Test that stats endpoint is public."""
    response = client.get("/v1/stats")
    assert response.status_code == 200
