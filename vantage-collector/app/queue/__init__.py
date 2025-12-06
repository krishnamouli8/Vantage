"""Queue package for Vantage Collector."""

from app.queue.producer import MetricProducer, get_producer, shutdown_producer

__all__ = ["MetricProducer", "get_producer", "shutdown_producer"]
