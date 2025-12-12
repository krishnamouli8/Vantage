"""Main FastAPI application."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.config import settings
from api.query import router as query_router
from api.traces import router as traces_router
from api.alerts import router as alerts_router
from api.websocket import websocket_endpoint

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

app = FastAPI(
    title="Vantage Query API",
    description="Query API for Vantage metrics",
    version="0.1.0"
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
app.include_router(traces_router)
app.include_router(alerts_router)

# WebSocket
app.websocket("/ws/metrics")(websocket_endpoint)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"service": "vantage-api", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
