"""
Ingestion API endpoints for receiving metrics from agents.

Handles metric batch validation, rate limiting, and Kafka production.
"""

import logging
import time
from fastapi import APIRouter, HTTPException, Request, status, Depends
from fastapi.responses import JSONResponse
from app.models import MetricBatch, IngestResponse
from app.queue import get_producer
from app.config import settings
from app.auth import verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["ingestion"])

# Statistics
_stats = {
    "metrics_received": 0,
    "metrics_accepted": 0,
    "metrics_rejected": 0,
    "batches_received": 0,
    "start_time": time.time(),
}


@router.post(
    "/metrics",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest metric batch",
    description="Receive a batch of metrics from an agent and send to Kafka",
)
async def ingest_metrics(
    batch: MetricBatch,
    request: Request,
    _: None = Depends(verify_api_key),  # Add authentication
) -> IngestResponse:
    """
    Ingest a batch of metrics.
    
    This endpoint:
    1. Validates the incoming batch
    2. Sends metrics to Kafka/Redpanda
    3. Returns acceptance status
    
    The endpoint returns 202 Accepted immediately after queuing
    the metrics, without waiting for Kafka confirmation.
    """
    try:
        # Update statistics
        _stats["batches_received"] += 1
        _stats["metrics_received"] += len(batch.metrics)
        
        logger.info(
            f"Received batch of {len(batch.metrics)} metrics",
            extra={
                "service_name": batch.service_name,
                "environment": batch.environment,
                "agent_version": batch.agent_version,
                "client_ip": request.client.host if request.client else "unknown",
            }
        )
        
        # Get Kafka producer
        producer = await get_producer()
        
        if not producer.is_connected():
            logger.error("Kafka producer is not connected")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Message queue is unavailable"
            )
        
        # Convert metrics to dictionaries
        metric_dicts = [metric.model_dump() for metric in batch.metrics]
        
        # Send to Kafka
        successful, failed = await producer.send_batch(
            metric_dicts,
            key=batch.service_name
        )
        
        # Update statistics
        _stats["metrics_accepted"] += successful
        _stats["metrics_rejected"] += failed
        
        # Determine response status
        if failed == 0:
            response_status = "accepted"
            message = f"Successfully ingested {successful} metrics"
        elif successful > 0:
            response_status = "partial"
            message = f"Partially ingested {successful}/{len(batch.metrics)} metrics"
        else:
            response_status = "rejected"
            message = "Failed to ingest metrics"
        
        return IngestResponse(
            status=response_status,
            metrics_received=len(batch.metrics),
            metrics_accepted=successful,
            metrics_rejected=failed,
            message=message,
            errors=[] if failed == 0 else [f"{failed} metrics failed to send to queue"],
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(
            f"Error ingesting metrics: {e}",
            exc_info=True,
            extra={"batch": batch.model_dump()}
        )
        
        _stats["metrics_rejected"] += len(batch.metrics)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/stats",
    summary="Get ingestion statistics",
    description="Get current statistics for the ingestion service",
)
async def get_stats() -> dict:
    """
    Get ingestion statistics.
    
    Returns metrics about received/accepted/rejected metrics,
    uptime, and Kafka producer stats.
    """
    producer = await get_producer()
    producer_stats = producer.get_stats()
    
    uptime = time.time() - _stats["start_time"]
    
    return {
        "ingestion": {
            "batches_received": _stats["batches_received"],
            "metrics_received": _stats["metrics_received"],
            "metrics_accepted": _stats["metrics_accepted"],
            "metrics_rejected": _stats["metrics_rejected"],
            "acceptance_rate": (
                _stats["metrics_accepted"] / _stats["metrics_received"]
                if _stats["metrics_received"] > 0
                else 0.0
            ),
        },
        "kafka": producer_stats,
        "uptime_seconds": uptime,
        "service": settings.service_name,
        "environment": settings.environment,
    }
