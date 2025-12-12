#!/usr/bin/env python3
"""
Send test metrics to Vantage Collector.

This script sends realistic HTTP request metrics to test the complete pipeline:
Agent → Collector → Kafka → Worker → SQLite → API → Dashboard
"""

import requests
import time
import random
from typing import List, Dict

# Configuration
COLLECTOR_URL = "http://localhost:8000"
SERVICE_NAME = "test-web-app"
ENVIRONMENT = "production"

# Test endpoints to simulate
ENDPOINTS = [
    ("/api/users", ["GET", "POST"]),
    ("/api/products", ["GET", "POST", "PUT", "DELETE"]),
    ("/api/orders", ["GET", "POST"]),
    ("/api/auth/login", ["POST"]),
    ("/api/auth/logout", ["POST"]),
    ("/health", ["GET"]),
    ("/metrics", ["GET"]),
]


def generate_metric(endpoint: str, method: str) -> Dict:
    """Generate a realistic HTTP request metric."""
    # Realistic duration distribution
    if endpoint == "/health":
        duration = random.uniform(1, 5)  # Fast health checks
    elif endpoint.startswith("/api/auth"):
        duration = random.uniform(50, 200)  # Auth takes longer
    else:
        duration = random.uniform(10, 100)  # Normal API calls
    
    # Realistic status code distribution (mostly 2xx, some 4xx, rare 5xx)
    rand = random.random()
    if rand < 0.85:
        status_code = 200
    elif rand < 0.92:
        status_code = random.choice([200, 201, 204])
    elif rand < 0.97:
        status_code = random.choice([400, 401, 404])
    else:
        status_code = random.choice([500, 502, 503])
    
    return {
        "timestamp": int(time.time() * 1000),
        "service_name": SERVICE_NAME,
        "metric_name": "http.request.duration",
        "metric_type": "histogram",
        "value": duration,
        "endpoint": endpoint,
        "method": method,
        "status_code": status_code,
        "duration_ms": duration,
    }


def send_metrics_batch(metrics: List[Dict]) -> bool:
    """Send a batch of metrics to the collector."""
    payload = {
        "metrics": metrics,
        "service_name": SERVICE_NAME,
        "environment": ENVIRONMENT,
    }
    
    try:
        response = requests.post(
            f"{COLLECTOR_URL}/v1/metrics",
            json=payload,
            timeout=5,
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending metrics: {e}")
        return False


def check_collector_health() -> bool:
    """Check if the collector is healthy."""
    try:
        response = requests.get(f"{COLLECTOR_URL}/health", timeout=5)
        data = response.json()
        return data.get("status") == "healthy"
    except requests.exceptions.RequestException:
        return False


def main():
    print("=" * 70)
    print("VANTAGE PLATFORM - TEST METRIC GENERATOR")
    print("=" * 70)
    
    # Check collector health
    print("\n1. Checking collector health...")
    if not check_collector_health():
        print("   ❌ Collector is not healthy or not accessible")
        print("   Make sure services are running: docker compose up -d")
        return
    print("   ✓ Collector is healthy")
    
    # Send test metrics
    print("\n2. Sending test metrics...")
    total_sent = 0
    batches = 10
    metrics_per_batch = 50
    
    for batch_num in range(batches):
        metrics = []
        for _ in range(metrics_per_batch):
            endpoint, methods = random.choice(ENDPOINTS)
            method = random.choice(methods)
            metrics.append(generate_metric(endpoint, method))
        
        if send_metrics_batch(metrics):
            total_sent += len(metrics)
            print(f"   ✓ Batch {batch_num + 1}/{batches}: Sent {len(metrics)} metrics (Total: {total_sent})")
        else:
            print(f"   ❌ Batch {batch_num + 1}/{batches}: Failed to send")
        
        # Small delay between batches
        time.sleep(0.5)
    
    print(f"\n✅ Successfully sent {total_sent} metrics to the collector!")
    print("\nNext steps:")
    print("  1. Wait a few seconds for processing")
    print("  2. Check the dashboard: http://localhost:3000")
    print("  3. Run verification script: python verify_platform.py")
    print("  4. View Redpanda console: http://localhost:8080")
    

if __name__ == "__main__":
    main()
