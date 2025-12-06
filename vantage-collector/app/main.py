"""
Main FastAPI application for Vantage Collector.

High-performance metric ingestion service with Kafka integration.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.config import settings
from app.api import ingest_router, health_router
from app.queue import get_producer, shutdown_producer

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    
    Handles:
    - Kafka producer initialization on startup
    - Graceful shutdown on exit
    """
    # Startup
    logger.info(f"Starting {settings.service_name}...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Kafka bootstrap servers: {settings.kafka_bootstrap_servers}")
    logger.info(f"Kafka topic: {settings.kafka_topic}")
    
    try:
        # Initialize Kafka producer
        producer = await get_producer()
        logger.info("Kafka producer initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Kafka producer: {e}", exc_info=True)
        # Continue anyway - health checks will show degraded status
    
    logger.info(f"{settings.service_name} started successfully")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.service_name}...")
    
    try:
        await shutdown_producer()
        logger.info("Kafka producer shut down successfully")
    except Exception as e:
        logger.error(f"Error shutting down Kafka producer: {e}", exc_info=True)
    
    logger.info(f"{settings.service_name} shut down complete")


# Create FastAPI application
app = FastAPI(
    title="Vantage Collector",
    description="High-performance metric ingestion service for Vantage observability platform",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware
if settings.cors_enabled:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add GZip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
app.include_router(ingest_router)
app.include_router(health_router)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with service information."""
    return {
        "service": settings.service_name,
        "version": "0.1.0",
        "environment": settings.environment,
        "status": "running",
        "endpoints": {
            "ingest": "/v1/metrics",
            "health": "/health",
            "stats": "/v1/stats",
            "docs": "/docs",
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers if not settings.debug else 1,
        log_level="debug" if settings.debug else "info",
        reload=settings.debug,
    )
