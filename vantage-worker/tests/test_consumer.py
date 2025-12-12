"""
Tests for the Kafka consumer worker.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from worker.consumer import MetricConsumer
from worker.config import settings


@pytest.fixture
def mock_database():
    """Mock database insert function."""
    with patch('worker.consumer.insert_metrics_batch') as mock:
        mock.return_value = 0
        yield mock


@pytest.mark.asyncio
async def test_consumer_initialization():
    """Test consumer initializes correctly."""
    consumer = MetricConsumer()
    
    assert consumer.consumer is None
    assert consumer.running is False
    assert consumer.batch == []


@pytest.mark.asyncio
async def test_batch_flush(mock_database):
    """Test batch flushing to database."""
    consumer = MetricConsumer()
    
    # Add some metrics to batch
    consumer.batch = [
        {"service_name": "test", "value": 1.0},
        {"service_name": "test", "value": 2.0},
    ]
    
    consumer._flush_batch()
    
    # Verify database was called
    mock_database.assert_called_once()
    assert len(consumer.batch) == 0


@pytest.mark.asyncio
async def test_batch_flush_empty(mock_database):
    """Test flushing empty batch doesn't call database."""
    consumer = MetricConsumer()
    consumer.batch = []
    
    consumer._flush_batch()
    
    mock_database.assert_not_called()


@pytest.mark.asyncio
async def test_batch_flush_with_error(mock_database, caplog):
    """Test batch flush handles database errors gracefully."""
    consumer = MetricConsumer()
    consumer.batch = [{"service_name": "test", "value": 1.0}]
    
    # Make database throw an error
    mock_database.side_effect = Exception("Database error")
    
    consumer._flush_batch()
    
    # Batch should still be cleared (prevents infinite retry)
    assert len(consumer.batch) == 0
    # Error should be logged
    assert "Error inserting batch" in caplog.text


@pytest.mark.asyncio
async def test_batch_size_trigger(mock_database):
    """Test batch flushes when size limit reached."""
    with patch('worker.config.settings.batch_size', 5):
        consumer = MetricConsumer()
        
        # Add metrics up to batch size
        for i in range(5):
            consumer.batch.append({"service_name": "test", "value": float(i)})
        
        # Batch should be at limit
        assert len(consumer.batch) == 5
        
        # Flush should be triggered
        consumer._flush_batch()
        
        # Verify flush occurred
        assert len(consumer.batch) == 0
        mock_database.assert_called_once()


@pytest.mark.asyncio
async def test_stop_flushes_remaining_batch(mock_database):
    """Test stop() flushes any remaining metrics in batch."""
    consumer = MetricConsumer()
    consumer.batch = [{"service_name": "test", "value": 1.0}]
    consumer.running = True
    consumer.consumer = Mock()
    consumer.consumer.stop = AsyncMock()
    
    await consumer.stop()
    
    # Should have flushed the batch
    mock_database.assert_called_once()
    assert consumer.running is False
