"""Query endpoints."""

from fastapi import APIRouter, Query
from typing import Optional, List, Dict
from api.database import get_timeseries_data, get_aggregated_metrics, get_services

router = APIRouter(prefix="/api", tags=["query"])


@router.get("/metrics/timeseries")
async def get_timeseries(
    service: Optional[str] = Query(None, description="Filter by service name"),
    range: int = Query(3600, description="Time range in seconds", ge=60, le=86400)
) -> List[Dict]:
    """Get time-series metrics data."""
    return get_timeseries_data(service, range)


@router.get("/metrics/aggregated")
async def get_aggregated(
    service: Optional[str] = Query(None, description="Filter by service name"),
    range: int = Query(3600, description="Time range in seconds", ge=60, le=86400)
) -> Dict:
    """Get aggregated metrics."""
    return get_aggregated_metrics(service, range)


@router.get("/services")
async def list_services() -> List[str]:
    """Get list of all services."""
    return get_services()
