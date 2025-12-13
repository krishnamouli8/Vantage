"""Kafka consumer for metrics."""

import json
import logging
import asyncio
import time
import sqlite3
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
        self.failed_batches: List[List[Dict]] = []  # For retry
        self.max_retries = 3
        
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
        
        # Try to flush remaining batches
        if self.batch:
            self._flush_batch()
        
        # Try to flush failed batches one last time
        self._retry_failed_batches()
        
        if self.consumer:
            await self.consumer.stop()
        
        # Log any data that couldn't be saved
        if self.failed_batches:
            total_lost = sum(len(batch) for batch in self.failed_batches)
            logger.error(
                f"Shutting down with {total_lost} metrics that could not be saved. "
                f"Consider increasing database resources or retry limits."
            )
        
        logger.info("Consumer stopped")
        
    def _flush_batch(self, retry_count=0):
        """Flush batch to database with retry logic."""
        if not self.batch:
            return
            
        try:
            count = insert_metrics_batch(self.batch)
            logger.info(f"Inserted {count} metrics into database")
            self.batch = []
            
        except Exception as e:
            logger.error(
                f"Error inserting batch (attempt {retry_count + 1}/{self.max_retries}): {e}",
                exc_info=True
            )
            
            # Retry with exponential backoff
            if retry_count < self.max_retries:
                backoff = 2 ** retry_count  # 1s, 2s, 4s
                logger.info(f"Retrying in {backoff} seconds...")
                time.sleep(backoff)
                return self._flush_batch(retry_count + 1)
            else:
                # Max retries exceeded - save to failed batches instead of dropping
                logger.error(
                    f"Max retries exceeded. Moving {len(self.batch)} metrics to failed queue."
                )
                self.failed_batches.append(self.batch.copy())
                self.batch = []
                
                # Limit failed batches to prevent memory issues
                if len(self.failed_batches) > 100:
                    dropped = self.failed_batches.pop(0)
                    logger.error(
                        f"Failed batch queue full. Dropping oldest batch of {len(dropped)} metrics."
                    )
    
    def _retry_failed_batches(self):
        """Attempt to retry previously failed batches."""
        if not self.failed_batches:
            return
            
        logger.info(f"Retrying {len(self.failed_batches)} failed batches...")
        
        while self.failed_batches:
            batch = self.failed_batches.pop(0)
            try:
                count = insert_metrics_batch(batch)
                logger.info(f"Successfully inserted previously failed batch: {count} metrics")
            except Exception as e:
                logger.error(f"Failed to insert retry batch: {e}")
                # Put it back - it will be lost on shutdown
                self.failed_batches.append(batch)
                break  # Don't retry more if one fails
    
    async def consume(self):
        """Consume messages from Kafka."""
        try:
            async for message in self.consumer:
                metric = message.value
                
                # Store span data if present
                if metric.get("metric_type") == "trace.span":
                    self._store_span(metric)
                else:
                    self.batch.append(metric)
                
                if len(self.batch) >= settings.batch_size:
                    self._flush_batch()
                    
                # Periodically retry failed batches during normal operation
                if len(self.batch) == 0 and self.failed_batches:
                    self._retry_failed_batches()
                    
        except Exception as e:
            logger.error(f"Error consuming messages: {e}", exc_info=True)
    
    def _store_span(self, metric: Dict):
        """Store span data in traces/spans tables"""
        try:
            conn = sqlite3.connect(settings.database_path)
            cursor = conn.cursor()
            
            trace_id = metric.get("tags", {}).get("trace_id")
            span_id = metric.get("tags", {}).get("span_id")
            parent_span_id = metric.get("tags", {}).get("parent_span_id")
            operation = metric.get("tags", {}).get("operation", "unknown")
            
            if not trace_id or not span_id:
                logger.warning("Span missing trace_id or span_id, skipping")
                return
            
            # Insert/update trace
            cursor.execute(
                """
                INSERT INTO traces (trace_id, service_name, start_time, status)
                VALUES (?, ?, ?, 'active')
                ON CONFLICT(trace_id) DO UPDATE SET
                    end_time = ?,
                    duration_ms = ? - start_time
                """,
                (
                    trace_id,
                    metric.get("service_name"),
                    metric.get("timestamp"),
                    metric.get("timestamp"),
                    metric.get("timestamp"),
                ),
            )
            
            # Insert span
            cursor.execute(
                """
                INSERT OR REPLACE INTO spans (
                    span_id, trace_id, parent_span_id, service_name,
                    operation_name, start_time, end_time, duration_ms,
                    tags, logs, status, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    span_id,
                    trace_id,
                    parent_span_id if parent_span_id != "root" else None,
                    metric.get("service_name"),
                    operation,
                    metric.get("timestamp"),
                    metric.get("timestamp"),
                    metric.get("duration_ms"),
                    json.dumps(metric.get("tags", {})),
                    json.dumps([]),
                    "ok",
                    0,
                ),
            )
            
            conn.commit()
            conn.close()
            logger.debug(f"Stored span {span_id} for trace {trace_id}")
            
        except Exception as e:
            logger.error(f"Error storing span: {e}")


