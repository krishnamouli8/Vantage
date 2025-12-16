"""Prometheus metrics exporter utility.

Provides consistent Prometheus metrics collection and formatting
across all Vantage services. Outputs in standard Prometheus text format.
"""

import time
from collections import defaultdict
from threading import Lock
from typing import Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class MetricValue:
    """Single metric value with labels."""
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float | None = None


class Counter:
    """Prometheus Counter metric.
    
    A counter is a cumulative metric that only increases.
    Used for counting requests, errors, etc.
    """
    
    def __init__(self, name: str, description: str, labels: List[str] | None = None):
        """Initialize counter.
        
        Args:
            name: Metric name (should end with _total)
            description: Human-readable description
            labels: List of label names
        """
        self.name = name
        self.description = description
        self.label_names = labels or []
        self._values: Dict[tuple, float] = defaultdict(float)
        self._lock = Lock()
    
    def inc(self, amount: float = 1.0, labels: Dict[str, str] | None = None) -> None:
        """Increment counter by amount.
        
        Args:
            amount: Amount to increment (must be >= 0)
            labels: Label values
        """
        if amount < 0:
            raise ValueError("Counter can only increase")
        
        label_tuple = self._make_label_tuple(labels or {})
        with self._lock:
            self._values[label_tuple] += amount
    
    def _make_label_tuple(self, labels: Dict[str, str]) -> tuple:
        """Convert label dict to hashable tuple."""
        return tuple(labels.get(name, "") for name in self.label_names)
    
    def collect(self) -> List[MetricValue]:
        """Collect current metric values."""
        with self._lock:
            return [
                MetricValue(
                    value=value,
                    labels=dict(zip(self.label_names, label_tuple))
                )
                for label_tuple, value in self._values.items()
            ]


class Gauge:
    """Prometheus Gauge metric.
    
    A gauge can increase or decrease.
    Used for current values like queue depth, active connections.
    """
    
    def __init__(self, name: str, description: str, labels: List[str] | None = None):
        self.name = name
        self.description = description
        self.label_names = labels or []
        self._values: Dict[tuple, float] = defaultdict(float)
        self._lock = Lock()
    
    def set(self, value: float, labels: Dict[str, str] | None = None) -> None:
        """Set gauge to specific value."""
        label_tuple = self._make_label_tuple(labels or {})
        with self._lock:
            self._values[label_tuple] = value
    
    def inc(self, amount: float = 1.0, labels: Dict[str, str] | None = None) -> None:
        """Increment gauge."""
        label_tuple = self._make_label_tuple(labels or {})
        with self._lock:
            self._values[label_tuple] += amount
    
    def dec(self, amount: float = 1.0, labels: Dict[str, str] | None = None) -> None:
        """Decrement gauge."""
        self.inc(-amount, labels)
    
    def _make_label_tuple(self, labels: Dict[str, str]) -> tuple:
        return tuple(labels.get(name, "") for name in self.label_names)
    
    def collect(self) -> List[MetricValue]:
        with self._lock:
            return [
                MetricValue(
                    value=value,
                    labels=dict(zip(self.label_names, label_tuple))
                )
                for label_tuple, value in self._values.items()
            ]


