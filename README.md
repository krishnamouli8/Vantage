# Vantage Observability Platform

A full-stack observability platform for monitoring distributed applications with real-time metric collection, storage, and visualization.

## Overview

Vantage automatically collects, processes, and visualizes application performance metrics through a complete data pipeline:

**Python APM Agent** → **Collector (FastAPI)** → **Redpanda (Kafka)** → **Worker** → **SQLite** → **Query API** → **React Dashboard**

## Tech Stack

**Backend:**

- Python 3.10+ with FastAPI
- aiokafka for async message processing
- SQLite for time-series storage
- Pydantic for data validation

**Frontend:**

- React 18 with TypeScript
- Recharts for visualizations
- WebSocket for real-time updates

**Infrastructure:**

- Redpanda (Kafka-compatible message queue)
- Docker & Docker Compose
- Nginx for dashboard serving

## Key Features

- **Auto-instrumentation**: Python agent automatically tracks HTTP requests, database calls, and more
- **High-throughput ingestion**: Async Kafka producer with batch processing
- **Real-time visualization**: WebSocket-based dashboard with live metric updates
- **API authentication**: Optional API key protection for production use
- **Time-series storage**: Indexed SQLite database optimized for time-range queries

## Using the Agent

```python
from vantage_agent import init_agent

# Initialize once at application startup
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

**Supported Libraries:** requests, httpx, Flask, FastAPI

## How It Works

Vantage implements a complete observability pipeline with event-driven architecture:

### 1. **Metric Collection**

The Python agent runs inside your application and automatically tracks every HTTP request, database query, and external API call. It captures timing, status codes, and metadata without requiring code changes.

### 2. **Async Ingestion**

Metrics are sent to the Collector service via HTTP POST. The Collector validates data using Pydantic schemas and immediately publishes to Redpanda (Kafka), ensuring zero blocking and high throughput.

### 3. **Stream Processing**

The Worker service consumes metrics from Redpanda in real-time, processes them in batches, and stores them in a time-series optimized SQLite database with proper indexing for fast queries.

### 4. **Query & Visualization**

The Query API provides REST endpoints and WebSocket connections for retrieving metrics. The React dashboard subscribes to live updates and displays interactive charts showing request rates, response times, error rates, and service performance.

## Why Vantage?

**For Developers:**

- **Zero Code Changes**: Auto-instrumentation means you just initialize the agent and everything is tracked automatically
- **Instant Visibility**: See your application's performance in real-time without complex setup
- **Debug Production Issues**: Quickly identify slow endpoints, error spikes, and performance bottlenecks

**For System Architecture:**

- **Event-Driven Design**: Kafka-based architecture ensures metrics never block your application
- **Horizontal Scalability**: Add more workers to handle increased metric volume
- **Decoupled Components**: Each service can be scaled, updated, or replaced independently

**For Learning:**

- **Production Patterns**: Demonstrates async processing, message queues, and time-series storage
- **Modern Stack**: Built with FastAPI, React, TypeScript, and containerized with Docker
- **Real-World Use Case**: Mirrors how professional observability platforms like Datadog and New Relic work

## What You Get

- 📊 **Real-time Dashboards**: Live visualization of your application metrics
- 🔍 **Service Monitoring**: Track multiple services and compare their performance
- ⚡ **Fast Queries**: Indexed time-series database for quick historical analysis
- 🔒 **Secure by Default**: API key authentication protects your metrics
- 🐳 **Easy Deployment**: Everything runs in Docker with a single command

## License

MIT License - see [LICENSE](LICENSE) file for details.
