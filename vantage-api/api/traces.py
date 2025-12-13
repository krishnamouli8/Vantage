"""
Trace and Span API Endpoints

Query distributed traces and visualize request flows.
"""

import logging
import sqlite3
import json
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from api.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/traces", tags=["traces"])


class Trace(BaseModel):
    """Trace response model"""

    trace_id: str
    service_name: str
    start_time: int
    end_time: Optional[int]
    duration_ms: Optional[float]
    status: str
    error: bool
    span_count: int = 0


class Span(BaseModel):
    """Span response model"""

    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    service_name: str
    operation_name: str
    start_time: int
    end_time: Optional[int]
    duration_ms: Optional[float]
    tags: Dict
    status: str
    error: bool
    depth: int = 0


@router.get("/")
async def list_traces(
    service: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
) -> List[Trace]:
    """List recent traces"""
    try:
        conn = sqlite3.connect(settings.database_path)
        cursor = conn.cursor()

        query = """
            SELECT t.trace_id, t.service_name, t.start_time, t.end_time,
                   t.duration_ms, t.status, t.error,
                   COUNT(s.span_id) as span_count
            FROM traces t
            LEFT JOIN spans s ON t.trace_id = s.trace_id
        """

        params = []
        if service:
            query += " WHERE t.service_name = ?"
            params.append(service)

        query += " GROUP BY t.trace_id ORDER BY t.start_time DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)

        traces = []
        for row in cursor.fetchall():
            traces.append(
                Trace(
                    trace_id=row[0],
                    service_name=row[1],
                    start_time=row[2],
                    end_time=row[3],
                    duration_ms=row[4],
                    status=row[5],
                    error=bool(row[6]),
                    span_count=row[7],
                )
            )

        conn.close()
        return traces

    except Exception as e:
        logger.error(f"Error fetching traces: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{trace_id}")
async def get_trace(trace_id: str) -> Dict:
    """Get trace with all spans"""
    try:
        conn = sqlite3.connect(settings.database_path)
        cursor = conn.cursor()

        # Get trace info
        cursor.execute(
            """
            SELECT trace_id, service_name, start_time, end_time,
                   duration_ms, status, error
            FROM traces
            WHERE trace_id = ?
            """,
            (trace_id,),
        )

        trace_row = cursor.fetchone()
        if not trace_row:
            conn.close()
            raise HTTPException(status_code=404, detail="Trace not found")

        # Get all spans
        cursor.execute(
            """
            SELECT span_id, trace_id, parent_span_id, service_name,
                   operation_name, start_time, end_time, duration_ms,
                   tags, logs, status, error
            FROM spans
            WHERE trace_id = ?
            ORDER BY start_time
            """,
            (trace_id,),
        )

        spans = []
        for row in cursor.fetchall():
            try:
                tags = json.loads(row[8]) if row[8] else {}
            except json.JSONDecodeError:
                tags = {}

            spans.append(
                {
                    "span_id": row[0],
                    "trace_id": row[1],
                    "parent_span_id": row[2],
                    "service_name": row[3],
                    "operation_name": row[4],
                    "start_time": row[5],
                    "end_time": row[6],
                    "duration_ms": row[7],
                    "tags": tags,
                    "status": row[10],
                    "error": bool(row[11]),
                }
            )

        conn.close()

        # Build span tree with depth
        span_tree = _build_span_tree(spans)

        return {
            "trace": {
                "trace_id": trace_row[0],
                "service_name": trace_row[1],
                "start_time": trace_row[2],
                "end_time": trace_row[3],
                "duration_ms": trace_row[4],
                "status": trace_row[5],
                "error": bool(trace_row[6]),
            },
            "spans": span_tree,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching trace: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _build_span_tree(spans: List[Dict]) -> List[Dict]:
    """Build hierarchical span tree with depth"""
    span_map = {s["span_id"]: s for s in spans}
    root_spans = []

    # Calculate depth for each span
    def calculate_depth(span_id: str, current_depth: int = 0) -> int:
        span = span_map.get(span_id)
        if not span:
            return current_depth

        span["depth"] = current_depth

        # Process children
        children = [
            s for s in spans if s.get("parent_span_id") == span_id
        ]
        for child in children:
            calculate_depth(child["span_id"], current_depth + 1)

        return current_depth

    # Find root spans (no parent or parent not in map)
    for span in spans:
        parent_id = span.get("parent_span_id")
        if not parent_id or parent_id not in span_map:
            root_spans.append(span)
            calculate_depth(span["span_id"], 0)

    return spans


@router.get("/search/")
async def search_traces(
    service: Optional[str] = None,
    min_duration: Optional[float] = None,
    max_duration: Optional[float] = None,
    error: Optional[bool] = None,
    limit: int = Query(100, le=1000),
) -> List[Trace]:
    """Search traces with filters"""
    try:
        conn = sqlite3.connect(settings.database_path)
        cursor = conn.cursor()

        query = """
            SELECT DISTINCT t.trace_id, t.service_name, t.start_time, t.end_time,
                   t.duration_ms, t.status, t.error,
                   COUNT(s.span_id) as span_count
            FROM traces t
            LEFT JOIN spans s ON t.trace_id = s.trace_id
            WHERE 1=1
        """

        params = []

        if service:
            query += " AND t.service_name = ?"
            params.append(service)

        if min_duration is not None:
            query += " AND t.duration_ms >= ?"
            params.append(min_duration)

        if max_duration is not None:
            query += " AND t.duration_ms <= ?"
            params.append(max_duration)

        if error is not None:
            query += " AND t.error = ?"
            params.append(1 if error else 0)

        query += " GROUP BY t.trace_id ORDER BY t.start_time DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        traces = []
        for row in cursor.fetchall():
            traces.append(
                Trace(
                    trace_id=row[0],
                    service_name=row[1],
                    start_time=row[2],
                    end_time=row[3],
                    duration_ms=row[4],
                    status=row[5],
                    error=bool(row[6]),
                    span_count=row[7],
                )
            )

        conn.close()
        return traces

    except Exception as e:
        logger.error(f"Error searching traces: {e}")
        raise HTTPException(status_code=500, detail=str(e))
