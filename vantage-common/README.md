# Vantage Common Utilities

Shared utilities and components used across all Vantage services.

## Components

- **exceptions.py**: Custom exception hierarchy for consistent error handling
- **constants.py**: Named constants to replace magic numbers
- **prometheus_exporter.py**: Prometheus metrics collection and formatting
- **structured_logging.py**: Structured JSON logging with structlog

## Installation

```bash
pip install -e ./vantage-common
```

## Usage

### Exceptions

```python
from vantage_common.exceptions import DatabaseConnectionError

try:
    connect_to_database()
except Exception as e:
    raise DatabaseConnectionError(
        "Failed to connect to ClickHouse",
        details={"host": "localhost", "port": 9000}
    )
```

### Constants

```python
from vantage_common.constants import BATCH_SIZE_DEFAULT, MAX_RETRY_ATTEMPTS

batch = metrics[:BATCH_SIZE_DEFAULT]
for attempt in range(MAX_RETRY_ATTEMPTS):
    # Retry logic
    pass
```

### Prometheus Metrics

```python
from vantage_common.prometheus_exporter import PrometheusExporter
from vantage_common.constants import LATENCY_HISTOGRAM_BUCKETS

exporter = PrometheusExporter("vantage_collector")

# Create metrics
requests_total = exporter.counter(
    "requests_total",
    "Total requests received",
    labels=["method", "endpoint"]
)

request_duration = exporter.histogram(
    "request_duration_seconds",
    "Request duration in seconds",
    buckets=LATENCY_HISTOGRAM_BUCKETS,
    labels=["endpoint"]
)

# Use metrics
requests_total.inc(labels={"method": "POST", "endpoint": "/v1/metrics"})
request_duration.observe(0.123, labels={"endpoint": "/v1/metrics"})

# Export (for /metrics endpoint)
print(exporter.generate_text_format())
```

### Structured Logging

```python
from vantage_common.structured_logging import setup_logging, get_logger, bind_trace_id

# Setup once at application startup
setup_logging("vantage-collector", level="INFO", json_output=True)

# Get logger
logger = get_logger(__name__)

# Log with structured data
logger.info("request_received", method="POST", endpoint="/v1/metrics", count=100)

# Bind trace ID for distributed tracing
bind_trace_id("abc-123-def")
logger.info("processing_batch")  # Will include trace_id in output
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .
ruff check .
```
