"""Configuration for the worker service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Worker configuration."""
    
    # Kafka settings
    kafka_bootstrap_servers: str = "redpanda:29092"
    kafka_topic: str = "metrics-raw"
    kafka_group_id: str = "vantage-worker"
    
    # Database settings
    database_type: str = "clickhouse"  # "sqlite" or "clickhouse"
    
    # SQLite settings (fallback)
    database_path: str = "/app/data/metrics.db"
    
    # ClickHouse settings
    clickhouse_host: str = "clickhouse"
    clickhouse_port: int = 9000
    clickhouse_database: str = "vantage"
    clickhouse_user: str = "default"
    clickhouse_password: str = ""
    
    # Processing settings
    batch_size: int = 100
    
    # Worker settings
    debug: bool = False
    
    class Config:
        env_prefix = "WORKER_"
        case_sensitive = False


settings = Settings()