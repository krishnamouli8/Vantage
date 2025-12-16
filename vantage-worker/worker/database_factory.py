"""
Database factory for selecting database backend.

Provides abstraction layer to switch between SQLite and ClickHouse
based on configuration.
"""

from typing import Protocol, List, Dict, Any
from worker.config import settings
from vantage_common.structured_logging import get_logger

logger = get_logger(__name__)


class DatabaseBackend(Protocol):
    """Protocol defining database backend interface."""
    
    def connect(self) -> None:
        """Establish database connection."""
        ...
    
    def disconnect(self) -> None:
        """Close database connection."""
        ...
    
    def init_schema(self) -> None:
        """Initialize database schema."""
        ...
    
    def insert_metrics_batch(self, metrics: List[Dict[str, Any]]) -> int:
        """Insert batch of metrics.
        
        Returns:
            Number of metrics inserted
        """
        ...
    
    def insert_trace(self, trace_data: Dict[str, Any]) -> None:
        """Insert or update trace record."""
        ...
    
    def insert_span(self, span_data: Dict[str, Any]) -> None:
        """Insert span record."""
        ...
    
    def execute_retention_cleanup(self) -> Dict[str, int]:
        """Execute data retention cleanup.
        
        Returns:
            Cleanup statistics
        """
        ...


def get_database() -> DatabaseBackend:
    """Get database backend based on configuration.
    
    Returns:
        Database backend instance (SQLite or ClickHouse)
    
    Example:
        >>> db = get_database()
        >>> db.connect()
        >>> db.init_schema()
        >>> db.insert_metrics_batch(metrics)
    """
    db_type = getattr(settings, "database_type", "sqlite").lower()
    
    if db_type == "clickhouse":
        from worker.database_clickhouse import ClickHouseDatabase
        
        logger.info(
            "database_backend_selected",
            type="clickhouse",
            host=settings.clickhouse_host,
            database=settings.clickhouse_database,
        )
        
        return ClickHouseDatabase(
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            database=settings.clickhouse_database,
            user=settings.clickhouse_user,
            password=settings.clickhouse_password,
        )
    else:
        # Default to SQLite
        from worker.database_sqlite import SQLiteDatabase
        
        logger.info(
            "database_backend_selected",
            type="sqlite",
            path=settings.database_path,
        )
        
        return SQLiteDatabase(settings.database_path)
