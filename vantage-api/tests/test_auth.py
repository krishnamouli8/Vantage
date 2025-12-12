"""
Tests for API authentication.
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.config import settings

client = TestClient(app)


def test_root_endpoint_public():
    """Test that root endpoint is public."""
    response = client.get("/")
    assert response.status_code == 200


def test_query_endpoints_without_auth_when_disabled():
    """Test query endpoints work when auth is disabled."""
    # Auth should be disabled by default
    assert settings.auth_enabled == False
    
    # Test timeseries endpoint
    response = client.get("/api/metrics/timeseries")
    assert response.status_code == 200
    
    # Test aggregated endpoint
    response = client.get("/api/metrics/aggregated")
    assert response.status_code == 200
    
    # Test services endpoint
    response = client.get("/api/services")
    assert response.status_code == 200


@pytest.mark.skipif(
    not settings.auth_enabled,
    reason="Authentication not enabled"
)
def test_query_endpoints_require_api_key():
    """Test that query endpoints require API key when auth enabled."""
    # Without API key should fail
    response = client.get("/api/metrics/timeseries")
    assert response.status_code == 401
    
    response = client.get("/api/metrics/aggregated")
    assert response.status_code == 401
    
    response = client.get("/api/services")
    assert response.status_code == 401


@pytest.mark.skipif(
    not settings.auth_enabled,
    reason="Authentication not enabled"
)
def test_query_endpoints_with_valid_api_key():
    """Test that query endpoints work with valid API key."""
    headers = {"X-API-Key": settings.api_key}
    
    # With valid API key should succeed
    response = client.get("/api/metrics/timeseries", headers=headers)
    assert response.status_code == 200
    
    response = client.get("/api/metrics/aggregated", headers=headers)
    assert response.status_code == 200
    
    response = client.get("/api/services", headers=headers)
    assert response.status_code == 200


@pytest.mark.skipif(
    not settings.auth_enabled,
    reason="Authentication not enabled"
)
def test_query_endpoints_with_invalid_api_key():
    """Test that query endpoints reject invalid API key."""
    headers = {"X-API-Key": "wrong-key"}
    
    # With invalid API key should fail
    response = client.get("/api/metrics/timeseries", headers=headers)
    assert response.status_code == 401
    
    response = client.get("/api/metrics/aggregated", headers=headers)
    assert response.status_code == 401
    
    response = client.get("/api/services", headers=headers)
    assert response.status_code == 401
