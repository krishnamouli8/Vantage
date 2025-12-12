# Vantage Observability Platform

A full-stack observability platform for monitoring distributed applications, featuring auto-instrumentation, high-throughput metric ingestion, time-series storage, and real-time visualization dashboards.

## Overview

Vantage is a complete observability solution that automatically collects, processes, stores, and visualizes application performance metrics. Built with modern distributed systems patterns, it demonstrates event-driven architecture, async processing, and real-time data streaming.

**Key Components:**

- **Python APM Agent**: Auto-instruments applications with minimal overhead
- **Ingestion Service**: FastAPI-based collector with Kafka integration
- **Storage Layer**: Consumer worker with SQLite time-series database
- **Query API**: RESTful API with WebSocket support for real-time updates
- **Dashboard**: React-based UI with dark/light themes and live visualizations

## Architecture

```
┌─────────────────┐
│  Python App     │  User Application with Agent
│  (with agent)   │
└────────┬────────┘
         │ HTTP POST /v1/metrics
         ▼
┌─────────────────┐
│   Collector     │  FastAPI + Pydantic Validation
│   (Port 8000)   │
└────────┬────────┘
         │ Async Kafka Producer
         ▼
┌─────────────────┐
│   Redpanda      │  Kafka-compatible Message Queue
│   (Port 9092)   │  Topic: metrics-raw
└────────┬────────┘
         │ Consumer Group
         ▼
┌─────────────────┐
│    Worker       │  Metric Consumer & Processor
│                 │  Batch Insert to Database
└────────┬────────┘
         │ SQLite Writes
         ▼
┌─────────────────┐
│    SQLite       │  Time-Series Metrics Storage
│   (metrics.db)  │  Indexed by timestamp & service
└────────┬────────┘
         │ Query API
         ▼
┌─────────────────┐
│   Query API     │  REST + WebSocket
│   (Port 8001)   │
└────────┬────────┘
         │ HTTP + WS
         ▼
┌─────────────────┐
│   Dashboard     │  React + TypeScript
│   (Port 3000)   │  Real-time Visualization
└─────────────────┘
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.10+ (for local agent development)
- Node.js 18+ (for dashboard development)

### Running the Platform

```bash
# Start all services
docker-compose up -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f
```

**Services:**

- Dashboard: http://localhost:3000
- Collector API: http://localhost:8000
- Query API: http://localhost:8001
- API Docs: http://localhost:8000/docs
- Redpanda Console: http://localhost:8080

### Testing the Agent

```bash
cd vantage-agent

# Install the agent
pip install -e .

# Run the test script
python test_agent.py
```

The test script will send sample metrics through the entire pipeline. You should see them appear in the dashboard within 2-3 seconds.

## Features

### Auto-Instrumentation Agent

The Python APM agent automatically instruments popular libraries with zero code changes:

```python
from vantage_agent import init_agent

# Initialize once at startup
init_agent(
    service_name="my-api",
    collector_url="http://localhost:8000",
    auto_instrument=["requests", "flask", "fastapi"]
)

