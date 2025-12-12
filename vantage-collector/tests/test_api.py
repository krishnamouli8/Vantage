"""
Tests for the collector API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "kafka" in data


def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "vantage-collector"
    assert "endpoints" in data


def test_ingest_metrics_valid():
    """Test ingesting valid metrics."""
    payload = {
        "metrics": [
            {
                "timestamp": 1701878400000,
                "service_name": "test-service",
                "metric_name": "http.request.duration",
                "metric_type": "histogram",
                "value": 123.45,
                "endpoint": "/api/test",
                "method": "GET",
                "status_code": 200,
                "duration_ms": 123.45
            }
        ],
        "service_name": "test-service",
        "environment": "test"
    }
    
    response = client.post("/v1/metrics", json=payload)
    
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "accepted"
    assert data["metrics_received"] == 1


def test_ingest_metrics_batch():
    """Test ingesting a batch of metrics."""
    metrics = [
        {
            "timestamp": 1701878400000 + i,
            "service_name": "test-service",
            "metric_name": "http.request.duration",
            "metric_type": "histogram",
            "value": 100.0 + i,
            "endpoint": f"/api/endpoint{i}",
            "method": "GET",
            "status_code": 200
        }
        for i in range(10)
    ]
    
    payload = {
        "metrics": metrics,
        "service_name": "test-service"
    }
    
    response = client.post("/v1/metrics", json=payload)
    
    assert response.status_code == 202
    data = response.json()
    assert data["metrics_received"] == 10


def test_ingest_metrics_invalid_missing_required():
    """Test ingesting metrics with missing required fields."""
    payload = {
        "metrics": [
            {
                "timestamp": 1701878400000,
                # Missing service_name
                "metric_name": "test.metric",
                "value": 123.45
            }
        ]
    }
    
    response = client.post("/v1/metrics", json=payload)
    
    assert response.status_code == 422  # Validation error


def test_ingest_metrics_empty_batch():
    """Test ingesting an empty batch."""
    payload = {
        "metrics": [],
        "service_name": "test-service"
    }
    
    response = client.post("/v1/metrics", json=payload)
    
    # Should accept empty batches or reject them
    assert response.status_code in [200, 202, 422]


def test_stats_endpoint():
    """Test the statistics endpoint."""
    response = client.get("/v1/stats")
    
    assert response.status_code == 200
    data = response.json()
    assert "metrics_received" in data or "batches_processed" in data

