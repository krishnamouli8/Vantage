"""
Tests for query API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "vantage-api"


def test_get_services():
    """Test getting list of services."""
    response = client.get("/api/services")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_timeseries_no_filter():
    """Test getting timeseries data without filters."""
    response = client.get("/api/metrics/timeseries")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_timeseries_with_service_filter():
    """Test getting timeseries data filtered by service."""
    response = client.get("/api/metrics/timeseries?service=test-service")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_timeseries_with_range():
    """Test getting timeseries data with time range."""
    response = client.get("/api/metrics/timeseries?range=7200")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_aggregated_metrics():
    """Test getting aggregated metrics."""
    response = client.get("/api/metrics/aggregated")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)


def test_get_aggregated_with_service():
    """Test getting aggregated metrics for specific service."""
    response = client.get("/api/metrics/aggregated?service=test-service")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)


def test_get_aggregated_with_range():
    """Test getting aggregated metrics with time range."""
    response = client.get("/api/metrics/aggregated?range=3600")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)

