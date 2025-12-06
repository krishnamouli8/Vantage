"""Models package for Vantage Collector."""

from app.models.metric import (
    Metric,
    MetricBatch,
    IngestResponse,
    HealthResponse,
    MetricsResponse,
)

__all__ = [
    "Metric",
    "MetricBatch",
    "IngestResponse",
    "HealthResponse",
    "MetricsResponse",
]
