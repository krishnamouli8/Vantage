"""
Integration tests for the complete Vantage pipeline.
Tests the flow from agent → collector → kafka → worker → database → API.
"""

import pytest
import time
import requests
from vantage_agent import init_agent
import httpx


class TestEndToEndPipeline:
    """Test the complete metric pipeline."""
    
    @pytest.fixture(scope="class")
    def setup_agent(self):
        """Initialize the agent for testing."""
        init_agent(
            service_name="integration-test",
            collector_url="http://localhost:8000",
            flush_interval=1,  # Fast flush for testing
            batch_size=10,
        )
        yield
        # Cleanup handled by agent shutdown
    
    def test_metric_ingestion_flow(self, setup_agent):
        """Test that metrics flow through the entire pipeline."""
        # Step 1: Send a test metric via agent
        test_url = "http://httpbin.org/get"
        
        # Make request with instrumented requests library
        response = requests.get(test_url)
        assert response.status_code == 200
        
        # Step 2: Wait for metric to flow through pipeline
        time.sleep(3)  # Allow time for processing
        
        # Step 3: Verify metric appears in query API
        query_response = requests.get(
            "http://localhost:8001/api/metrics/timeseries",
            params={"service": "integration-test", "range": 300}
        )
        
        assert query_response.status_code == 200
        metrics = query_response.json()
        
        # Should have at least one metric
        assert len(metrics) > 0
        
        # Verify metric content
        metric = metrics[0]
        assert metric["service_name"] == "integration-test"
        assert "duration_ms" in metric
        assert metric["status_code"] == 200
    
    def test_aggregated_metrics(self, setup_agent):
        """Test aggregated metrics calculation."""
        # Make multiple requests to generate data
        for _ in range(5):
            requests.get("http://httpbin.org/status/200")
        
        time.sleep(3)
        
        # Get aggregated metrics
        response = requests.get(
            "http://localhost:8001/api/metrics/aggregated",
            params={"service": "integration-test"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_requests" in data
        assert "avg_duration" in data
        assert data["total_requests"] > 0
    
    def test_service_listing(self, setup_agent):
        """Test that services are correctly listed."""
        # Make a request to ensure service exists
        requests.get("http://httpbin.org/get")
        time.sleep(2)
        
        response = requests.get("http://localhost:8001/api/services")
        assert response.status_code == 200
        
        services = response.json()
        assert isinstance(services, list)
        assert "integration-test" in services
    
    def test_collector_health(self):
        """Test collector health endpoint."""
        response = requests.get("http://localhost:8000/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_collector_stats(self):
        """Test collector statistics endpoint."""
        response = requests.get("http://localhost:8000/v1/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "metrics_received" in data
        assert "batches_processed" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
