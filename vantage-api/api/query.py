"""Query endpoints."""

from fastapi import APIRouter, Query, Depends
from typing import Optional, List, Dict
from api.database import get_timeseries_data, get_aggregated_metrics, get_services
from api.auth import verify_api_key

router = APIRouter(prefix="/api", tags=["query"])


@router.get("/metrics/timeseries")
async def get_timeseries(
    service: Optional[str] = Query(None, description="Filter by service name"),
    range: int = Query(3600, description="Time range in seconds", ge=60, le=86400),
    _: None = Depends(verify_api_key),  # Add authentication
) -> List[Dict]:
    """Get time-series metrics data."""
    return get_timeseries_data(service, range)


@router.get("/metrics/aggregated")
async def get_aggregated(
    service: Optional[str] = Query(None, description="Filter by service name"),
    range: int = Query(3600, description="Time range in seconds", ge=60, le=86400),
    _: None = Depends(verify_api_key),  # Add authentication
) -> Dict:
    """Get aggregated metrics."""
    return get_aggregated_metrics(service, range)


@router.get("/services")
async def list_services(
    _: None = Depends(verify_api_key),  # Add authentication
) -> List[str]:
    """Get list of all services."""
    return get_services()
