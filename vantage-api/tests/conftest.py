"""
Pytest configuration for API tests.
"""

import pytest


@pytest.fixture
def sample_timeseries_data():
    """Sample timeseries data for testing."""
    return [
        {
            "timestamp": 1701878400000,
            "service_name": "test-service",
            "endpoint": "/api/test",
            "method": "GET",
            "status_code": 200,
            "duration_ms": 123.45
        },
        {
            "timestamp": 1701878460000,
            "service_name": "test-service",
            "endpoint": "/api/users",
            "method": "GET",
            "status_code": 200,
            "duration_ms": 98.12
        }
    ]
