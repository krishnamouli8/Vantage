"""Prometheus metrics for API service."""

from fastapi import APIRouter, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CollectorRegistry

router = APIRouter(tags=["metrics"])

# Create API-specific registry
api_registry = CollectorRegistry()

# Define metrics
requests_total = Counter(
    'vantage_api_requests_total',
    'Total API requests received',
    ['method', 'endpoint', 'status'],
    registry=api_registry
)

request_duration = Histogram(
    'vantage_api_request_duration_seconds',
    'API request duration in seconds',
    ['endpoint'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    registry=api_registry
)

database_query_duration = Histogram(
    'vantage_api_database_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=api_registry
)

websocket_connections = Gauge(
    'vantage_api_websocket_connections',
    'Current WebSocket connections',
    registry=api_registry
)

vql_queries_total = Counter(
    'vantage_api_vql_queries_total',
    'Total VQL queries executed',
    ['status'],
    registry=api_registry
)

errors_total = Counter(
    'vantage_api_errors_total',
    'Total API errors',
    ['error_type'],
    registry=api_registry
)


@router.get("/metrics")
async def metrics_endpoint():
    """Export Prometheus metrics in text format."""
    return Response(
        content=generate_latest(api_registry),
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )


# Export metrics for use in other modules
__all__ = [
    'router',
    'requests_total',
    'request_duration',
    'database_query_duration',
    'websocket_connections',
    'vql_queries_total',
    'errors_total',
]
