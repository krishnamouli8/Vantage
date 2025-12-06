"""
Metric data models for Vantage Agent.

Defines the structure of metrics collected by the agent.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Literal
from datetime import datetime
import time


MetricType = Literal["counter", "gauge", "histogram"]


@dataclass
class Metric:
    """
    Represents a single metric data point.
    
    Attributes:
        timestamp: Unix timestamp in milliseconds
        service_name: Name of the service
        metric_name: Name of the metric (e.g., "http.request.duration")
        metric_type: Type of metric (counter, gauge, histogram)
        value: Numeric value of the metric
        tags: Additional key-value tags
        endpoint: HTTP endpoint (for HTTP metrics)
        method: HTTP method (for HTTP metrics)
        status_code: HTTP status code (for HTTP metrics)
        duration_ms: Request duration in milliseconds
        error: Error message if request failed
    """
    
    timestamp: int
    service_name: str
    metric_name: str
    metric_type: MetricType
    value: float
    tags: dict[str, str] = field(default_factory=dict)
    endpoint: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    duration_ms: Optional[float] = None
    error: Optional[str] = None
    
    @classmethod
    def create_http_request_metric(
        cls,
        service_name: str,
        endpoint: str,
        method: str,
        status_code: int,
        duration_ms: float,
        tags: Optional[dict[str, str]] = None,
        error: Optional[str] = None,
    ) -> "Metric":
        """
        Create a metric for an HTTP request.
        
        Args:
            service_name: Name of the service
            endpoint: HTTP endpoint
            method: HTTP method (GET, POST, etc.)
            status_code: HTTP status code
            duration_ms: Request duration in milliseconds
            tags: Additional tags
            error: Error message if request failed
        
        Returns:
            Metric instance
        """
        return cls(
            timestamp=int(time.time() * 1000),
            service_name=service_name,
            metric_name="http.request.duration",
            metric_type="histogram",
            value=duration_ms,
            tags=tags or {},
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            duration_ms=duration_ms,
            error=error,
        )
    
    @classmethod
    def create_counter_metric(
        cls,
        service_name: str,
        metric_name: str,
        value: float = 1.0,
        tags: Optional[dict[str, str]] = None,
    ) -> "Metric":
        """
        Create a counter metric.
        
        Args:
            service_name: Name of the service
            metric_name: Name of the metric
            value: Counter value (default: 1.0)
            tags: Additional tags
        
        Returns:
            Metric instance
        """
        return cls(
            timestamp=int(time.time() * 1000),
            service_name=service_name,
            metric_name=metric_name,
            metric_type="counter",
            value=value,
            tags=tags or {},
        )
    
    @classmethod
    def create_gauge_metric(
        cls,
        service_name: str,
        metric_name: str,
        value: float,
        tags: Optional[dict[str, str]] = None,
    ) -> "Metric":
        """
        Create a gauge metric.
        
        Args:
            service_name: Name of the service
            metric_name: Name of the metric
            value: Gauge value
            tags: Additional tags
        
        Returns:
            Metric instance
        """
        return cls(
            timestamp=int(time.time() * 1000),
            service_name=service_name,
            metric_name=metric_name,
            metric_type="gauge",
            value=value,
            tags=tags or {},
        )
    
    def to_dict(self) -> dict:
        """Convert metric to dictionary, excluding None values."""
        data = asdict(self)
        return {k: v for k, v in data.items() if v is not None}
    
    def __repr__(self) -> str:
        """String representation of the metric."""
        return (
            f"Metric(name={self.metric_name}, type={self.metric_type}, "
            f"value={self.value}, service={self.service_name})"
        )


@dataclass
class MetricBatch:
    """
    A batch of metrics to be sent to the collector.
    
    Attributes:
        metrics: List of metrics
        service_name: Name of the service (all metrics in batch)
        environment: Deployment environment
        agent_version: Version of the agent
    """
    
    metrics: list[Metric]
    service_name: str
    environment: str = "development"
    agent_version: str = "0.1.0"
    
    def to_dict(self) -> dict:
        """Convert batch to dictionary for JSON serialization."""
        return {
            "metrics": [m.to_dict() for m in self.metrics],
            "service_name": self.service_name,
            "environment": self.environment,
            "agent_version": self.agent_version,
            "batch_size": len(self.metrics),
        }
    
    def __len__(self) -> int:
        """Return number of metrics in batch."""
        return len(self.metrics)
