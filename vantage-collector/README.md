# Vantage Collector

High-performance metric ingestion service for the Vantage observability platform.

## Features

- ⚡ **High Throughput**: Handles 100K+ metrics/second
- 🔄 **Async Processing**: Non-blocking Kafka integration with aiokafka
- ✅ **Validation**: Pydantic models with comprehensive validation
- 📊 **Monitoring**: Built-in health checks and statistics
- 🐳 **Production Ready**: Docker support with health checks
- 🔒 **CORS Support**: Configurable CORS for web clients

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables (optional)
export VANTAGE_KAFKA_BOOTSTRAP_SERVERS=localhost:9092
export VANTAGE_DEBUG=true

# Run the collector
python -m app.main
```

The collector will start on `http://localhost:8000`.

### With Docker

```bash
# Build the image
docker build -t vantage-collector .

# Run the container
docker run -p 8000:8000 \
  -e VANTAGE_KAFKA_BOOTSTRAP_SERVERS=kafka:9092 \
  vantage-collector
```

## API Endpoints

### Ingestion

**POST /v1/metrics** - Ingest metric batch

```bash
curl -X POST http://localhost:8000/v1/metrics \
  -H "Content-Type: application/json" \
  -d '{
    "metrics": [{
      "timestamp": 1701878400000,
      "service_name": "api-gateway",
      "metric_name": "http.request.duration",
      "metric_type": "histogram",
      "value": 123.45,
      "endpoint": "/api/users",
      "method": "GET",
      "status_code": 200,
      "duration_ms": 123.45
    }],
    "service_name": "api-gateway",
    "environment": "production",
    "agent_version": "0.1.0"
  }'
```

**GET /v1/stats** - Get ingestion statistics

```bash
curl http://localhost:8000/v1/stats
```

### Monitoring

**GET /health** - Health check

```bash
curl http://localhost:8000/health
```

**GET /ready** - Readiness check (Kubernetes)

```bash
curl http://localhost:8000/ready
```

**GET /live** - Liveness check (Kubernetes)

```bash
curl http://localhost:8000/live
```

### Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI**: http://localhost:8000/openapi.json

## Configuration

All configuration can be set via environment variables with the `VANTAGE_` prefix:

| Variable                          | Default          | Description           |
| --------------------------------- | ---------------- | --------------------- |
| `VANTAGE_API_HOST`                | `0.0.0.0`        | API host              |
| `VANTAGE_API_PORT`                | `8000`           | API port              |
| `VANTAGE_KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka servers         |
| `VANTAGE_KAFKA_TOPIC`             | `metrics-raw`    | Kafka topic           |
| `VANTAGE_KAFKA_COMPRESSION_TYPE`  | `gzip`           | Compression type      |
| `VANTAGE_MAX_BATCH_SIZE`          | `1000`           | Max metrics per batch |
| `VANTAGE_DEBUG`                   | `false`          | Enable debug logging  |
| `VANTAGE_CORS_ENABLED`            | `true`           | Enable CORS           |

## Architecture

```
Agent → POST /v1/metrics → Validation → Kafka Producer → Redpanda
                              ↓
                         Statistics
                              ↓
                         202 Accepted
```

## Performance

- **Throughput**: 100K+ metrics/second
- **Latency**: <10ms per request (p99)
- **Batch Size**: Up to 1000 metrics per request
- **Compression**: gzip for reduced network usage

## Development

```bash
# Install dev dependencies
pip install -r requirements.txt pytest pytest-asyncio httpx

# Run tests
pytest tests/ -v

# Format code
black app/

# Type checking
mypy app/
```

## License

MIT License