# All HTTP requests are now automatically tracked
import requests
response = requests.get("https://api.example.com/users")
# Metric sent: endpoint=/users, duration=123ms, status=200
```

**Supported Libraries:**

- `requests` - HTTP client library
- `httpx` - Modern async HTTP client
- `Flask` - Web framework
- `FastAPI` - Modern async web framework

### High-Throughput Ingestion

The collector service handles metric ingestion at scale:

- Async Kafka producer for non-blocking writes
- Pydantic validation for data integrity
- Batch processing support (up to 1000 metrics/request)
- GZip compression for reduced network overhead
- Health check endpoints for monitoring

### Time-Series Storage

Metrics are stored in SQLite with time-series optimizations:

- Indexed by timestamp and service name for fast queries
- Batch inserts for write efficiency
- Supports time-range filtering and aggregations
- Simple deployment with no external database dependencies

### Real-Time Dashboard

Modern React-based UI with professional design:

- **Dark/Light Mode**: Theme switching with persistence
- **Real-Time Updates**: WebSocket streaming for live metrics
- **Interactive Charts**: Area charts with Recharts library
- **Service Filtering**: Filter metrics by service name
- **Time Range Selection**: View metrics from last hour to 24 hours
- **Responsive Design**: Works on desktop, tablet, and mobile

## Project Structure

```
Vantage/
├── vantage-agent/          # Python APM agent package
│   ├── vantage_agent/      # Main package code
│   │   ├── instrumentation/  # Library patches
│   │   ├── metrics/          # Metric collection
│   │   └── utils/            # Utilities
│   ├── tests/              # Unit tests
│   ├── examples/           # Demo applications
│   └── README.md
├── vantage-collector/      # Ingestion service
│   ├── app/                # FastAPI application
│   │   ├── api/            # API endpoints
│   │   ├── models/         # Data models
│   │   └── queue/          # Kafka producer
│   ├── tests/              # API tests
│   └── Dockerfile
├── vantage-worker/         # Consumer worker
│   ├── worker/             # Consumer code
│   └── Dockerfile
├── vantage-api/            # Query API service
│   ├── api/                # Query endpoints
│   └── Dockerfile
├── vantage-dashboard/      # React frontend
│   ├── src/                # React components
│   │   ├── components/     # UI components
│   │   ├── hooks/          # Custom hooks
│   │   └── api/            # API client
│   └── Dockerfile
├── docker-compose.yml      # Service orchestration
└── README.md
```

## Development

### Agent Development

```bash
cd vantage-agent

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=vantage_agent --cov-report=html
```

### Collector Development

```bash
cd vantage-collector

# Install dependencies
pip install -r requirements.txt

# Run locally
python -m app.main

# Run tests
pytest tests/ -v
```

### Dashboard Development

```bash
cd vantage-dashboard

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

## Testing

### Running Tests

```bash
# Agent tests
cd vantage-agent && pytest

# Collector tests
cd vantage-collector && pytest

# Worker tests
cd vantage-worker && pytest

# API tests
cd vantage-api && pytest

# All tests with coverage
./run_tests.sh
```

### Integration Testing

```bash
# Run end-to-end integration test
python test_integration.py
```

This script tests the complete pipeline from agent instrumentation through to
The dashboard will automatically detect and display these metrics in real-time.

## Authentication

**Optional but recommended for production.**

Vantage supports API key authentication for securing the collector and query API.

### Setup API Keys

```bash
# Copy environment template
cp .env.example .env

# Generate secure API keys
export API_KEY=$(openssl rand -hex 32)

# Enable authentication
export VANTAGE_AUTH_ENABLED=true
export API_AUTH_ENABLED=true

# Start with authentication
docker-compose up -d
```

### Using Authenticated APIs

**Collector (metrics ingestion):**

```bash
curl -X POST http://localhost:8000/v1/metrics \
  -H "X-API-Key: your-secret-api-key" \
  -H "Content-Type: application/json" \
  -d @metrics.json
```

**Query API:**

```bash
curl -H "X-API-Key: your-secret-api-key" \
  http://localhost:8001/api/metrics/timeseries
```

**Python Agent:**

