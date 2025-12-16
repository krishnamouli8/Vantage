"""Prometheus metrics HTTP server for worker service.

Exposes metrics on a separate port for scraping.
"""

import logging
from aiohttp import web
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CollectorRegistry

logger = logging.getLogger(__name__)

# Create worker-specific registry
worker_registry = CollectorRegistry()

# Define metrics
messages_consumed = Counter(
    'vantage_worker_kafka_messages_consumed_total',
    'Total Kafka messages consumed',
    ['topic'],
    registry=worker_registry
)

messages_processed = Counter(
    'vantage_worker_messages_processed_total',
    'Total messages successfully processed',
    ['status'],
    registry=worker_registry
)

database_inserts = Counter(
    'vantage_worker_database_inserts_total',
    'Total database insert operations',
    ['status'],
    registry=worker_registry
)

database_insert_duration = Histogram(
    'vantage_worker_database_insert_duration_seconds',
    'Database insert duration in seconds',
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
    registry=worker_registry
)

batch_size = Histogram(
    'vantage_worker_batch_size',
    'Size of batches processed',
    buckets=[1, 10, 25, 50, 100, 250, 500, 1000],
    registry=worker_registry
)

processing_lag = Gauge(
    'vantage_worker_processing_lag_seconds',
    'Processing lag in seconds',
    registry=worker_registry
)

errors_total = Counter(
    'vantage_worker_errors_total',
    'Total worker errors',
    ['error_type'],
    registry=worker_registry
)


async def metrics_handler(request):
    """Handle Prometheus metrics request."""
    return web.Response(
        text=generate_latest(worker_registry).decode('utf-8'),
        content_type="text/plain",
        charset="utf-8"
    )


def create_metrics_app(port: int = 9092):
    """Create aiohttp app for metrics server.
    
    Args:
        port: Port to run metrics server on
        
    Returns:
        aiohttp web application
    """
    app = web.Application()
    app.router.add_get('/metrics', metrics_handler)
    
    logger.info(f"Metrics server configured on port {port}")
    
    return app


async def start_metrics_server(port: int = 9092):
    """Start metrics server.
    
    Args:
        port: Port to run metrics server on
    """
    app = create_metrics_app(port)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"Metrics server started on http://0.0.0.0:{port}/metrics")


# Export metrics for use in consumer
__all__ = [
    'worker_registry',
    'messages_consumed',
    'messages_processed',
    'database_inserts',
    'database_insert_duration',
    'batch_size',
    'processing_lag',
    'errors_total',
    'start_metrics_server',
]
