"""Main FastAPI application."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.config import settings
from api.query import router as query_router
from api.vql_router import router as vql_router
from api.comparison_router import router as comparison_router
from api.health_router import router as health_router
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

# WebSocket
app.websocket("/ws/metrics")(websocket_endpoint)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"service": "vantage-api", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
