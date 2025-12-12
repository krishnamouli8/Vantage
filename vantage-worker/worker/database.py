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
    
    # Check if metrics table exists and get its columns
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='metrics'")
    table_exists = cursor.fetchone() is not None
    
    if table_exists:
        # Migrate existing table
        _migrate_metrics_table(cursor)
    else:
        # Create new table with full schema
        cursor.execute("""
            CREATE TABLE metrics (
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
                trace_id TEXT,
                span_id TEXT,
                aggregated INTEGER DEFAULT 0,
                resolution_minutes INTEGER DEFAULT 0,
                min_value REAL,
                max_value REAL,
                p50 REAL,
                p95 REAL,
                p99 REAL,
                sample_count INTEGER,
                error_count INTEGER,
                created_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        """)
    
    # Traces table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS traces (
            trace_id TEXT PRIMARY KEY,
            service_name TEXT NOT NULL,
            start_time INTEGER NOT NULL,
            end_time INTEGER,
            duration_ms REAL,
            status TEXT,
            error INTEGER DEFAULT 0,
            created_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
    """)
    
    # Spans table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS spans (
            span_id TEXT PRIMARY KEY,
            trace_id TEXT NOT NULL,
            parent_span_id TEXT,
            service_name TEXT NOT NULL,
            operation_name TEXT NOT NULL,
            start_time INTEGER NOT NULL,
            end_time INTEGER,
            duration_ms REAL,
            tags TEXT,
            logs TEXT,
            status TEXT,
            error INTEGER DEFAULT 0,
            FOREIGN KEY (trace_id) REFERENCES traces(trace_id)
        )
    """)
    
    # Alerts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id TEXT UNIQUE NOT NULL,
            service_name TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            severity TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT NOT NULL,
            current_value REAL,
            expected_min REAL,
            expected_max REAL,
            threshold_breach_count INTEGER DEFAULT 1,
            first_triggered INTEGER NOT NULL,
            last_triggered INTEGER NOT NULL,
            resolved_at INTEGER,
            created_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
    """)
    
    # Query log for access frequency tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS query_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_name TEXT,
            metric_name TEXT,
            timestamp INTEGER NOT NULL,
            duration_ms REAL,
            created_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
    """)
    
    # Create indexes (safe for both new and migrated tables)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON metrics(timestamp DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_service ON metrics(service_name, timestamp DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_metric ON metrics(metric_name, timestamp DESC)")
    
    # Only create new indexes if columns exist
    if _column_exists(cursor, 'metrics', 'trace_id'):
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trace_id ON metrics(trace_id)")
    if _column_exists(cursor, 'metrics', 'aggregated'):
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_aggregated ON metrics(aggregated, timestamp)")
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trace_service ON traces(service_name, start_time DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trace_time ON traces(start_time DESC)")
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_span_trace ON spans(trace_id, start_time)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_span_parent ON spans(parent_span_id)")
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_service ON alerts(service_name, status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_status ON alerts(status, last_triggered DESC)")
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_query_log ON query_log(service_name, metric_name, timestamp)")
    
    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {settings.database_path}")


def _column_exists(cursor, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table"""
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        return column_name in columns
    except Exception:
        return False


def _migrate_metrics_table(cursor):
    """Migrate existing metrics table to new schema"""
    logger.info("Migrating metrics table to new schema...")
    
    # Get existing columns
    cursor.execute("PRAGMA table_info(metrics)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    
    # Add new columns if they don't exist
    new_columns = {
        'trace_id': 'TEXT',
        'span_id': 'TEXT',
        'aggregated': 'INTEGER DEFAULT 0',
        'resolution_minutes': 'INTEGER DEFAULT 0',
        'min_value': 'REAL',
        'max_value': 'REAL',
        'p50': 'REAL',
        'p95': 'REAL',
        'p99': 'REAL',
        'sample_count': 'INTEGER',
        'error_count': 'INTEGER',
    }
    
    for column_name, column_type in new_columns.items():
        if column_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE metrics ADD COLUMN {column_name} {column_type}")
                logger.info(f"Added column: {column_name}")
            except sqlite3.OperationalError as e:
                logger.warning(f"Could not add column {column_name}: {e}")
    
    logger.info("Metrics table migration complete")


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
