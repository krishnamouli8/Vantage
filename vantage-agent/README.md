# Vantage Agent

A production-grade, lightweight APM (Application Performance Monitoring) agent for Python applications. Auto-instruments your code with **<1ms overhead** per request.

## Features

- 🚀 **Zero-Code Instrumentation**: Just 2 lines to start monitoring
- ⚡ **Ultra-Low Overhead**: <1ms per request using non-blocking queues
- 🔌 **Auto-Instrumentation**: Supports `requests`, `httpx`, Flask, and FastAPI
- 📊 **Rich Metrics**: Request duration, status codes, endpoints, errors
- 🧵 **Thread-Safe**: Lock-free queue with background exporter
- 🔄 **Reliable**: Exponential backoff retry logic
- 🎯 **Production-Ready**: Graceful shutdown, error handling, structured logging

## Installation

```bash
pip install vantage-agent
```

## Quick Start

### Basic Usage

```python
from vantage_agent import init_agent

# Initialize the agent (call this once at app startup)
init_agent(
    service_name="my-api",
    collector_url="http://localhost:8000",
    auto_instrument=["requests", "flask"]
)

# That's it! All HTTP requests are now automatically tracked
```

### With Requests Library

```python
import requests
from vantage_agent import init_agent

# Initialize agent
init_agent(
    service_name="my-service",
    auto_instrument=["requests"]
)

# All requests are automatically tracked
response = requests.get("https://api.example.com/users")
# Metric automatically sent: endpoint=/users, duration=123ms, status=200
```

### With Flask

```python
from flask import Flask
from vantage_agent import init_agent

app = Flask(__name__)

# Initialize agent
init_agent(
    service_name="flask-api",
    auto_instrument=["flask", "requests"]
)

@app.route("/api/users")
def get_users():
    # This request is automatically tracked
    return {"users": []}

# All incoming requests are automatically tracked
```

### With FastAPI

```python
from fastapi import FastAPI
from vantage_agent import init_agent

# Initialize agent BEFORE creating FastAPI app
init_agent(
    service_name="fastapi-api",
    auto_instrument=["fastapi", "httpx"]
)

app = FastAPI()

@app.get("/api/users")
async def get_users():
    # All incoming requests are automatically tracked
    return {"users": []}
```

## Configuration

```python
init_agent(
    service_name="my-service",           # Required: service identifier
    collector_url="http://localhost:8000", # Collector API URL
    auto_instrument=["requests", "flask"], # Libraries to instrument
    flush_interval=5,                     # Seconds between flushes (default: 5)
    batch_size=100,                       # Metrics per batch (default: 100)
    max_queue_size=10000,                 # Max metrics in queue (default: 10000)
    environment="production",             # Environment name
    tags={"region": "us-east-1"},        # Additional tags
    debug=False,                          # Enable debug logging
)
```

### Environment Variables

- `VANTAGE_COLLECTOR_URL`: Override collector URL
- `VANTAGE_ENVIRONMENT`: Set environment (e.g., "production", "staging")
- `VANTAGE_DEBUG`: Enable debug logging (set to "true", "1", or "yes")

## Supported Libraries

| Library    | Type                     | Status       |
| ---------- | ------------------------ | ------------ |
| `requests` | HTTP Client              | ✅ Supported |
| `httpx`    | HTTP Client (sync/async) | ✅ Supported |
| `Flask`    | Web Framework            | ✅ Supported |
| `FastAPI`  | Web Framework            | ✅ Supported |

## Architecture

```
┌─────────────────┐
│  Your App Code  │
└────────┬────────┘
         │ (instrumented)
         ▼
┌─────────────────┐
│ Metric Collector│ ◄── Thread-safe queue (non-blocking)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Background      │ ◄── Daemon thread (flushes every 5s)
│ Exporter        │
└────────┬────────┘
         │ (HTTP POST)
         ▼
┌─────────────────┐
│ Vantage         │
│ Collector API   │
└─────────────────┘
```

## Performance

- **Overhead**: <1ms per instrumented request
- **Memory**: ~10MB for 10,000 queued metrics
- **Throughput**: Handles 100K+ requests/second

## Development

```bash
# Clone the repository
git clone https://github.com/vantage/vantage-agent.git
cd vantage-agent

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=vantage_agent --cov-report=html

# Format code
black vantage_agent/

# Type checking
mypy vantage_agent/
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Support

- Documentation: https://docs.vantage.dev
- Issues: https://github.com/vantage/vantage-agent/issues
- Email: support@vantage.dev
