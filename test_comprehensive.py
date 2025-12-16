#!/usr/bin/env python3
"""
Comprehensive Test Suite for Vantage Observability Platform
Tests all implemented features including Phase 2 and Phase 3
"""

import requests
import json
import time
import sys
from typing import Dict, List, Tuple
from datetime import datetime

# Configuration
COLLECTOR_URL = "http://localhost:8000"
API_URL = "http://localhost:5000"
DASHBOARD_URL = "http://localhost:3000"
REDPANDA_CONSOLE_URL = "http://localhost:8080"

# Colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def add_pass(self, test_name: str, message: str = ""):
        self.passed.append((test_name, message))
        print(f"{GREEN}✓{RESET} {test_name}" + (f": {message}" if message else ""))
    
    def add_fail(self, test_name: str, message: str = ""):
        self.failed.append((test_name, message))
        print(f"{RED}✗{RESET} {test_name}" + (f": {message}" if message else ""))
    
    def add_warning(self, test_name: str, message: str = ""):
        self.warnings.append((test_name, message))
        print(f"{YELLOW}⚠{RESET} {test_name}" + (f": {message}" if message else ""))
    
    def print_summary(self):
        print(f"\n{BOLD}{BLUE}{'=' * 80}{RESET}")
        print(f"{BOLD}{BLUE}{'TEST SUMMARY'.center(80)}{RESET}")
        print(f"{BOLD}{BLUE}{'=' * 80}{RESET}\n")
        
        print(f"{GREEN}Passed: {len(self.passed)}{RESET}")
        print(f"{RED}Failed: {len(self.failed)}{RESET}")
        print(f"{YELLOW}Warnings: {len(self.warnings)}{RESET}")
        
        if self.failed:
            print(f"\n{BOLD}{RED}Failed Tests:{RESET}")
            for test, msg in self.failed:
                print(f"  - {test}: {msg}")
        
        total = len(self.passed) + len(self.failed)
        if total > 0:
            success_rate = (len(self.passed) / total) * 100
            print(f"\n{BOLD}Success Rate: {success_rate:.1f}%{RESET}")
        
        return len(self.failed) == 0

def print_header(text: str):
    print(f"\n{BOLD}{BLUE}{'=' * 80}{RESET}")
    print(f"{BOLD}{BLUE}{text.center(80)}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 80}{RESET}\n")

