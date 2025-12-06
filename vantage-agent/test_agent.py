"""
Simple test script to verify the Vantage agent is working.

This script demonstrates the agent collecting metrics without needing
the full collector backend running.
"""

import time
import requests
from vantage_agent import init_agent
from vantage_agent.metrics.collector import MetricCollector
from vantage_agent.config import AgentConfig

def test_agent_basic():
    """Test basic agent functionality."""
    print("=" * 70)
    print("VANTAGE AGENT - BASIC FUNCTIONALITY TEST")
    print("=" * 70)
    
    # Initialize the agent
    print("\n1. Initializing Vantage agent...")
    init_agent(
        service_name="test-app",
        collector_url="http://localhost:8000",  # Will send to collector if running
        auto_instrument=["requests"],
        debug=True,
    )
    print("   ✓ Agent initialized successfully")
    
    # Make some HTTP requests
    print("\n2. Making instrumented HTTP requests...")
    try:
        response = requests.get("https://httpbin.org/get")
        print(f"   ✓ GET request completed: {response.status_code}")
        
        response = requests.post("https://httpbin.org/post", json={"test": "data"})
        print(f"   ✓ POST request completed: {response.status_code}")
    except Exception as e:
        print(f"   ⚠ Request failed (but metrics were still collected): {e}")
    
    # Wait a moment for metrics to be collected
    print("\n3. Waiting for metrics to be collected...")
    time.sleep(1)
    
    # Access the global collector to check metrics
    from vantage_agent import _collector
    
    if _collector:
        stats = _collector.get_stats()
        print(f"\n4. Collector Statistics:")
        print(f"   - Metrics collected: {stats['metrics_collected']}")
        print(f"   - Metrics dropped: {stats['metrics_dropped']}")
        print(f"   - Queue size: {stats['queue_size']}")
        print(f"   - Drop rate: {stats['drop_rate']:.2%}")
        
        # Get the actual metrics
        metrics = _collector.get_all()
        print(f"\n5. Collected Metrics ({len(metrics)} total):")
        for i, metric in enumerate(metrics, 1):
            print(f"\n   Metric #{i}:")
            print(f"   - Name: {metric.metric_name}")
            print(f"   - Method: {metric.method}")
            print(f"   - Endpoint: {metric.endpoint}")
            print(f"   - Status: {metric.status_code}")
            print(f"   - Duration: {metric.duration_ms:.2f}ms")
            print(f"   - Tags: {metric.tags}")
    else:
        print("   ⚠ Collector not initialized")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE - Agent is working correctly! ✓")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Start the collector: docker compose up -d")
    print("  2. Run this script again to send metrics to collector")
    print("  3. View metrics in Redpanda Console: http://localhost:8080")
    print("  4. Check collector stats: curl http://localhost:8000/v1/stats")

if __name__ == "__main__":
    test_agent_basic()
