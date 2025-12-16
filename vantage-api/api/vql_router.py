"""
VQL API Endpoint - Execute VQL queries with security validation
"""

import logging
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from api.config import settings
from api.vql import VQLExecutor
from api.vql_security import validate_vql_query
from vantage_common.exceptions import ValidationError

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
    execution_time_ms: float


@router.post("/execute")
async def execute_vql(request: VQLQueryRequest) -> VQLQueryResponse:
    """
    Execute a VQL query with security validation.
    
    Example queries:
    - SELECT service_name, AVG(value) FROM metrics WHERE timestamp > 1234567890 GROUP BY service_name
    - SELECT * FROM metrics WHERE service_name = 'api-gateway' LIMIT 100
    - SELECT service_name, COUNT(*) FROM metrics GROUP BY service_name ORDER BY COUNT(*) DESC LIMIT 10
    
    Security: All queries are validated to prevent SQL injection and dangerous operations.
    """
    start_time = time.time()
    
    try:
        # SECURITY: Validate query before execution
        validate_vql_query(request.query)
        
        # Execute query
        executor = VQLExecutor(settings.database_path)
        results = executor.execute(request.query)
        
        execution_time = (time.time() - start_time) * 1000
        
        return VQLQueryResponse(
            results=results,
            row_count=len(results),
            query=request.query,
            execution_time_ms=execution_time
        )
        
    except ValidationError as e:
        # Security validation failed - query blocked
        logger.warning(f"VQL validation failed: {e.message}", extra={"query": request.query})
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid or dangerous query",
                "message": e.message,
                "details": e.details if hasattr(e, 'details') else {}
            }
        )
    
    except ValueError as e:
        # VQL parsing/execution error
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        # Unexpected error
        logger.error(f"Error executing VQL: {e}")
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")


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