class Histogram:
    """Prometheus Histogram metric.
    
    Tracks distribution of values in buckets.
    Used for request durations, response sizes, etc.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        buckets: List[float],
        labels: List[str] | None = None
    ):
        self.name = name
        self.description = description
        self.buckets = sorted(buckets)
        self.label_names = labels or []
        self._counts: Dict[tuple, Dict[float, int]] = defaultdict(
            lambda: {b: 0 for b in self.buckets + [float('inf')]}
        )
        self._sums: Dict[tuple, float] = defaultdict(float)
        self._lock = Lock()
    
    def observe(self, value: float, labels: Dict[str, str] | None = None) -> None:
        """Observe a value."""
        label_tuple = self._make_label_tuple(labels or {})
        with self._lock:
            # Update sum
            self._sums[label_tuple] += value
            
            # Update bucket counts
            for bucket in self.buckets + [float('inf')]:
                if value <= bucket:
                    self._counts[label_tuple][bucket] += 1
    
    def _make_label_tuple(self, labels: Dict[str, str]) -> tuple:
        return tuple(labels.get(name, "") for name in self.label_names)
    
    def collect(self) -> Dict[str, List[MetricValue]]:
        """Collect histogram metrics (buckets, sum, count)."""
        with self._lock:
            buckets = []
            sums = []
            counts = []
            
            for label_tuple, bucket_counts in self._counts.items():
                labels_dict = dict(zip(self.label_names, label_tuple))
                
                # Bucket counts (cumulative)
                cumulative = 0
                for bucket in self.buckets + [float('inf')]:
                    cumulative += bucket_counts[bucket]
                    bucket_labels = {**labels_dict, 'le': str(bucket)}
                    buckets.append(MetricValue(value=cumulative, labels=bucket_labels))
                
                # Sum
                sums.append(MetricValue(value=self._sums[label_tuple], labels=labels_dict))
                
                # Count
                counts.append(MetricValue(value=cumulative, labels=labels_dict))
            
            return {
                f'{self.name}_bucket': buckets,
                f'{self.name}_sum': sums,
                f'{self.name}_count': counts,
            }


class PrometheusExporter:
    """Prometheus metrics registry and exporter."""
    
    def __init__(self, namespace: str = "vantage"):
        """Initialize exporter with namespace prefix.
        
        Args:
            namespace: Prefix for all metric names (e.g., "vantage_collector")
        """
        self.namespace = namespace
        self.metrics: Dict[str, Any] = {}
    
    def counter(
        self,
        name: str,
        description: str,
        labels: List[str] | None = None
    ) -> Counter:
        """Create or get a Counter metric."""
        full_name = f"{self.namespace}_{name}"
        if full_name not in self.metrics:
            self.metrics[full_name] = Counter(full_name, description, labels)
        return self.metrics[full_name]
    
    def gauge(
        self,
        name: str,
        description: str,
        labels: List[str] | None = None
    ) -> Gauge:
        """Create or get a Gauge metric."""
        full_name = f"{self.namespace}_{name}"
        if full_name not in self.metrics:
            self.metrics[full_name] = Gauge(full_name, description, labels)
        return self.metrics[full_name]
    
    def histogram(
        self,
        name: str,
        description: str,
        buckets: List[float],
        labels: List[str] | None = None
    ) -> Histogram:
        """Create or get a Histogram metric."""
        full_name = f"{self.namespace}_{name}"
        if full_name not in self.metrics:
            self.metrics[full_name] = Histogram(full_name, description, buckets, labels)
        return self.metrics[full_name]
    
    def generate_text_format(self) -> str:
        """Generate Prometheus text format output.
        
        Returns:
            String in Prometheus exposition format
        """
        lines = []
        
        for metric_name, metric in self.metrics.items():
            # Add HELP line
            lines.append(f"# HELP {metric_name} {metric.description}")
            
            # Add TYPE line
            metric_type = metric.__class__.__name__.lower()
            lines.append(f"# TYPE {metric_name} {metric_type}")
            
            # Add metric values
            if isinstance(metric, Histogram):
                collected = metric.collect()
                for suffix, values in collected.items():
                    for mv in values:
                        labels_str = self._format_labels(mv.labels)
                        lines.append(f"{suffix}{{{labels_str}}} {mv.value}")
            else:
                for mv in metric.collect():
                    labels_str = self._format_labels(mv.labels)
                    if labels_str:
                        lines.append(f"{metric_name}{{{labels_str}}} {mv.value}")
                    else:
                        lines.append(f"{metric_name} {mv.value}")
        
        return "\n".join(lines) + "\n"
    
    def _format_labels(self, labels: Dict[str, str]) -> str:
        """Format labels for Prometheus output."""
        if not labels:
            return ""
        
        pairs = [f'{k}="{v}"' for k, v in sorted(labels.items())]
        return ",".join(pairs)
