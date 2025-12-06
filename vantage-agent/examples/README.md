# Vantage Agent Examples

This directory contains example applications demonstrating how to use the Vantage APM agent.

## Examples

### 1. Basic Requests (`demo_requests.py`)

Simple script showing how to instrument the `requests` library.

```bash
python demo_requests.py
```

### 2. Flask Application (`demo_flask.py`)

Flask web application with multiple endpoints.

```bash
# Install Flask first
pip install flask

# Run the app
python demo_flask.py
```

Then visit:

- http://localhost:5000/
- http://localhost:5000/api/users
- http://localhost:5000/api/slow

### 3. FastAPI Application (`demo_fastapi.py`)

FastAPI application with async endpoints.

```bash
# Install FastAPI and uvicorn first
pip install fastapi uvicorn

# Run the app
python demo_fastapi.py
```

Then visit:

- http://localhost:8001/
- http://localhost:8001/api/users
- http://localhost:8001/docs (Swagger UI)

## Prerequisites

Make sure the Vantage collector is running at `http://localhost:8000` before running these examples.

## What Gets Tracked

All examples automatically track:

- Request duration (milliseconds)
- HTTP method (GET, POST, etc.)
- Endpoint/URL
- Status code
- Errors (if any)

Metrics are batched and sent to the collector every 5 seconds.
