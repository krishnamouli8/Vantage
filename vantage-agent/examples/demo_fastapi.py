"""
Demo: FastAPI application with auto-instrumentation

This example shows how to use the Vantage agent with a FastAPI application.
"""

from fastapi import FastAPI, HTTPException
import httpx
from vantage_agent import init_agent

# Initialize agent BEFORE creating FastAPI app
init_agent(
    service_name="demo-fastapi-app",
    collector_url="http://localhost:8000",
    auto_instrument=["fastapi", "httpx"],
    debug=True,
)

# Create FastAPI app
app = FastAPI(title="Vantage Demo API")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to Vantage FastAPI Demo"}

@app.get("/api/users")
async def get_users():
    """Get users from external API"""
    async with httpx.AsyncClient() as client:
        response = await client.get("https://jsonplaceholder.typicode.com/users")
        users = response.json()
    
    return {
        "count": len(users),
        "users": users[:3]
    }

@app.get("/api/posts/{post_id}")
async def get_post(post_id: int):
    """Get a specific post"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://jsonplaceholder.typicode.com/posts/{post_id}")
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Post not found")
        
        return response.json()

@app.get("/api/slow")
async def slow_endpoint():
    """Slow endpoint for testing"""
    import asyncio
    await asyncio.sleep(2)
    return {"message": "This was slow"}

@app.get("/api/error")
async def error_endpoint():
    """Endpoint that raises an error"""
    raise HTTPException(status_code=500, detail="This is a test error")

if __name__ == "__main__":
    import uvicorn
    
    print("Starting FastAPI demo app...")
    print("Try these endpoints:")
    print("  - http://localhost:8000/")
    print("  - http://localhost:8000/api/users")
    print("  - http://localhost:8000/api/posts/1")
    print("  - http://localhost:8000/api/slow")
    print("  - http://localhost:8000/api/error")
    print("  - http://localhost:8000/docs (Swagger UI)")
    print("\nMetrics will be sent to http://localhost:8000")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
