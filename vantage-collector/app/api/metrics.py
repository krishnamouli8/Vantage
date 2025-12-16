"""Prometheus metrics endpoint for collector service.

Exposes metrics in Prometheus text format for scraping.
"""

from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse

# Import will come from vantage-common when it's installed in container
# For now, create a simple inline implementation
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from prometheus_client import CollectorRegistry

router = APIRouter(tags=["metrics"])

# Create collector-specific registry
collector_registry = CollectorRegistry()

# Define metrics
requests_total = Counter(
    'vantage_collector_requests_total',
    'Total HTTP requests received',
    ['method', 'endpoint', 'status'],
    registry=collector_registry
)

request_duration = Histogram(
    'vantage_collector_request_duration_seconds',
    'HTTP request duration in seconds',
    ['endpoint'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=collector_registry
)

kafka_publish_duration = Histogram(
    'vantage_collector_kafka_publish_duration_seconds',
    'Kafka publish duration in seconds',
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5],
    registry=collector_registry
)

kafka_messages_published = Counter(
    'vantage_collector_kafka_messages_published_total',
    'Total messages published to Kafka',
    ['topic'],
    registry=collector_registry
)

errors_total = Counter(
    'vantage_collector_errors_total',
    'Total errors encountered',
    ['error_type'],
    registry=collector_registry
)

active_connections = Gauge(
    'vantage_collector_active_connections',
    'Current number of active connections',
    registry=collector_registry
)


@router.get(
    "/metrics",
    response_class=PlainTextResponse,
    summary="Prometheus metrics",
    description="Expose metrics in Prometheus text format"
)
async def metrics_endpoint():
    """
    Export Prometheus metrics in text format.
    
    Returns:
        Prometheus-formatted metrics
    """
    return Response(
        content=generate_latest(collector_registry),
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )


# Export metrics for use in other modules
__all__ = [
    'router',
    'requests_total',
    'request_duration',
    'kafka_publish_duration',
    'kafka_messages_published',
    'errors_total',
    'active_connections',
]
