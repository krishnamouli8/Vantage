"""
Kafka/Redpanda producer for sending metrics to the message queue.

Handles async message production with error handling and retries.
"""

import json
import logging
from typing import Optional
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError
from app.config import settings

logger = logging.getLogger(__name__)


class MetricProducer:
    """
    Async Kafka producer for metrics.
    
    Handles connection management, message serialization,
    and error handling for Kafka/Redpanda.
    """
    
    def __init__(self):
        """Initialize the producer (not connected yet)."""
        self.producer: Optional[AIOKafkaProducer] = None
        self._connected = False
        
        # Statistics
        self.messages_sent = 0
        self.messages_failed = 0
        self.bytes_sent = 0
    
    async def start(self) -> None:
        """
        Start the Kafka producer and establish connection.
        
        Raises:
            KafkaError: If connection fails
        """
        if self._connected:
            logger.warning("Producer is already connected")
            return
        
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                compression_type=settings.kafka_compression_type,
                max_batch_size=settings.kafka_max_batch_size,
                linger_ms=settings.kafka_linger_ms,
                acks=settings.kafka_acks,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
            )
            
            await self.producer.start()
            self._connected = True
            
            logger.info(
                f"Kafka producer started successfully",
                extra={
                    "bootstrap_servers": settings.kafka_bootstrap_servers,
                    "topic": settings.kafka_topic,
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}", exc_info=True)
            raise
    
    async def stop(self) -> None:
        """Stop the Kafka producer and close connection."""
        if not self._connected or not self.producer:
            return
        
        try:
            await self.producer.stop()
            self._connected = False
            logger.info("Kafka producer stopped")
            
        except Exception as e:
            logger.error(f"Error stopping Kafka producer: {e}", exc_info=True)
    
    async def send_metric(
        self,
        metric: dict,
        key: Optional[str] = None
    ) -> bool:
        """
        Send a single metric to Kafka.
        
        Args:
            metric: Metric data as dictionary
            key: Optional partition key (defaults to service_name)
        
        Returns:
            True if successful, False otherwise
        """
        if not self._connected or not self.producer:
            logger.error("Producer is not connected")
            return False
        
        try:
            # Use service_name as key for partitioning
            if key is None:
                key = metric.get("service_name", "unknown")
            
            # Send to Kafka
            await self.producer.send(
                settings.kafka_topic,
                value=metric,
                key=key,
            )
            
            # Update statistics
            self.messages_sent += 1
            self.bytes_sent += len(json.dumps(metric))
            
            return True
            
        except KafkaError as e:
            logger.error(
                f"Kafka error sending metric: {e}",
                extra={"metric": metric}
            )
            self.messages_failed += 1
            return False
            
        except Exception as e:
            logger.error(
                f"Unexpected error sending metric: {e}",
                exc_info=True,
                extra={"metric": metric}
            )
            self.messages_failed += 1
            return False
    
    async def send_batch(
        self,
        metrics: list[dict],
        key: Optional[str] = None
    ) -> tuple[int, int]:
        """
        Send a batch of metrics to Kafka.
        
        Args:
            metrics: List of metric dictionaries
            key: Optional partition key
        
        Returns:
            Tuple of (successful_count, failed_count)
        """
        if not self._connected or not self.producer:
            logger.error("Producer is not connected")
            return 0, len(metrics)
        
        successful = 0
        failed = 0
        
        for metric in metrics:
            result = await self.send_metric(metric, key)
            if result:
                successful += 1
            else:
                failed += 1
        
        # Flush to ensure messages are sent
        await self.producer.flush()
        
        logger.info(
            f"Sent batch of {len(metrics)} metrics",
            extra={
                "successful": successful,
                "failed": failed,
                "topic": settings.kafka_topic,
            }
        )
        
        return successful, failed
    
    def is_connected(self) -> bool:
        """Check if producer is connected."""
        return self._connected
    
    def get_stats(self) -> dict:
        """
        Get producer statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "connected": self._connected,
            "messages_sent": self.messages_sent,
            "messages_failed": self.messages_failed,
            "bytes_sent": self.bytes_sent,
            "success_rate": (
                self.messages_sent / (self.messages_sent + self.messages_failed)
                if (self.messages_sent + self.messages_failed) > 0
                else 0.0
            ),
        }


# Global producer instance
_producer: Optional[MetricProducer] = None


async def get_producer() -> MetricProducer:
    """
    Get or create the global producer instance.
    
    Returns:
        MetricProducer instance
    """
    global _producer
    
    if _producer is None:
        _producer = MetricProducer()
        await _producer.start()
    
    return _producer


async def shutdown_producer() -> None:
    """Shutdown the global producer instance."""
    global _producer
    
    if _producer is not None:
        await _producer.stop()
        _producer = None
