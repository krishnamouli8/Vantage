"""Load testing for Vantage Platform.

Simulates high-load scenarios to validate performance and scalability.
Uses Locust for distributed load generation.
"""

from locust import HttpUser, task, between, events
import random
import time
import json


class VantageUser(HttpUser):
    """Simulates a user sending metrics to Vantage."""
    
    wait_time = between(0.1, 0.5)  # 100-500ms between requests
    host = "http://localhost:8000"
    
    def on_start(self):
        """Called when a user starts."""
        self.services = [
            "web-api",
            "auth-service",
            "payment-service",
            "notification-service",
            "analytics-service"
        ]
        
        self.metrics = [
            "http.request.duration",
            "http.request.count",
            "http.error.count",
            "cache.hit.rate",
            "database.query.duration"
        ]
        
    def _generate_metrics(self, count=10):
        """Generate random metrics for testing."""
        timestamp = int(time.time() * 1000)
        
        metrics = []
        for _ in range(count):
            metrics.append({
                "timestamp": timestamp,
                "service_name": random.choice(self.services),
                "metric_name": random.choice(self.metrics),
                "metric_type": random.choice(["gauge", "counter"]),
                "value": random.uniform(10, 1000),
                "endpoint": random.choice(["/api/users", "/api/posts", "/api/auth"]),
                "method": random.choice(["GET", "POST", "PUT", "DELETE"]),
                "status_code": random.choice([200, 201, 400, 404, 500]),
                "duration_ms": random.uniform(10, 500),
                "tags": {
                    "environment": "load-test",
                    "region": random.choice(["us-east-1", "us-west-2", "eu-west-1"])
                }
            })
        
        return metrics
    
    @task(weight=10)
    def send_single_metric(self):
        """Send a single metric (most common scenario)."""
        payload = {
            "metrics": self._generate_metrics(1)
        }
        
        with self.client.post(
            "/v1/metrics",
            json=payload,
            catch_response=True,
            name="POST /v1/metrics (single)"
        ) as response:
            if response.status_code == 202:
                response.success()
            elif response.status_code == 429:
                # Rate limited - expected under high load
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")
    
    @task(weight=5)
    def send_batch_metrics(self):
        """Send batch of metrics (10-100)."""
        batch_size = random.randint(10, 100)
        payload = {
            "metrics": self._generate_metrics(batch_size)
        }
        
        with self.client.post(
            "/v1/metrics",
            json=payload,
            catch_response=True,
            name=f"POST /v1/metrics (batch-{batch_size})"
        ) as response:
            if response.status_code == 202:
                response.success()
            elif response.status_code == 429:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")
    
    @task(weight=3)
    def check_health(self):
        """Check health endpoint."""
        self.client.get("/health", name="GET /health")
    
    @task(weight=1)
    def get_metrics_prometheus(self):
        """Fetch Prometheus metrics."""
        self.client.get("/metrics", name="GET /metrics")


class VantageAPIUser(HttpUser):
    """Simulates a user querying the API."""
    
    wait_time = between(1, 3)  # 1-3s between queries
    host = "http://localhost:5000"
    
    def on_start(self):
        """Called when a user starts."""
        self.services = ["web-api", "auth-service", "payment-service"]
    
    @task(weight=5)
    def query_timeseries(self):
        """Query timeseries data."""
        params = {
            "service": random.choice(self.services),
            "metric": "http.request.duration",
            "start_time": int(time.time()) - 3600,  # Last hour
            "end_time": int(time.time())
        }
        
        self.client.get(
            "/api/metrics/timeseries",
            params=params,
            name="GET /api/metrics/timeseries"
        )
    
    @task(weight=3)
    def query_aggregated(self):
        """Query aggregated metrics."""
        params = {
            "service": random.choice(self.services),
            "start_time": int(time.time()) - 3600,
            "end_time": int(time.time()),
            "aggregation": random.choice(["avg", "sum", "max"])
        }
        
        self.client.get(
            "/api/metrics/aggregated",
            params=params,
            name="GET /api/metrics/aggregated"
        )
    
    @task(weight=1)
    def execute_vql(self):
        """Execute VQL query."""
        query = f"""
        SELECT service_name, AVG(value) as avg_value
        FROM metrics
        WHERE timestamp > {int(time.time() - 3600)}
        GROUP BY service_name
        LIMIT 100
        """
        
        self.client.post(
            "/vql/execute",
            json={"query": query},
            name="POST /vql/execute"
        )


# Test scenarios
class NormalLoad(VantageUser):
    """Normal load: 100 users, 5min"""
    weight = 1


class PeakLoad(VantageUser):
    """Peak load: 500 users, 2min bursts"""
    weight = 2
    wait_time = between(0.01, 0.1)  # Very fast


class SustainedLoad(VantageUser):
    """Sustained load: 200 users, 30min"""
    weight = 1
    wait_time = between(0.5, 1.5)


# Event handlers for reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    print("\n" + "=" * 80)
    print("VANTAGE LOAD TEST STARTED")
    print("=" * 80)
    print(f"Target: {environment.host}")
    print(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")
    print("=" * 80 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops."""
    stats = environment.stats
    
    print("\n" + "=" * 80)
    print("VANTAGE LOAD TEST COMPLETED")
    print("=" * 80)
    
    print(f"\nTotal Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Failure Rate: {stats.total.fail_ratio * 100:.2f}%")
    
    print(f"\nLatency:")
    print(f"  Median: {stats.total.median_response_time}ms")
    print(f"  95th percentile: {stats.total.get_response_time_percentile(0.95)}ms")
    print(f"  99th percentile: {stats.total.get_response_time_percentile(0.99)}ms")
    
    print(f"\nThroughput: {stats.total.current_rps:.2f} req/s")
    
    print("=" * 80 + "\n")
    
    # Performance assertions
    if stats.total.fail_ratio > 0.01:  # > 1% failure rate
        print("⚠️  WARNING: Failure rate exceeded 1%")
    
    if stats.total.get_response_time_percentile(0.99) > 1000:  # p99 > 1s
        print("⚠️  WARNING: p99 latency exceeded 1 second")
    
    if stats.total.current_rps < 100:  # < 100 req/s
        print("⚠️  WARNING: Throughput below 100 req/s")


# Usage:
# 
# Normal load test (100 users, 5 minutes):
#   locust -f load_test.py --users 100 --spawn-rate 10 --run-time 5m --headless
#
# Peak load test (1000 users, burst):
#   locust -f load_test.py --users 1000 --spawn-rate 100 --run-time 2m --headless
#
# Sustained load test (500 users, 30 minutes):
#   locust -f load_test.py --users 500 --spawn-rate 50 --run-time 30m --headless
#
# With web UI:
#   locust -f load_test.py
#   # Open http://localhost:8089
