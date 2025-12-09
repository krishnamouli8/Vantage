"""SQLite database operations."""

import sqlite3
import json
import logging
from typing import List, Dict
from contextlib import contextmanager
from worker.config import settings

logger = logging.getLogger(__name__)


def init_database():
    """Initialize SQLite database and create schema."""
    conn = sqlite3.connect(settings.database_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER NOT NULL,
            service_name TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            metric_type TEXT NOT NULL,
            value REAL NOT NULL,
            endpoint TEXT,
            method TEXT,
            status_code INTEGER,
            duration_ms REAL,
            tags TEXT,
            created_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON metrics(timestamp DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_service ON metrics(service_name, timestamp DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_metric ON metrics(metric_name, timestamp DESC)")
    
    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {settings.database_path}")


@contextmanager
def get_connection():
    """Get database connection."""
    conn = sqlite3.connect(settings.database_path)
    try:
        yield conn
    finally:
        conn.close()


def insert_metrics_batch(metrics: List[Dict]) -> int:
    """Insert a batch of metrics into database."""
    if not metrics:
        return 0
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        data = []
        for metric in metrics:
            tags_json = json.dumps(metric.get("tags", {}))
            data.append((
                metric["timestamp"],
                metric["service_name"],
                metric["metric_name"],
                metric["metric_type"],
                metric["value"],
                metric.get("endpoint"),
                metric.get("method"),
                metric.get("status_code"),
                metric.get("duration_ms"),
                tags_json
            ))
        
        cursor.executemany("""
            INSERT INTO metrics 
            (timestamp, service_name, metric_name, metric_type, value, 
             endpoint, method, status_code, duration_ms, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        
        conn.commit()
        return len(data)