```python
from vantage_agent import init_agent

init_agent(
    service_name="my-service",
    collector_url="http://localhost:8000",
    api_key="your-secret-api-key",  # Add API key
    auto_instrument=["requests"]
)
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for production security best practices.

## Configuration

### Environment Variables

**Collector:**

- `VANTAGE_KAFKA_BOOTSTRAP_SERVERS` - Kafka connection (default: `localhost:9092`)
- `VANTAGE_KAFKA_TOPIC` - Topic name (default: `metrics-raw`)
- `VANTAGE_DEBUG` - Enable debug logging (default: `false`)

**Worker:**

- `WORKER_KAFKA_BOOTSTRAP_SERVERS` - Kafka connection
- `WORKER_KAFKA_TOPIC` - Topic to consume from
- `WORKER_DATABASE_PATH` - SQLite database path

**API:**

- `API_DATABASE_PATH` - SQLite database path
- `API_CORS_ORIGINS` - Allowed CORS origins

### Agent Configuration

```python
init_agent(
    service_name="my-service",           # Required: service identifier
    collector_url="http://localhost:8000", # Collector endpoint
    auto_instrument=["requests", "flask"], # Libraries to instrument
    flush_interval=5,                     # Seconds between flushes
    batch_size=100,                       # Metrics per batch
    max_queue_size=10000,                 # Max queued metrics
    debug=False,                          # Debug logging
)
```

## API Reference

### Ingestion API

**POST /v1/metrics** - Ingest metric batch

```bash
curl -X POST http://localhost:8000/v1/metrics \
  -H "Content-Type: application/json" \
  -d '{
    "metrics": [{
      "timestamp": 1701878400000,
      "service_name": "api-gateway",
      "metric_name": "http.request.duration",
      "value": 123.45,
      "endpoint": "/api/users",
      "method": "GET",
      "status_code": 200
    }]
  }'
```

**GET /v1/stats** - Get collector statistics

**GET /health** - Health check endpoint

### Query API

**GET /api/metrics/timeseries** - Get time-series data

- Query params: `service` (optional), `range` (seconds, default: 3600)

**GET /api/metrics/aggregated** - Get aggregated metrics

- Query params: `service` (optional), `range` (seconds)

**GET /api/services** - List all services

**WS /ws/metrics** - WebSocket for real-time metric updates

## Known Limitations

This project is a demonstration platform and has several limitations compared to production observability systems:

### Storage

- **SQLite for time-series data**: Works for demos but not suitable for high-volume production use
  - No support for distributed queries or horizontal scaling
  - Limited to single-node deployment
  - No automatic data retention or rollup strategies
  - Performance degrades with database growth

### Security

- **No authentication or authorization**: All endpoints are publicly accessible
- **No API key management**: Cannot restrict access to collector or query API
- **No encryption**: Metrics transmitted in plain HTTP
- **No rate limiting**: Vulnerable to abuse

### Monitoring & Operations

- **No self-monitoring**: The platform doesn't monitor its own health metrics
- **Limited observability**: No metrics about collector throughput, worker lag, or queue depth
- **No alerting**: No support for threshold-based alerts or notifications
- **Basic error handling**: Limited retry logic and no dead letter queues

### Features

- **No metric cardinality limits**: Can experience cardinality explosion with high-variance tags
- **No downsampling or aggregation**: All raw metrics stored indefinitely
- **Limited query capabilities**: No complex aggregations, percentiles, or histogram queries
- **Single region**: No support for multi-region deployments

### Scale

- **Performance claims untested**: Throughput numbers are estimates, not benchmarked
- **No load testing**: System behavior under high load is unknown
- **Limited batch sizes**: Worker processes fixed batch sizes without backpressure handling

### Recommendations for Production Use

If adapting this for production, consider:

- Replace SQLite with ClickHouse or TimescaleDB for time-series storage
- Implement authentication (OAuth2, API keys) and HTTPS
- Add comprehensive monitoring and alerting
- Implement data retention policies and downsampling
- Add rate limiting and cardinality protection
- Conduct thorough load testing and performance optimization
- Implement proper error recovery and dead letter queues
- Add support for distributed tracing and logs (not just metrics)

## Technology Stack

- **Backend**: Python 3.10+, FastAPI, aiokafka
- **Frontend**: React 18, TypeScript, Recharts
- **Message Queue**: Redpanda (Kafka-compatible)
- **Database**: SQLite
- **Infrastructure**: Docker, Docker Compose
- **Testing**: pytest, pytest-asyncio

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

### Development Setup

1. Clone the repository
2. Run `docker-compose up -d` to start infrastructure
3. Follow development instructions for each component
4. Run tests before submitting PRs

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

This project was built as a learning exercise to understand observability platforms like Datadog, New Relic, and OpenTelemetry. It demonstrates distributed systems concepts including event-driven architecture, async processing, and real-time data streaming.
