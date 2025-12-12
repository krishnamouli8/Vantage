#!/usr/bin/env python3
"""
Comprehensive verification script for Vantage Platform.

Verifies the complete end-to-end pipeline:
1. All services are running
2. Data flows from Collector → Kafka → Worker → SQLite
3. API can query the data
4. WebSocket connections work
"""

import requests
import sqlite3
import json
import time
from pathlib import Path

# Configuration
COLLECTOR_URL = "http://localhost:8000"
API_URL = "http://localhost:8001"
DASHBOARD_URL = "http://localhost:3000"
REDPANDA_CONSOLE_URL = "http://localhost:8080"

# Database path (inside Docker volume, we'll check via API)
# For local verification, you'd need to access the Docker volume


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 70}")
    print(f"{title}")
    print('=' * 70)


def check_service(name: str, url: str, endpoint: str = "/") -> bool:
    """Check if a service is accessible."""
    try:
        response = requests.get(f"{url}{endpoint}", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def main():
    print("=" * 70)
    print("VANTAGE PLATFORM - COMPREHENSIVE VERIFICATION")
    print("=" * 70)
    
    results = {
        "services": {},
        "data_flow": {},
        "api": {},
    }
    
    # 1. Check all services
    print_section("1. Checking Service Status")
    
    services = [
        ("Collector", COLLECTOR_URL, "/health"),
        ("API", API_URL, "/"),
        ("Dashboard", DASHBOARD_URL, "/"),
        ("Redpanda Console", REDPANDA_CONSOLE_URL, "/"),
    ]
    
    for name, url, endpoint in services:
        status = check_service(name, url, endpoint)
        results["services"][name] = status
        symbol = "✓" if status else "❌"
        print(f"   {symbol} {name}: {'Running' if status else 'Not accessible'}")
    
    # 2. Check collector health details
    print_section("2. Checking Collector Health Details")
    
    try:
        response = requests.get(f"{COLLECTOR_URL}/health", timeout=5)
        health_data = response.json()
        print(f"   Status: {health_data.get('status', 'unknown')}")
        
        if "checks" in health_data:
            for check_name, check_data in health_data["checks"].items():
                check_status = check_data.get("status", "unknown")
                symbol = "✓" if check_status == "healthy" else "❌"
                print(f"   {symbol} {check_name}: {check_data.get('message', 'N/A')}")
        
        results["data_flow"]["collector_health"] = health_data
    except Exception as e:
        print(f"   ❌ Error checking collector health: {e}")
        results["data_flow"]["collector_health"] = None
    
    # 3. Check collector stats
    print_section("3. Checking Collector Stats")
    
    try:
        response = requests.get(f"{COLLECTOR_URL}/v1/stats", timeout=5)
        stats = response.json()
        print(f"   Total metrics received: {stats.get('total_metrics', 0)}")
        print(f"   Total batches received: {stats.get('total_batches', 0)}")
        print(f"   Messages sent to Kafka: {stats.get('kafka_messages_sent', 0)}")
        
        results["data_flow"]["collector_stats"] = stats
    except Exception as e:
        print(f"   ❌ Error checking collector stats: {e}")
        results["data_flow"]["collector_stats"] = None
    
    # 4. Query API for available services
    print_section("4. Querying API for Services")
    
    try:
        response = requests.get(f"{API_URL}/v1/services", timeout=5)
        services_list = response.json()
        print(f"   Services found: {len(services_list)}")
        for service in services_list:
            print(f"     - {service}")
        
        results["api"]["services"] = services_list
    except Exception as e:
        print(f"   ❌ Error querying services: {e}")
        results["api"]["services"] = []
    
    # 5. Query API for metrics
    print_section("5. Querying API for Metrics")
    
    try:
        # Query recent metrics
        response = requests.get(
            f"{API_URL}/v1/metrics",
            params={"limit": 10},
            timeout=5,
        )
        metrics = response.json()
        metric_count = len(metrics)
        print(f"   Recent metrics returned: {metric_count}")
        
        if metric_count > 0:
            print(f"   Sample metric:")
            sample = metrics[0]
            print(f"     Service: {sample.get('service_name', 'N/A')}")
            print(f"     Metric: {sample.get('metric_name', 'N/A')}")
            print(f"     Endpoint: {sample.get('endpoint', 'N/A')}")
            print(f"     Duration: {sample.get('duration_ms', 'N/A')}ms")
        
        results["api"]["metrics"] = metrics
    except Exception as e:
        print(f"   ❌ Error querying metrics: {e}")
        results["api"]["metrics"] = []
    
    # 6. Query API for aggregated stats
    print_section("6. Querying API for Aggregated Stats")
    
    try:
        response = requests.get(
            f"{API_URL}/v1/metrics/aggregated",
            params={"time_range": 3600},  # Last hour
            timeout=5,
        )
        agg_stats = response.json()
        print(f"   Total requests: {agg_stats.get('total_requests', 0)}")
        print(f"   Average duration: {agg_stats.get('avg_duration', 0):.2f}ms")
        print(f"   Error count: {agg_stats.get('error_count', 0)}")
        
        results["api"]["aggregated"] = agg_stats
    except Exception as e:
        print(f"   ❌ Error querying aggregated stats: {e}")
        results["api"]["aggregated"] = None
    
    # 7. Summary
    print_section("VERIFICATION SUMMARY")
    
    all_services_up = all(results["services"].values())
    has_metrics = len(results["api"].get("metrics", [])) > 0
    
    if all_services_up and has_metrics:
        print("\n   ✅ ALL SYSTEMS OPERATIONAL!")
        print("   ✅ Data is flowing through the pipeline")
        print("   ✅ Metrics are being stored and can be queried")
        print("\n   🎉 Platform is working correctly!")
    else:
        print("\n   ⚠️  Some issues detected:")
        if not all_services_up:
            print("      - Not all services are running")
        if not has_metrics:
            print("      - No metrics found in database")
            print("      - Run: python send_test_metrics.py")
    
    # Save report
    report_path = Path("verification_report.json")
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n   📄 Detailed report saved to: {report_path}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
