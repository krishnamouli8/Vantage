"""
Unit tests for configuration.
"""

import pytest
import os
from vantage_agent.config import AgentConfig


class TestAgentConfig:
    """Tests for AgentConfig class."""
    
    def test_create_config_with_defaults(self):
        """Test creating config with default values."""
        config = AgentConfig(service_name="test-service")
        
        assert config.service_name == "test-service"
        assert config.collector_url == "http://localhost:8000"
        assert config.flush_interval == 5
        assert config.batch_size == 100
        assert config.max_queue_size == 10000
        assert config.debug is False
        assert config.timeout == 10
        assert config.retry_attempts == 3
    
    def test_create_config_with_custom_values(self):
        """Test creating config with custom values."""
        config = AgentConfig(
            service_name="my-service",
            collector_url="http://collector:9000",
            flush_interval=10,
            batch_size=50,
            max_queue_size=5000,
            debug=True,
            environment="production",
            tags={"region": "us-east-1"},
        )
        
        assert config.service_name == "my-service"
        assert config.collector_url == "http://collector:9000"
        assert config.flush_interval == 10
        assert config.batch_size == 50
        assert config.max_queue_size == 5000
        assert config.debug is True
        assert config.environment == "production"
        assert config.tags == {"region": "us-east-1"}
    
    def test_collector_endpoint(self):
        """Test collector endpoint property."""
        config = AgentConfig(
            service_name="test-service",
            collector_url="http://localhost:8000"
        )
        
        assert config.collector_endpoint == "http://localhost:8000/v1/metrics"
    
    def test_collector_endpoint_strips_trailing_slash(self):
        """Test that trailing slash is stripped from collector URL."""
        config = AgentConfig(
            service_name="test-service",
            collector_url="http://localhost:8000/"
        )
        
        assert config.collector_endpoint == "http://localhost:8000/v1/metrics"
    
    def test_validation_empty_service_name(self):
        """Test validation fails with empty service name."""
        with pytest.raises(ValueError, match="service_name is required"):
            AgentConfig(service_name="")
    
    def test_validation_negative_flush_interval(self):
        """Test validation fails with negative flush interval."""
        with pytest.raises(ValueError, match="flush_interval must be positive"):
            AgentConfig(service_name="test", flush_interval=-1)
    
    def test_validation_zero_batch_size(self):
        """Test validation fails with zero batch size."""
        with pytest.raises(ValueError, match="batch_size must be positive"):
            AgentConfig(service_name="test", batch_size=0)
    
    def test_env_override_collector_url(self, monkeypatch):
        """Test environment variable override for collector URL."""
        monkeypatch.setenv("VANTAGE_COLLECTOR_URL", "http://env-collector:8000")
        
        config = AgentConfig(service_name="test-service")
        
        assert config.collector_url == "http://env-collector:8000"
    
    def test_env_override_debug(self, monkeypatch):
        """Test environment variable override for debug flag."""
        monkeypatch.setenv("VANTAGE_DEBUG", "true")
        
        config = AgentConfig(service_name="test-service", debug=False)
        
        assert config.debug is True
    
    def test_env_override_environment(self, monkeypatch):
        """Test environment variable for environment name."""
        monkeypatch.setenv("VANTAGE_ENVIRONMENT", "staging")
        
        config = AgentConfig(service_name="test-service")
        
        assert config.environment == "staging"
    
    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = AgentConfig(
            service_name="test-service",
            environment="production",
            tags={"key": "value"},
        )
        
        data = config.to_dict()
        
        assert data["service_name"] == "test-service"
        assert data["environment"] == "production"
        assert data["tags"] == {"key": "value"}
        assert "flush_interval" in data
        assert "batch_size" in data
