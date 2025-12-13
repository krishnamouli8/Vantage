"""Main FastAPI application."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.config import settings
from api.query import router as query_router
from api.vql_router import router as vql_router
from api.comparison_router import router as comparison_router
from api.health_router import router as health_router
from api.alerts import router as alerts_router
from api.traces import router as traces_router
from api.websocket import websocket_endpoint

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

app = FastAPI(
    title="Vantage Query API",
    description="Query API for Vantage metrics with VQL, comparison, and health scores",
    version="0.2.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(query_router)
app.include_router(vql_router)
app.include_router(comparison_router)
app.include_router(health_router)
app.include_router(alerts_router)
app.include_router(traces_router)

# WebSocket
app.websocket("/ws/metrics")(websocket_endpoint)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"service": "vantage-api", "version": "0.1.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    from datetime import datetime
    from api.database import get_connection
    
    try:
        # Test database connection
        with get_connection() as db:
            cursor = db.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
        db_status = "healthy"
        db_message = "Database connection successful"
    except Exception as e:
        db_status = "unhealthy"
        db_message = f"Database connection failed: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "service": "vantage-api",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "database": {
                "status": db_status,
                "message": db_message
            },
            "api": {
                "status": "healthy",
                "message": "API is running"
            }
        }
    }




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
