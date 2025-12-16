"""SQLite database operations (fallback/legacy backend).

Kept as fallback option for smaller deployments.
For production scale, use ClickHouse via database_factory.
"""

import sqlite3
import json
import logging
from typing import List, Dict, Any
from contextmanager import contextmanager

from vantage_common.exceptions import DatabaseConnectionError
from vantage_common.constants import DATABASE_CONNECTION_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


class SQLiteDatabase:
    """SQLite database operations manager."""
    
    def __init__(self, database_path: str):
        """Initialize SQLite database.
        
        Args:
            database_path: Path to SQLite database file
        """
        self.database_path = database_path
        self.conn: sqlite3.Connection | None = None
    
    def connect(self) -> None:
        """Establish connection to SQLite database."""
        try:
            self.conn = sqlite3.connect(
                self.database_path,
                timeout=DATABASE_CONNECTION_TIMEOUT_SECONDS
            )
            logger.info(f"SQLite connected: {self.database_path}")
        except sqlite3.Error as e:
            raise DatabaseConnectionError(
                f"Failed to connect to SQLite at {self.database_path}",
                details={"error": str(e)}
            ) from e
    
    def disconnect(self) -> None:
        """Close SQLite connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("SQLite disconnected")
    
    @contextmanager
    def get_connection(self):
        """Get SQLite connection."""
        if not self.conn:
            self.connect()
        
        try:
            yield self.conn
        except sqlite3.Error as e:
            logger.error(f"SQLite query error: {e}")
            raise DatabaseConnectionError(
                "SQLite query failed",
                details={"error": str(e)}
            ) from e
    
    def init_schema(self) -> None:
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Check if metrics table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='metrics'")
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            self._migrate_metrics_table(cursor)
        else:
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
        
        # Query log
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
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON metrics(timestamp DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_service ON metrics(service_name, timestamp DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metric ON metrics(metric_name, timestamp DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trace_id ON metrics(trace_id)")
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
        logger.info(f"SQLite schema initialized at {self.database_path}")
    
    def _migrate_metrics_table(self, cursor):
        """Migrate existing metrics table to new schema."""
        logger.info("Migrating metrics table...")
        
        cursor.execute("PRAGMA table_info(metrics)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
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
    
    def insert_metrics_batch(self, metrics: List[Dict[str, Any]]) -> int:
        """Insert batch of metrics into SQLite."""
        if not metrics:
            return 0
        
        with self.get_connection() as conn:
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
                    tags_json,
                    metric.get("trace_id"),
                    metric.get("span_id"),
                ))
            
            cursor.executemany("""
                INSERT INTO metrics 
                (timestamp, service_name, metric_name, metric_type, value, 
                 endpoint, method, status_code, duration_ms, tags, trace_id, span_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, data)
            
            conn.commit()
            return len(data)
    
    def insert_trace(self, trace_data: Dict[str, Any]) -> None:
        """Insert or update trace record."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO traces
                (trace_id, service_name, start_time, status, error)
                VALUES (?, ?, ?, ?, ?)
            """, (
                trace_data["trace_id"],
                trace_data["service_name"],
                trace_data["start_time"],
                trace_data.get("status", "active"),
                trace_data.get("error", 0),
            ))
            
            conn.commit()
    
    def insert_span(self, span_data: Dict[str, Any]) -> None:
        """Insert span record."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            tags_json = json.dumps(span_data.get("tags", {}))
            logs_json = json.dumps(span_data.get("logs", []))
            
            cursor.execute("""
                INSERT OR REPLACE INTO spans
                (span_id, trace_id, parent_span_id, service_name, operation_name,
                 start_time, duration_ms, tags, logs, status, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                span_data["span_id"],
                span_data["trace_id"],
                span_data.get("parent_span_id", ""),
                span_data["service_name"],
                span_data["operation_name"],
                span_data["start_time"],
                span_data.get("duration_ms", 0.0),
                tags_json,
                logs_json,
                span_data.get("status", "ok"),
                span_data.get("error", 0),
            ))
            
            conn.commit()
    
    def execute_retention_cleanup(self) -> Dict[str, int]:
        """Execute data retention cleanup for SQLite."""
        from vantage_common.constants import DEFAULT_DATA_RETENTION_DAYS
        import time
        
        cutoff_timestamp = (time.time() - (DEFAULT_DATA_RETENTION_DAYS * 86400)) * 1000
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Delete old metrics
            cursor.execute("DELETE FROM metrics WHERE timestamp < ?", (cutoff_timestamp,))
            metrics_deleted = cursor.rowcount
            
            # Delete old traces
            cursor.execute("DELETE FROM traces WHERE start_time < ?", (cutoff_timestamp,))
            traces_deleted = cursor.rowcount
            
            # Delete old spans
            cursor.execute("DELETE FROM spans WHERE start_time < ?", (cutoff_timestamp,))
            spans_deleted = cursor.rowcount
            
            conn.commit()
            
            logger.info(
                f"Retention cleanup: deleted {metrics_deleted} metrics, "
                f"{traces_deleted} traces, {spans_deleted} spans"
            )
            
            return {
                "metrics_deleted": metrics_deleted,
                "traces_deleted": traces_deleted,
                "spans_deleted": spans_deleted,
            }
