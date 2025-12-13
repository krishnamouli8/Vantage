"""
Alerts API Endpoints

Query and manage alerts from the adaptive threshold system.
"""

import logging
import sqlite3
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from api.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/alerts", tags=["alerts"])


class Alert(BaseModel):
    """Alert response model"""

    alert_id: str
    service_name: str
    metric_name: str
    severity: str
    status: str
    message: str
    current_value: float
    expected_min: float
    expected_max: float
    threshold_breach_count: int
    first_triggered: int
    last_triggered: int
    resolved_at: Optional[int]


@router.get("/")
async def list_alerts(
    service: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
) -> List[Alert]:
    """List alerts with optional filters"""
    try:
        conn = sqlite3.connect(settings.database_path)
        cursor = conn.cursor()

        query = "SELECT * FROM alerts WHERE 1=1"
        params = []

        if service:
            query += " AND service_name = ?"
            params.append(service)

        if status:
            query += " AND status = ?"
            params.append(status)

        if severity:
            query += " AND severity = ?"
            params.append(severity)

        query += " ORDER BY last_triggered DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        alerts = []
        for row in cursor.fetchall():
            alerts.append(
                Alert(
                    alert_id=row[1],
                    service_name=row[2],
                    metric_name=row[3],
                    severity=row[4],
                    status=row[5],
                    message=row[6],
                    current_value=row[7],
                    expected_min=row[8],
                    expected_max=row[9],
                    threshold_breach_count=row[10],
                    first_triggered=row[11],
                    last_triggered=row[12],
                    resolved_at=row[13],
                )
            )

        conn.close()
        return alerts

    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active")
async def get_active_alerts(
    service: Optional[str] = Query(None),
) -> List[Alert]:
    """Get currently firing alerts"""
    try:
        conn = sqlite3.connect(settings.database_path)
        cursor = conn.cursor()

        query = "SELECT * FROM alerts WHERE status = 'firing'"
        params = []

        if service:
            query += " AND service_name = ?"
            params.append(service)

        query += " ORDER BY severity DESC, last_triggered DESC"

        cursor.execute(query, params)

        alerts = []
        for row in cursor.fetchall():
            alerts.append(
                Alert(
                    alert_id=row[1],
                    service_name=row[2],
                    metric_name=row[3],
                    severity=row[4],
                    status=row[5],
                    message=row[6],
                    current_value=row[7],
                    expected_min=row[8],
                    expected_max=row[9],
                    threshold_breach_count=row[10],
                    first_triggered=row[11],
                    last_triggered=row[12],
                    resolved_at=row[13],
                )
            )

        conn.close()
        return alerts

    except Exception as e:
        logger.error(f"Error fetching active alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_alert_summary() -> dict:
    """Get alert summary statistics"""
    try:
        conn = sqlite3.connect(settings.database_path)
        cursor = conn.cursor()

        # Count by status
        cursor.execute(
            """
            SELECT status, COUNT(*) 
            FROM alerts 
            GROUP BY status
            """
        )
        status_counts = {row[0]: row[1] for row in cursor.fetchall()}

        # Count by severity (only firing)
        cursor.execute(
            """
            SELECT severity, COUNT(*) 
            FROM alerts 
            WHERE status = 'firing'
            GROUP BY severity
            """
        )
        severity_counts = {row[0]: row[1] for row in cursor.fetchall()}

        # Top services with alerts
        cursor.execute(
            """
            SELECT service_name, COUNT(*) as alert_count
            FROM alerts
            WHERE status = 'firing'
            GROUP BY service_name
            ORDER BY alert_count DESC
            LIMIT 10
            """
        )
        top_services = [
            {"service": row[0], "count": row[1]} for row in cursor.fetchall()
        ]

        conn.close()

        return {
            "status_counts": status_counts,
            "severity_counts": severity_counts,
            "top_services": top_services,
            "total_firing": status_counts.get("firing", 0),
            "total_resolved": status_counts.get("resolved", 0),
        }

    except Exception as e:
        logger.error(f"Error fetching alert summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
