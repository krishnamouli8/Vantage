"""Database connection for API."""

import sqlite3
import json
from contextlib import contextmanager
from typing import List, Dict, Optional
from api.config import settings


@contextmanager
def get_connection():
    """Get database connection."""
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def get_timeseries_data(
    service_name: Optional[str] = None,
    time_range: int = 3600
) -> List[Dict]:
    """Get time-series metrics data."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        now = int(__import__('time').time())
        start_time = (now - time_range) * 1000  # Convert to milliseconds
        
        query = """
            SELECT 
                timestamp,
                service_name,
                metric_name,
                value,
                duration_ms,
                status_code,
                endpoint,
                method
            FROM metrics
            WHERE timestamp >= ?
        """
        params = [start_time]
        
        if service_name:
            query += " AND service_name = ?"
            params.append(service_name)
            
        query += " ORDER BY timestamp ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]


def get_aggregated_metrics(
    service_name: Optional[str] = None,
    time_range: int = 3600
) -> Dict:
    """Get aggregated metrics."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        now = int(__import__('time').time())
        start_time = (now - time_range) * 1000
        
        query = """
            SELECT 
                COUNT(*) as total_requests,
                AVG(duration_ms) as avg_duration,
                MIN(duration_ms) as min_duration,
                MAX(duration_ms) as max_duration,
                SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) as error_count
            FROM metrics
            WHERE timestamp >= ? AND duration_ms IS NOT NULL
        """
        params = [start_time]
        
        if service_name:
            query += " AND service_name = ?"
            params.append(service_name)
        
        cursor.execute(query, params)
        row = cursor.fetchone()
        
        return dict(row) if row else {}


def get_services() -> List[str]:
    """Get list of unique services."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT service_name FROM metrics ORDER BY service_name")
        return [row[0] for row in cursor.fetchall()]
