"""ClickHouse database operations for worker service.

Provides high-performance time-series data storage with optimal
partitioning, indexing, and TTL for data retention.
"""

import time
import json
from typing import List, Dict, Any
from contextlib import contextmanager
from clickhouse_driver import Client
from clickhouse_driver.errors import Error as ClickHouseError

from vantage_common.exceptions import DatabaseConnectionError
from vantage_common.constants import (
    DATABASE_CONNECTION_TIMEOUT_SECONDS,
    CLICKHOUSE_BATCH_SIZE,
    DEFAULT_DATA_RETENTION_DAYS,
    DOWNSAMPLED_DATA_RETENTION_DAYS,
)
from vantage_common.structured_logging import get_logger

logger = get_logger(__name__)


class ClickHouseDatabase:
    """ClickHouse database operations manager."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 9000,
        database: str = "vantage",
        user: str = "default",
        password: str = "",
    ):
        """Initialize ClickHouse connection.
        
        Args:
            host: ClickHouse server host
            port: Native protocol port (default 9000)
            database: Database name
            user: Username
            password: Password
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.client: Client | None = None
    
    def connect(self) -> None:
        """Establish connection to ClickHouse."""
        try:
            self.client = Client(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                connect_timeout=DATABASE_CONNECTION_TIMEOUT_SECONDS,
                send_receive_timeout=DATABASE_CONNECTION_TIMEOUT_SECONDS,
            )
            
            # Test connection
            self.client.execute("SELECT 1")
            
            logger.info(
                "clickhouse_connected",
                host=self.host,
                port=self.port,
                database=self.database,
            )
            
        except ClickHouseError as e:
            logger.error(
                "clickhouse_connection_failed",
                host=self.host,
                port=self.port,
                error=str(e),
            )
            raise DatabaseConnectionError(
                f"Failed to connect to ClickHouse at {self.host}:{self.port}",
                details={"error": str(e)}
            ) from e
    
    def disconnect(self) -> None:
        """Close ClickHouse connection."""
        if self.client:
            self.client.disconnect()
            self.client = None
            logger.info("clickhouse_disconnected")
    
    @contextmanager
    def get_client(self):
        """Get ClickHouse client with automatic reconnection.
        
        Yields:
            ClickHouse client instance
        
        Raises:
            DatabaseConnectionError: If connection fails
        """
        if not self.client:
            self.connect()
        
        try:
            yield self.client
        except ClickHouseError as e:
            logger.error("clickhouse_query_error", error=str(e))
            # Try to reconnect for next query
            self.disconnect()
            raise DatabaseConnectionError(
                "ClickHouse query failed",
                details={"error": str(e)}
            ) from e
    
    def init_schema(self) -> None:
        """Initialize ClickHouse database schema with optimized tables."""
        with self.get_client() as client:
            # Create database if not exists
            client.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            
            # Metrics table with MergeTree engine
            # Partitioned by month for efficient data management and TTL
            client.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.database}.metrics (
                    id UInt64,
                    timestamp DateTime64(3),
                    service_name String,
                    metric_name String,
                    metric_type String,
                    value Float64,
                    endpoint String,
                    method String,
                    status_code UInt16,
                    duration_ms Float64,
                    tags String,
                    trace_id String,
                    span_id String,
                    aggregated UInt8 DEFAULT 0,
                    resolution_minutes UInt32 DEFAULT 0,
                    min_value Nullable(Float64),
                    max_value Nullable(Float64),
                    p50 Nullable(Float64),
                    p95 Nullable(Float64),
                    p99 Nullable(Float64),
                    sample_count Nullable(UInt64),
                    error_count Nullable(UInt64),
                    created_at DateTime DEFAULT now()
                )
                ENGINE = MergeTree()
                PARTITION BY toYYYYMM(timestamp)
                ORDER BY (service_name, metric_name, timestamp)
                TTL timestamp + INTERVAL {DEFAULT_DATA_RETENTION_DAYS} DAY
                SETTINGS index_granularity = 8192
            """)
            
            # Traces table
            client.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.database}.traces (
                    trace_id String,
                    service_name String,
                    start_time DateTime64(3),
                    end_time Nullable(DateTime64(3)),
                    duration_ms Nullable(Float64),
                    status String,
                    error UInt8 DEFAULT 0,
                    created_at DateTime DEFAULT now()
                )
                ENGINE = MergeTree()
                PARTITION BY toYYYYMM(start_time)
                ORDER BY (service_name, start_time, trace_id)
                TTL start_time + INTERVAL {DEFAULT_DATA_RETENTION_DAYS} DAY
            """)
            
            # Spans table
            client.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.database}.spans (
                    span_id String,
                    trace_id String,
                    parent_span_id String,
                    service_name String,
                    operation_name String,
                    start_time DateTime64(3),
                    end_time Nullable(DateTime64(3)),
                    duration_ms Nullable(Float64),
                    tags String,
                    logs String,
                    status String,
                    error UInt8 DEFAULT 0
                )
                ENGINE = MergeTree()
                PARTITION BY toYYYYMM(start_time)
                ORDER BY (trace_id, start_time, span_id)
                TTL start_time + INTERVAL {DEFAULT_DATA_RETENTION_DAYS} DAY
            """)
            
            # Alerts table
            client.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.database}.alerts (
                    id UInt64,
                    alert_id String,
                    service_name String,
                    metric_name String,
                    severity String,
                    status String,
                    message String,
                    current_value Nullable(Float64),
                    expected_min Nullable(Float64),
                    expected_max Nullable(Float64),
                    threshold_breach_count UInt32 DEFAULT 1,
                    first_triggered DateTime64(3),
                    last_triggered DateTime64(3),
                    resolved_at Nullable(DateTime64(3)),
                    created_at DateTime DEFAULT now()
                )
                ENGINE = MergeTree()
                PARTITION BY toYYYYMM(first_triggered)
                ORDER BY (service_name, status, last_triggered)
                TTL first_triggered + INTERVAL {DOWNSAMPLED_DATA_RETENTION_DAYS} DAY
            """)
            
            # Query log for access frequency tracking
            client.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.database}.query_log (
                    id UInt64,
                    service_name String,
                    metric_name String,
                    timestamp DateTime64(3),
                    duration_ms Float64,
                    created_at DateTime DEFAULT now()
                )
                ENGINE = MergeTree()
                PARTITION BY toYYYYMM(timestamp)
                ORDER BY (service_name, metric_name, timestamp)
                TTL timestamp + INTERVAL 30 DAY
            """)
            
            logger.info("clickhouse_schema_initialized", database=self.database)
    
    def insert_metrics_batch(self, metrics: List[Dict[str, Any]]) -> int:
        """Insert batch of metrics into ClickHouse.
        
        Args:
            metrics: List of metric dictionaries
        
        Returns:
            Number of metrics inserted
        
        Raises:
            DatabaseConnectionError: If insert fails
        """
        if not metrics:
            return 0
        
        with self.get_client() as client:
            # Prepare data for batch insert
            data = []
            for i, metric in enumerate(metrics):
                tags_json = json.dumps(metric.get("tags", {}))
                
                # Convert timestamp from milliseconds to DateTime64
                timestamp_ms = metric["timestamp"]
                timestamp = time.strftime(
                    "%Y-%m-%d %H:%M:%S",
                    time.gmtime(timestamp_ms / 1000.0)
                )
                
                data.append((
                    i,  # id (will be unique within batch)
                    timestamp,
                    metric["service_name"],
                    metric["metric_name"],
                    metric["metric_type"],
                    metric["value"],
                    metric.get("endpoint", ""),
                    metric.get("method", ""),
                    metric.get("status_code", 0),
                    metric.get("duration_ms", 0.0),
                    tags_json,
                    metric.get("trace_id", ""),
                    metric.get("span_id", ""),
                ))
            
            # Execute batch insert
            client.execute(
                f"""
                INSERT INTO {self.database}.metrics 
                (id, timestamp, service_name, metric_name, metric_type, value,
                 endpoint, method, status_code, duration_ms, tags, trace_id, span_id)
                VALUES
                """,
                data
            )
            
            logger.debug(
                "metrics_inserted",
                count=len(data),
                database=self.database,
            )
            
            return len(data)
    
    def insert_trace(self, trace_data: Dict[str, Any]) -> None:
        """Insert or update trace record.
        
        Args:
            trace_data: Trace information dictionary
        """
        with self.get_client() as client:
            timestamp_ms = trace_data["start_time"]
            start_time = time.strftime(
                "%Y-%m-%d %H:%M:%S",
                time.gmtime(timestamp_ms / 1000.0)
            )
            
            client.execute(
                f"""
                INSERT INTO {self.database}.traces
                (trace_id, service_name, start_time, status, error)
                VALUES
                """,
                [(
                    trace_data["trace_id"],
                    trace_data["service_name"],
                    start_time,
                    trace_data.get("status", "active"),
                    trace_data.get("error", 0),
                )]
            )
    
    def insert_span(self, span_data: Dict[str, Any]) -> None:
        """Insert span record.
        
        Args:
            span_data: Span information dictionary
        """
        with self.get_client() as client:
            timestamp_ms = span_data["start_time"]
            start_time = time.strftime(
                "%Y-%m-%d %H:%M:%S",
                time.gmtime(timestamp_ms / 1000.0)
            )
            
            tags_json = json.dumps(span_data.get("tags", {}))
            logs_json = json.dumps(span_data.get("logs", []))
            
            client.execute(
                f"""
                INSERT INTO {self.database}.spans
                (span_id, trace_id, parent_span_id, service_name, operation_name,
                 start_time, duration_ms, tags, logs, status, error)
                VALUES
                """,
                [(
                    span_data["span_id"],
                    span_data["trace_id"],
                    span_data.get("parent_span_id", ""),
                    span_data["service_name"],
                    span_data["operation_name"],
                    start_time,
                    span_data.get("duration_ms", 0.0),
                    tags_json,
                    logs_json,
                    span_data.get("status", "ok"),
                    span_data.get("error", 0),
                )]
            )
    
    def execute_retention_cleanup(self) -> Dict[str, int]:
        """Execute data retention cleanup (TTL is automatic in ClickHouse).
        
        ClickHouse handles TTL automatically, but this can force optimization.
        
        Returns:
            Dictionary with cleanup statistics
        """
        with self.get_client() as client:
            # Force TTL cleanup by optimizing partitions
            client.execute(f"OPTIMIZE TABLE {self.database}.metrics FINAL")
            client.execute(f"OPTIMIZE TABLE {self.database}.traces FINAL")
            client.execute(f"OPTIMIZE TABLE {self.database}.spans FINAL")
            client.execute(f"OPTIMIZE TABLE {self.database}.alerts FINAL")
            
            logger.info("retention_cleanup_completed")
            
            return {"status": "completed", "method": "ttl_automatic"}
