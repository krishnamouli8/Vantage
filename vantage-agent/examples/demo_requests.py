"""
Demo: Basic usage with requests library

This example shows how to use the Vantage agent to automatically
track HTTP requests made with the requests library.
"""

import time
import requests
from vantage_agent import init_agent

def main():
    # Initialize the agent
    print("Initializing Vantage agent...")
    init_agent(
        service_name="demo-requests-app",
        collector_url="http://localhost:8000",
        auto_instrument=["requests"],
        debug=True,  # Enable debug logging to see what's happening
    )
    
    print("\nMaking HTTP requests...")
    print("=" * 60)
    
    # Make some HTTP requests - these will be automatically tracked
    try:
        # GET request
        print("\n1. GET request to httpbin.org...")
        response = requests.get("https://httpbin.org/get")
        print(f"   Status: {response.status_code}")
        
        # POST request
        print("\n2. POST request to httpbin.org...")
        response = requests.post(
            "https://httpbin.org/post",
            json={"key": "value"}
        )
        print(f"   Status: {response.status_code}")
        
        # Request with delay
        print("\n3. Request with 2-second delay...")
        response = requests.get("https://httpbin.org/delay/2")
        print(f"   Status: {response.status_code}")
        
        # Request that returns 404
        print("\n4. Request that returns 404...")
        response = requests.get("https://httpbin.org/status/404")
        print(f"   Status: {response.status_code}")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 60)
    print("\nWaiting for metrics to be flushed...")
    time.sleep(6)  # Wait for flush interval
    
    print("\nDemo complete! Check your collector for metrics.")

if __name__ == "__main__":
    main()
