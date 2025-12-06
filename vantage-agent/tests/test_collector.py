"""
Unit tests for metric collector.
"""

import pytest
import time
from vantage_agent.config import AgentConfig
from vantage_agent.metrics.collector import MetricCollector
from vantage_agent.metrics.models import Metric


class TestMetricCollector:
    """Tests for MetricCollector class."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return AgentConfig(
            service_name="test-service",
            max_queue_size=100,
            batch_size=10,
        )
    
    @pytest.fixture
    def collector(self, config):
        """Create test collector."""
        return MetricCollector(config)
    
    def test_collect_metric(self, collector):
        """Test collecting a single metric."""
        metric = Metric.create_counter_metric("test-service", "test.metric", 1.0)
        
        result = collector.collect(metric)
        
        assert result is True
        assert collector.size() == 1
        assert not collector.is_empty()
    
    def test_collect_multiple_metrics(self, collector):
        """Test collecting multiple metrics."""
        metrics = [
            Metric.create_counter_metric("test-service", f"metric{i}", 1.0)
            for i in range(5)
        ]
        
        for metric in metrics:
            collector.collect(metric)
        
        assert collector.size() == 5
    
    def test_collect_batch(self, collector):
        """Test collecting a batch of metrics."""
        metrics = [
            Metric.create_counter_metric("test-service", f"metric{i}", 1.0)
            for i in range(5)
        ]
        
        collected = collector.collect_batch(metrics)
        
        assert collected == 5
        assert collector.size() == 5
    
    def test_get_batch(self, collector):
        """Test getting a batch of metrics."""
        # Add 15 metrics
        for i in range(15):
            metric = Metric.create_counter_metric("test-service", f"metric{i}", 1.0)
            collector.collect(metric)
        
        # Get batch of 10
        batch = collector.get_batch(max_size=10, timeout=0.1)
        
        assert len(batch) == 10
        assert collector.size() == 5  # 5 remaining
    
    def test_get_all(self, collector):
        """Test getting all metrics."""
        # Add 5 metrics
        for i in range(5):
            metric = Metric.create_counter_metric("test-service", f"metric{i}", 1.0)
            collector.collect(metric)
        
        # Get all
        all_metrics = collector.get_all()
        
        assert len(all_metrics) == 5
        assert collector.is_empty()
    
    def test_queue_full(self):
        """Test behavior when queue is full."""
        config = AgentConfig(
            service_name="test-service",
            max_queue_size=5,  # Small queue
        )
        collector = MetricCollector(config)
        
        # Fill the queue
        for i in range(5):
            metric = Metric.create_counter_metric("test-service", f"metric{i}", 1.0)
            result = collector.collect(metric)
            assert result is True
        
        # Try to add one more (should be dropped)
        metric = Metric.create_counter_metric("test-service", "overflow", 1.0)
        result = collector.collect(metric)
        
        assert result is False  # Metric was dropped
        assert collector.size() == 5
    
    def test_get_stats(self, collector):
        """Test getting collector statistics."""
        # Collect some metrics
        for i in range(3):
            metric = Metric.create_counter_metric("test-service", f"metric{i}", 1.0)
            collector.collect(metric)
        
        stats = collector.get_stats()
        
        assert stats["metrics_collected"] == 3
        assert stats["metrics_dropped"] == 0
        assert stats["queue_size"] == 3
        assert stats["drop_rate"] == 0.0
    
    def test_clear(self, collector):
        """Test clearing the queue."""
        # Add metrics
        for i in range(5):
            metric = Metric.create_counter_metric("test-service", f"metric{i}", 1.0)
            collector.collect(metric)
        
        # Clear
        collector.clear()
        
        assert collector.is_empty()
        assert collector.size() == 0
