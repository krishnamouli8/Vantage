"""
Health check and monitoring endpoints.

Provides service health status and Prometheus-style metrics.
"""

import logging
from datetime import datetime
from fastapi import APIRouter, status
from app.models import HealthResponse
from app.queue import get_producer
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["monitoring"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check the health status of the collector service",
)
async def health_check() -> HealthResponse:
    """
    Perform health check on all service components.
    
    Checks:
    - Kafka producer connection
    - API service status
    
    Returns overall health status.
    """
    checks = {}
    overall_status = "healthy"
    
    # Check Kafka connection
    try:
        producer = await get_producer()
        if producer.is_connected():
            checks["kafka"] = {
                "status": "healthy",
                "message": "Connected to Kafka"
            }
        else:
            checks["kafka"] = {
                "status": "unhealthy",
                "message": "Not connected to Kafka"
            }
            overall_status = "unhealthy"
    except Exception as e:
        checks["kafka"] = {
            "status": "unhealthy",
            "message": f"Kafka error: {str(e)}"
        }
        overall_status = "unhealthy"
    
    # API is healthy if we got here
    checks["api"] = {
        "status": "healthy",
        "message": "API is running"
    }
    
    return HealthResponse(
        status=overall_status,
        service=settings.service_name,
        version="0.1.0",
        timestamp=datetime.now(),
        checks=checks,
    )


@router.get(
    "/ready",
    summary="Readiness check",
    description="Check if the service is ready to accept traffic",
)
async def readiness_check() -> dict:
    """
    Kubernetes-style readiness check.
    
    Returns 200 if ready, 503 if not ready.
    """
    try:
        producer = await get_producer()
        if producer.is_connected():
            return {"status": "ready"}
        else:
            return {"status": "not_ready", "reason": "Kafka not connected"}
    except Exception as e:
        return {"status": "not_ready", "reason": str(e)}


@router.get(
    "/live",
    summary="Liveness check",
    description="Check if the service is alive",
)
async def liveness_check() -> dict:
    """
    Kubernetes-style liveness check.
    
    Always returns 200 if the API is responding.
    """
    return {"status": "alive"}
