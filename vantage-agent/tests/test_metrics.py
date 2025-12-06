"""
Unit tests for metric models.
"""

import pytest
from vantage_agent.metrics.models import Metric, MetricBatch


class TestMetric:
    """Tests for Metric class."""
    
    def test_create_http_request_metric(self):
        """Test creating an HTTP request metric."""
        metric = Metric.create_http_request_metric(
            service_name="test-service",
            endpoint="/api/users",
            method="GET",
            status_code=200,
            duration_ms=123.45,
            tags={"region": "us-east-1"},
        )
        
        assert metric.service_name == "test-service"
        assert metric.endpoint == "/api/users"
        assert metric.method == "GET"
        assert metric.status_code == 200
        assert metric.duration_ms == 123.45
        assert metric.metric_name == "http.request.duration"
        assert metric.metric_type == "histogram"
        assert metric.tags == {"region": "us-east-1"}
        assert metric.error is None
    
    def test_create_http_request_metric_with_error(self):
        """Test creating an HTTP request metric with error."""
        metric = Metric.create_http_request_metric(
            service_name="test-service",
            endpoint="/api/error",
            method="POST",
            status_code=500,
            duration_ms=50.0,
            error="Connection timeout",
        )
        
        assert metric.status_code == 500
        assert metric.error == "Connection timeout"
    
    def test_create_counter_metric(self):
        """Test creating a counter metric."""
        metric = Metric.create_counter_metric(
            service_name="test-service",
            metric_name="requests.total",
            value=1.0,
            tags={"endpoint": "/api/users"},
        )
        
        assert metric.service_name == "test-service"
        assert metric.metric_name == "requests.total"
        assert metric.metric_type == "counter"
        assert metric.value == 1.0
        assert metric.tags == {"endpoint": "/api/users"}
    
    def test_create_gauge_metric(self):
        """Test creating a gauge metric."""
        metric = Metric.create_gauge_metric(
            service_name="test-service",
            metric_name="memory.usage",
            value=85.5,
            tags={"host": "server-1"},
        )
        
        assert metric.service_name == "test-service"
        assert metric.metric_name == "memory.usage"
        assert metric.metric_type == "gauge"
        assert metric.value == 85.5
    
    def test_to_dict(self):
        """Test converting metric to dictionary."""
        metric = Metric.create_counter_metric(
            service_name="test-service",
            metric_name="test.metric",
            value=1.0,
        )
        
        data = metric.to_dict()
        
        assert "timestamp" in data
        assert data["service_name"] == "test-service"
        assert data["metric_name"] == "test.metric"
        assert data["metric_type"] == "counter"
        assert data["value"] == 1.0
        # None values should be excluded
        assert "error" not in data


class TestMetricBatch:
    """Tests for MetricBatch class."""
    
    def test_create_batch(self):
        """Test creating a metric batch."""
        metrics = [
            Metric.create_counter_metric("test-service", "metric1", 1.0),
            Metric.create_counter_metric("test-service", "metric2", 2.0),
        ]
        
        batch = MetricBatch(
            metrics=metrics,
            service_name="test-service",
            environment="test",
        )
        
        assert len(batch) == 2
        assert batch.service_name == "test-service"
        assert batch.environment == "test"
    
    def test_to_dict(self):
        """Test converting batch to dictionary."""
        metrics = [
            Metric.create_counter_metric("test-service", "metric1", 1.0),
        ]
        
        batch = MetricBatch(
            metrics=metrics,
            service_name="test-service",
            environment="production",
        )
        
        data = batch.to_dict()
        
        assert "metrics" in data
        assert len(data["metrics"]) == 1
        assert data["service_name"] == "test-service"
        assert data["environment"] == "production"
        assert data["batch_size"] == 1
        assert "agent_version" in data
