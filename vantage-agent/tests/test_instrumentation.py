"""
Integration tests for instrumentation.

These tests verify that instrumentation works correctly with real libraries.
"""

import pytest
import requests
from vantage_agent.config import AgentConfig
from vantage_agent.metrics.collector import MetricCollector
from vantage_agent.instrumentation.requests_patch import RequestsInstrumentor


class TestRequestsInstrumentation:
    """Integration tests for requests instrumentation."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return AgentConfig(service_name="test-service")
    
    @pytest.fixture
    def collector(self, config):
        """Create test collector."""
        return MetricCollector(config)
    
    @pytest.fixture
    def instrumentor(self, config, collector):
        """Create and instrument requests."""
        inst = RequestsInstrumentor(config, collector)
        inst.instrument()
        yield inst
        inst.uninstrument()
    
    def test_instrument_get_request(self, instrumentor, collector):
        """Test that GET requests are instrumented."""
        # Make a request
        response = requests.get("https://httpbin.org/get")
        
        assert response.status_code == 200
        
        # Check that metric was collected
        # Wait a bit for async collection
        import time
        time.sleep(0.1)
        
        assert collector.size() > 0
        
        # Get the metric
        metrics = collector.get_all()
        assert len(metrics) > 0
        
        metric = metrics[0]
        assert metric.method == "GET"
        assert metric.endpoint == "/get"
        assert metric.status_code == 200
        assert metric.duration_ms > 0
    
    def test_instrument_post_request(self, instrumentor, collector):
        """Test that POST requests are instrumented."""
        response = requests.post(
            "https://httpbin.org/post",
            json={"key": "value"}
        )
        
        assert response.status_code == 200
        
        import time
        time.sleep(0.1)
        
        metrics = collector.get_all()
        assert len(metrics) > 0
        
        metric = metrics[0]
        assert metric.method == "POST"
        assert metric.endpoint == "/post"
    
    def test_uninstrument(self, config, collector):
        """Test that uninstrumentation works."""
        inst = RequestsInstrumentor(config, collector)
        inst.instrument()
        
        # Make a request (should be tracked)
        requests.get("https://httpbin.org/get")
        
        import time
        time.sleep(0.1)
        
        initial_count = collector.size()
        assert initial_count > 0
        
        # Uninstrument
        inst.uninstrument()
        
        # Clear collector
        collector.clear()
        
        # Make another request (should NOT be tracked)
        requests.get("https://httpbin.org/get")
        
        time.sleep(0.1)
        
        # No new metrics should be collected
        assert collector.size() == 0
