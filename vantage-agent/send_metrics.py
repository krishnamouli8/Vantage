"""
Test script that waits for metrics to be sent to the collector.
"""

import time
import requests
from vantage_agent import init_agent

print("=" * 70)
print("SENDING METRICS TO COLLECTOR")
print("=" * 70)

# Initialize the agent
print("\n1. Initializing agent...")
init_agent(
    service_name="test-app",
    collector_url="http://localhost:8000",
    auto_instrument=["requests"],
    flush_interval=2,  # Flush every 2 seconds
    debug=False,
)

# Make some requests
print("2. Making HTTP requests...")
requests.get("https://httpbin.org/get")
requests.post("https://httpbin.org/post", json={"test": "data"})
print("   ✓ Requests completed")

# Wait for metrics to be flushed (2 seconds flush interval + 1 second buffer)
print("\n3. Waiting for metrics to be sent to collector...")
time.sleep(4)

print("\n✅ Done! Metrics should now be in Redpanda.")
print("\nCheck:")
print("  • Collector stats: curl http://localhost:8000/v1/stats")
print("  • Redpanda Console: http://localhost:8080")
print("    → Topics → metrics-raw → Messages")
