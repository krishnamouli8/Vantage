"""
Pydantic models for the collector API.

Defines request/response schemas with validation.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime


class Metric(BaseModel):
    """
    Individual metric model.
    
    Matches the structure sent by the agent.
    """
    
    timestamp: int = Field(..., description="Unix timestamp in milliseconds")
    service_name: str = Field(..., min_length=1, max_length=255)
    metric_name: str = Field(..., min_length=1, max_length=255)
    metric_type: Literal["counter", "gauge", "histogram"]
    value: float
    tags: dict[str, str] = Field(default_factory=dict)
    endpoint: Optional[str] = Field(None, max_length=500)
    method: Optional[str] = Field(None, max_length=10)
    status_code: Optional[int] = Field(None, ge=0, le=999)
    duration_ms: Optional[float] = Field(None, ge=0)
    error: Optional[str] = Field(None, max_length=1000)
    
    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: int) -> int:
        """Validate timestamp is reasonable."""
        # Check timestamp is not in the future by more than 1 hour
        now_ms = int(datetime.now().timestamp() * 1000)
        if v > now_ms + 3600000:  # 1 hour in ms
            raise ValueError("Timestamp is too far in the future")
        
        # Check timestamp is not older than 7 days
        if v < now_ms - (7 * 24 * 3600000):  # 7 days in ms
            raise ValueError("Timestamp is too old (>7 days)")
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": 1701878400000,
                "service_name": "api-gateway",
                "metric_name": "http.request.duration",
                "metric_type": "histogram",
                "value": 123.45,
                "tags": {"region": "us-east-1"},
                "endpoint": "/api/users",
                "method": "GET",
                "status_code": 200,
                "duration_ms": 123.45,
            }
        }


class MetricBatch(BaseModel):
    """
    Batch of metrics from the agent.
    """
    
    metrics: list[Metric] = Field(..., min_length=1, max_length=1000)
    service_name: str = Field(..., min_length=1, max_length=255)
    environment: str = Field(default="development", max_length=50)
    agent_version: str = Field(default="unknown", max_length=50)
    batch_size: Optional[int] = None
    
    @field_validator("batch_size", mode="before")
    @classmethod
    def set_batch_size(cls, v, info):
        """Auto-set batch_size if not provided."""
        if v is None and "metrics" in info.data:
            return len(info.data["metrics"])
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "metrics": [
                    {
                        "timestamp": 1701878400000,
                        "service_name": "api-gateway",
                        "metric_name": "http.request.duration",
                        "metric_type": "histogram",
                        "value": 123.45,
                        "endpoint": "/api/users",
                        "method": "GET",
                        "status_code": 200,
                        "duration_ms": 123.45,
                    }
                ],
                "service_name": "api-gateway",
                "environment": "production",
                "agent_version": "0.1.0",
            }
        }


class IngestResponse(BaseModel):
    """
    Response from the ingest endpoint.
    """
    
    status: Literal["accepted", "partial", "rejected"]
    metrics_received: int
    metrics_accepted: int
    metrics_rejected: int = 0
    message: str
    errors: list[str] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "accepted",
                "metrics_received": 100,
                "metrics_accepted": 100,
                "metrics_rejected": 0,
                "message": "Successfully ingested 100 metrics",
                "errors": [],
            }
        }


class HealthResponse(BaseModel):
    """
    Health check response.
    """
    
    status: Literal["healthy", "degraded", "unhealthy"]
    service: str
    version: str
    timestamp: datetime
    checks: dict[str, dict[str, str]]
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "vantage-collector",
                "version": "0.1.0",
                "timestamp": "2025-12-05T22:00:00Z",
                "checks": {
                    "kafka": {"status": "healthy", "message": "Connected"},
                    "api": {"status": "healthy", "message": "Running"},
                },
            }
        }


class MetricsResponse(BaseModel):
    """
    Prometheus-style metrics response.
    """
    
    metrics_received_total: int
    metrics_accepted_total: int
    metrics_rejected_total: int
    kafka_messages_sent_total: int
    kafka_errors_total: int
    uptime_seconds: float
