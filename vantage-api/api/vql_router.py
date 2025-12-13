"""
VQL API Endpoint - Execute VQL queries
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any
from api.config import settings
from api.vql import VQLExecutor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/vql", tags=["vql"])


class VQLQueryRequest(BaseModel):
    """VQL query request"""
    query: str


class VQLQueryResponse(BaseModel):
    """VQL query response"""
    results: List[Dict[str, Any]]
    row_count: int
    query: str


@router.post("/execute")
async def execute_vql(request: VQLQueryRequest) -> VQLQueryResponse:
    """
    Execute a VQL query
    
    Example queries:
    - SELECT service_name, AVG(value) FROM metrics WHERE timestamp > 1234567890 GROUP BY service_name
    - SELECT * FROM metrics WHERE service_name = 'api-gateway' AND metric_name = 'http.request.duration' LIMIT 100
    - SELECT service_name, COUNT(*) FROM metrics GROUP BY service_name ORDER BY COUNT(*) DESC LIMIT 10
    """
    try:
        executor = VQLExecutor(settings.database_path)
        results = executor.execute(request.query)
        
        return VQLQueryResponse(
            results=results,
            row_count=len(results),
            query=request.query
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing VQL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/examples")
async def get_examples() -> Dict[str, List[str]]:
    """Get example VQL queries"""
    return {
        "examples": [
            "SELECT service_name, AVG(value) as avg_latency FROM metrics WHERE metric_name = 'http.request.duration' AND timestamp > 1234567890 GROUP BY service_name",
            "SELECT * FROM metrics WHERE service_name = 'api-gateway' ORDER BY timestamp DESC LIMIT 100",
            "SELECT service_name, COUNT(*) as request_count FROM metrics WHERE metric_type = 'counter' GROUP BY service_name ORDER BY COUNT(*) DESC",
            "SELECT metric_name, MIN(value), MAX(value), AVG(value) FROM metrics WHERE service_name = 'payment-service' GROUP BY metric_name",
        ]
    }
