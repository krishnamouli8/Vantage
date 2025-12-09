"""Kafka consumer for metrics."""

import json
import logging
import asyncio
from typing import List, Dict
from aiokafka import AIOKafkaConsumer
from worker.config import settings
from worker.database import insert_metrics_batch

logger = logging.getLogger(__name__)


class MetricConsumer:
    """Consume metrics from Kafka and write to SQLite."""
    
    def __init__(self):
        self.consumer = None
        self.running = False
        self.batch: List[Dict] = []
        
    async def start(self):
        """Start the consumer."""
        self.consumer = AIOKafkaConsumer(
            settings.kafka_topic,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=settings.kafka_group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True,
        )
        
        await self.consumer.start()
        self.running = True
        logger.info(f"Consumer started, listening to {settings.kafka_topic}")
        
    async def stop(self):
        """Stop the consumer."""
        self.running = False
        if self.batch:
            self._flush_batch()
        if self.consumer:
            await self.consumer.stop()
        logger.info("Consumer stopped")
        
    def _flush_batch(self):
        """Flush batch to database."""
        if not self.batch:
            return
            
        try:
            count = insert_metrics_batch(self.batch)
            logger.info(f"Inserted {count} metrics into database")
            self.batch = []
        except Exception as e:
            logger.error(f"Error inserting batch: {e}", exc_info=True)
            self.batch = []
    
    async def consume(self):
        """Consume messages from Kafka."""
        try:
            async for message in self.consumer:
                metric = message.value
                self.batch.append(metric)
                
                if len(self.batch) >= settings.batch_size:
                    self._flush_batch()
                    
        except Exception as e:
            logger.error(f"Error consuming messages: {e}", exc_info=True)
