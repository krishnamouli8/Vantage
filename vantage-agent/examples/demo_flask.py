"""
Demo: Flask application with auto-instrumentation

This example shows how to use the Vantage agent with a Flask application.
"""

from flask import Flask, jsonify
import requests
from vantage_agent import init_agent

# Initialize agent BEFORE creating Flask app
init_agent(
    service_name="demo-flask-app",
    collector_url="http://localhost:8000",
    auto_instrument=["flask", "requests"],
    debug=True,
)

# Create Flask app
app = Flask(__name__)

@app.route("/")
def index():
    """Home endpoint"""
    return jsonify({"message": "Welcome to Vantage Demo API"})

@app.route("/api/users")
def get_users():
    """Get users endpoint - makes an external API call"""
    # This external request will also be tracked
    response = requests.get("https://jsonplaceholder.typicode.com/users")
    users = response.json()
    
    return jsonify({
        "count": len(users),
        "users": users[:3]  # Return first 3 users
    })

@app.route("/api/slow")
def slow_endpoint():
    """Slow endpoint for testing"""
    import time
    time.sleep(2)
    return jsonify({"message": "This was slow"})

@app.route("/api/error")
def error_endpoint():
    """Endpoint that raises an error"""
    raise ValueError("This is a test error")

if __name__ == "__main__":
    print("Starting Flask demo app...")
    print("Try these endpoints:")
    print("  - http://localhost:5000/")
    print("  - http://localhost:5000/api/users")
    print("  - http://localhost:5000/api/slow")
    print("  - http://localhost:5000/api/error")
    print("\nMetrics will be sent to http://localhost:8000")
    
    app.run(debug=False, port=5000)
