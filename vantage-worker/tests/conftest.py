"""
Pytest configuration for worker tests.
"""

import pytest


@pytest.fixture
def sample_metric():
    """Sample metric for testing."""
    return {
        "timestamp": 1701878400000,
        "service_name": "test-service",
        "metric_name": "http.request.duration",
        "value": 123.45,
        "endpoint": "/api/test",
        "method": "GET",
        "status_code": 200
    }


@pytest.fixture
def sample_metrics_batch():
    """Batch of sample metrics for testing."""
    return [
        {
            "timestamp": 1701878400000 + i,
            "service_name": f"service-{i % 3}",
            "metric_name": "http.request.duration",
            "value": 100.0 + i,
            "endpoint": f"/api/endpoint{i}",
            "method": "GET",
            "status_code": 200
        }
        for i in range(10)
    ]
