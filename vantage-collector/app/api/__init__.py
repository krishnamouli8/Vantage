"""API package for Vantage Collector."""

from app.api.ingest import router as ingest_router
from app.api.health import router as health_router

__all__ = ["ingest_router", "health_router"]
