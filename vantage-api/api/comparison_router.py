"""
Comparison API Router - Metric comparison for A/B testing
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from api.config import settings
from api.comparison import MetricComparison, ComparisonResult

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/compare", tags=["comparison"])


class ServiceComparisonRequest(BaseModel):
    """Request to compare two services"""
    baseline_service: str
    candidate_service: str
    metric_name: str
    time_start: int
    time_end: int


class TimeComparisonRequest(BaseModel):
    """Request to compare two time periods"""
    service_name: str
    metric_name: str
    baseline_start: int
    baseline_end: int
    candidate_start: int
    candidate_end: int


@router.post("/services")
async def compare_services(request: ServiceComparisonRequest) -> ComparisonResult:
    """
    Compare a metric between two services (e.g., canary vs production)
    
    Example:
    - baseline_service: "api-v1"
    - candidate_service: "api-v2-canary"
    - metric_name: "http.request.duration"
    """
    try:
        engine = MetricComparison(settings.database_path)
        result = engine.compare_services(
            request.baseline_service,
            request.candidate_service,
            request.metric_name,
            request.time_start,
            request.time_end
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error comparing services: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/time-periods")
async def compare_time_periods(request: TimeComparisonRequest) -> ComparisonResult:
    """
    Compare a metric across two time periods (e.g., before/after deployment)
    
    Example:
    - service_name: "api-gateway"
    - metric_name: "http.request.duration"
    - baseline: last week
    - candidate: this week
    """
    try:
        engine = MetricComparison(settings.database_path)
        result = engine.compare_time_periods(
            request.service_name,
            request.metric_name,
            request.baseline_start,
            request.baseline_end,
            request.candidate_start,
            request.candidate_end
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error comparing time periods: {e}")
        raise HTTPException(status_code=500, detail=str(e))