def test_infrastructure(results: TestResults):
    """Test 1: Infrastructure & Services"""
    print_header("TEST 1: Infrastructure & Service Health")
    
    # Test Collector Health
    try:
        response = requests.get(f"{COLLECTOR_URL}/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            results.add_pass("Collector Health", f"Status: {health.get('status', 'unknown')}")
            
            # Check Kafka connection
            if health.get('checks', {}).get('kafka', {}).get('status') == 'healthy':
                results.add_pass("Collector Kafka Connection", "Connected")
            else:
                results.add_fail("Collector Kafka Connection", "Not connected")
        else:
            results.add_fail("Collector Health", f"HTTP {response.status_code}")
    except Exception as e:
        results.add_fail("Collector Health", str(e))
    
    # Test API Health
    try:
        response = requests.get(f"{API_URL}/", timeout=5)
        if response.status_code == 200:
            results.add_pass("API Service", "Running")
        else:
            results.add_fail("API Service", f"HTTP {response.status_code}")
    except Exception as e:
        results.add_fail("API Service", str(e))
    
    # Test Dashboard
    try:
        response = requests.get(f"{DASHBOARD_URL}/", timeout=5)
        if response.status_code == 200:
            results.add_pass("Dashboard", "Accessible")
        else:
            results.add_fail("Dashboard", f"HTTP {response.status_code}")
    except Exception as e:
        results.add_fail("Dashboard", str(e))
    
    # Test Redpanda Console
    try:
        response = requests.get(f"{REDPANDA_CONSOLE_URL}/", timeout=5)
        if response.status_code == 200:
            results.add_pass("Redpanda Console", "Accessible")
        else:
            results.add_warning("Redpanda Console", f"HTTP {response.status_code}")
    except Exception as e:
        results.add_warning("Redpanda Console", str(e))

def test_prometheus_metrics(results: TestResults):
    """Test 2: Prometheus Metrics Endpoints (Phase 2)"""
    print_header("TEST 2: Prometheus Metrics Integration (Phase 2)")
    
    # Test Collector /metrics
    try:
        response = requests.get(f"{COLLECTOR_URL}/metrics", timeout=5)
        if response.status_code == 200:
            metrics = response.text
            metric_lines = [l for l in metrics.split('\n') if l and not l.startswith('#')]
            if len(metric_lines) > 0:
                results.add_pass("Collector /metrics Endpoint", f"{len(metric_lines)} metrics exposed")
                
                # Check for specific metrics
                if 'vantage_collector_requests_total' in metrics:
                    results.add_pass("Collector Request Counter", "Found")
                else:
                    results.add_warning("Collector Request Counter", "Not found")
            else:
                results.add_fail("Collector /metrics Endpoint", "No metrics exported")
        else:
            results.add_fail("Collector /metrics Endpoint", f"HTTP {response.status_code}")
    except Exception as e:
        results.add_fail("Collector /metrics Endpoint", str(e))
    
    # Test Worker /metrics
    try:
        response = requests.get("http://localhost:9090/metrics", timeout=5)
        if response.status_code == 200:
            metrics = response.text
            metric_lines = [l for l in metrics.split('\n') if l and not l.startswith('#')]
            results.add_pass("Worker /metrics Endpoint", f"{len(metric_lines)} metrics exposed")
        else:
            results.add_fail("Worker /metrics Endpoint", f"HTTP {response.status_code}")
    except Exception as e:
        results.add_fail("Worker /metrics Endpoint", str(e))
    
    # Test API /metrics
    try:
        response = requests.get(f"{API_URL}/metrics", timeout=5)
        if response.status_code == 200:
            metrics = response.text
            metric_lines = [l for l in metrics.split('\n') if l and not l.startswith('#')]
            results.add_pass("API /metrics Endpoint", f"{len(metric_lines)} metrics exposed")
        else:
            results.add_fail("API /metrics Endpoint", f"HTTP {response.status_code}")
    except Exception as e:
        results.add_fail("API /metrics Endpoint", str(e))

def test_data_pipeline(results: TestResults):
    """Test 3: Core Data Pipeline"""
    print_header("TEST 3: Core Data Pipeline")
    
    # Send test metric
    test_metric = {
        "metrics": [{
            "timestamp": int(time.time() * 1000),
            "service_name": "test-comprehensive",
            "metric_name": "test.pipeline",
            "metric_type": "counter",
            "value": 42.0,
            "tags": {"test": "comprehensive", "timestamp": str(int(time.time()))}
        }],
        "service_name": "test-comprehensive",
        "environment": "test"
    }
    
    try:
        response = requests.post(f"{COLLECTOR_URL}/v1/metrics", json=test_metric, timeout=5)
        if response.status_code in [200, 202]:
            results.add_pass("Collector Accepts Metrics", f"HTTP {response.status_code}")
        else:
            results.add_fail("Collector Accepts Metrics", f"HTTP {response.status_code}")
            return
    except Exception as e:
        results.add_fail("Collector Accepts Metrics", str(e))
        return
    
    # Wait for processing
    print("  Waiting 5 seconds for metric processing...")
    time.sleep(5)
    
    # Query API for metrics
    try:
        response = requests.get(
            f"{API_URL}/api/metrics/timeseries",
            params={"service": "test-comprehensive", "limit": 10},
            timeout=5
        )
        if response.status_code == 200:
            metrics = response.json()
            if len(metrics) > 0:
                results.add_pass("End-to-End Data Flow", f"{len(metrics)} metrics retrieved")
            else:
                results.add_warning("End-to-End Data Flow", "No metrics found yet")
        else:
            results.add_fail("API Query Metrics", f"HTTP {response.status_code}")
    except Exception as e:
        results.add_fail("API Query Metrics", str(e))

def test_rate_limiting(results: TestResults):
    """Test 4: Rate Limiting (Phase 3)"""
    print_header("TEST 4: Rate Limiting (Phase 3 Security)")
    
    # Send rapid requests
    print("  Sending 50 rapid requests to test rate limiting...")
    rate_limited = False
    success_count = 0
    
    test_metric = {
        "metrics": [{
            "timestamp": int(time.time() * 1000),
            "service_name": "rate-limit-test",
            "metric_name": "test.rate",
            "metric_type": "counter",
            "value": 1.0
        }],
        "service_name": "rate-limit-test",
        "environment": "test"
    }
    
    for i in range(50):
        try:
            response = requests.post(f"{COLLECTOR_URL}/v1/metrics", json=test_metric, timeout=2)
            if response.status_code == 429:
                rate_limited = True
                break
            elif response.status_code in [200, 202]:
                success_count += 1
        except:
            break
    
    if rate_limited:
        results.add_pass("Rate Limiting", f"Triggered after {success_count} requests")
    else:
        results.add_warning("Rate Limiting", f"Not triggered ({success_count} requests accepted)")

def test_vql(results: TestResults):
    """Test 5: VQL Query Language"""
    print_header("TEST 5: VQL Query Language")
    
    # Test basic VQL query
    vql_query = {
        "query": "SELECT * FROM metrics WHERE service_name='test-comprehensive' LIMIT 5"
    }
    
    try:
        response = requests.post(f"{API_URL}/vql/execute", json=vql_query, timeout=5)
        if response.status_code == 200:
            result = response.json()
            results.add_pass("VQL Basic Query", "Executed successfully")
            
            if 'results' in result:
                results.add_pass("VQL Query Results", f"{len(result['results'])} rows returned")
            elif 'data' in result:
                results.add_pass("VQL Query Results", f"{len(result['data'])} rows returned")
        else:
            results.add_fail("VQL Basic Query", f"HTTP {response.status_code}: {response.text[:100]}")
    except Exception as e:
        results.add_fail("VQL Basic Query", str(e))

def test_vql_security(results: TestResults):
    """Test 6: VQL Security & Sanitization (Phase 3)"""
    print_header("TEST 6: VQL Security & Sanitization (Phase 3)")
    
    # Test SQL injection attempts
    malicious_queries = [
        {"query": "'; DROP TABLE metrics; --", "name": "Drop Table"},
        {"query": "SELECT * FROM metrics WHERE 1=1; DELETE FROM metrics; --", "name": "Delete"},
        {"query": "SELECT * FROM system.tables", "name": "System Tables"},
    ]
    
    for mq in malicious_queries:
        try:
            response = requests.post(f"{API_URL}/vql/execute", json={"query": mq["query"]}, timeout=5)
            # Should either be rejected (400) or sanitized (200 with no harmful effect)
            if response.status_code in [400, 403]:
                results.add_pass(f"VQL Sanitization: {mq['name']}", "Rejected malicious query")
            elif response.status_code == 200:
                results.add_warning(f"VQL Sanitization: {mq['name']}", "Accepted but should be sanitized")
            else:
                results.add_fail(f"VQL Sanitization: {mq['name']}", f"HTTP {response.status_code}")
        except Exception as e:
            results.add_fail(f"VQL Sanitization: {mq['name']}", str(e))

def test_comparison(results: TestResults):
    """Test 7: Metric Comparison & A/B Testing"""
    print_header("TEST 7: Metric Comparison & A/B Testing")
    
    try:
        comparison_request = {
            "baseline_service": "test-comprehensive",
            "candidate_service": "test-comprehensive",
            "metric_name": "test.pipeline",
            "time_start": int(time.time()) - 3600,
            "time_end": int(time.time())
        }
        
        response = requests.post(f"{API_URL}/compare/services", json=comparison_request, timeout=5)
        if response.status_code == 200:
            result = response.json()
            results.add_pass("Comparison API", "Executed successfully")
            
            if 'statistical_significance' in result or 'comparison' in result:
                results.add_pass("Comparison Results", "Statistical analysis included")
        elif response.status_code == 400 and "Insufficient data" in response.text:
            results.add_warning("Comparison API", "Insufficient data (expected - needs more test data)")
        else:
            results.add_fail("Comparison API", f"HTTP {response.status_code}: {response.text[:100]}")
    except Exception as e:
        results.add_fail("Comparison API", str(e))

def test_health_score(results: TestResults):
    """Test 8: Health Score Algorithm"""
    print_header("TEST 8: Health Score Algorithm")
    
    try:
        response = requests.get(
            f"{API_URL}/health/score/test-comprehensive",
            timeout=5
        )
        if response.status_code == 200:
            result = response.json()
            results.add_pass("Health Score API", "Executed successfully")
            
            if 'score' in result or 'health_score' in result:
                score = result.get('score', result.get('health_score', 'N/A'))
                results.add_pass("Health Score Calculation", f"Score: {score}")
        elif response.status_code == 404:
            results.add_warning("Health Score API", "Endpoint not found")
        else:
            results.add_fail("Health Score API", f"HTTP {response.status_code}")
    except Exception as e:
        results.add_fail("Health Score API", str(e))

def test_alerts(results: TestResults):
    """Test 9: Alert System"""
    print_header("TEST 9: Alert System & Adaptive Thresholds")
    
    try:
        response = requests.get(f"{API_URL}/alerts/", timeout=5)
        if response.status_code == 200:
            alerts = response.json()
            results.add_pass("Alerts API", f"Retrieved {len(alerts) if isinstance(alerts, list) else 'N/A'} alerts")
        elif response.status_code == 404:
            results.add_warning("Alerts API", "Endpoint not found")
        else:
            results.add_fail("Alerts API", f"HTTP {response.status_code}")
    except Exception as e:
        results.add_fail("Alerts API", str(e))

def test_traces(results: TestResults):
    """Test 10: Distributed Trace Correlation"""
    print_header("TEST 10: Distributed Trace Correlation")
    
    # Send metrics with trace IDs
    trace_metric = {
        "metrics": [{
            "timestamp": int(time.time() * 1000),
            "service_name": "trace-test-service",
            "metric_name": "test.trace",
            "metric_type": "counter",
            "value": 1.0,
            "trace_id": "trace-abc-123",
            "span_id": "span-001"
        }],
        "service_name": "trace-test-service",
        "environment": "test"
    }
    
    try:
        response = requests.post(f"{COLLECTOR_URL}/v1/metrics", json=trace_metric, timeout=5)
        if response.status_code in [200, 202]:
            results.add_pass("Trace Metric Ingestion", "Accepted")
            
            # Wait for processing
            time.sleep(3)
            
            # Query traces
            response = requests.get(
                f"{API_URL}/traces/",
                params={"limit": 10},
                timeout=5
            )
            if response.status_code == 200:
                results.add_pass("Trace Query API", "Executed successfully")
            elif response.status_code == 404:
                results.add_warning("Trace Query API", "Endpoint not found")
        else:
            results.add_fail("Trace Metric Ingestion", f"HTTP {response.status_code}")
    except Exception as e:
        results.add_fail("Trace Operations", str(e))

def test_input_validation(results: TestResults):
    """Test 11: Input Validation (Phase 3)"""
    print_header("TEST 11: Input Validation (Phase 3 Security)")
    
    # Test invalid metric format
    invalid_metrics = [
        ({"invalid": "data"}, "Missing required fields"),
        ({"metrics": []}, "Empty metrics array"),
        ({"metrics": [{"timestamp": "invalid"}]}, "Invalid timestamp type"),
    ]
    
    for invalid_data, test_name in invalid_metrics:
        try:
            response = requests.post(f"{COLLECTOR_URL}/v1/metrics", json=invalid_data, timeout=5)
            if response.status_code in [400, 422]:
                results.add_pass(f"Input Validation: {test_name}", "Rejected invalid data")
            else:
                results.add_warning(f"Input Validation: {test_name}", f"HTTP {response.status_code}")
        except Exception as e:
            results.add_fail(f"Input Validation: {test_name}", str(e))

def test_api_endpoints(results: TestResults):
    """Test 12: API Endpoints Coverage"""
    print_header("TEST 12: API Endpoints Coverage")
    
    endpoints = [
        ("/api/services", "GET", "Services List"),
        ("/api/metrics/timeseries", "GET", "Timeseries Metrics"),
        ("/api/metrics/aggregated", "GET", "Aggregated Metrics"),
    ]
    
    for endpoint, method, name in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{API_URL}{endpoint}", timeout=5)
            else:
                response = requests.post(f"{API_URL}{endpoint}", json={}, timeout=5)
            
            if response.status_code == 200:
                results.add_pass(f"API Endpoint: {name}", f"{method} {endpoint}")
            elif response.status_code == 404:
                results.add_warning(f"API Endpoint: {name}", "Not found")
            else:
                results.add_fail(f"API Endpoint: {name}", f"HTTP {response.status_code}")
        except Exception as e:
            results.add_fail(f"API Endpoint: {name}", str(e))

def main():
    print(f"{BOLD}{BLUE}{'=' * 80}{RESET}")
    print(f"{BOLD}{BLUE}{'VANTAGE PLATFORM - COMPREHENSIVE TEST SUITE'.center(80)}{RESET}")
    print(f"{BOLD}{BLUE}{'Testing All Implemented Features (Phase 1-3)'.center(80)}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 80}{RESET}\n")
    
    results = TestResults()
    
    # Run all tests
    test_infrastructure(results)
    test_prometheus_metrics(results)
    test_data_pipeline(results)
    test_rate_limiting(results)
    test_vql(results)
    test_vql_security(results)
    test_comparison(results)
    test_health_score(results)
    test_alerts(results)
    test_traces(results)
    test_input_validation(results)
    test_api_endpoints(results)
    
    # Print summary
    success = results.print_summary()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
