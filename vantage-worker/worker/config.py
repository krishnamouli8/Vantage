"""Configuration for the worker service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Worker configuration."""
    
    # Kafka settings
    kafka_bootstrap_servers: str = "redpanda:29092"  # Fixed default
    kafka_topic: str = "metrics-raw"
    kafka_group_id: str = "vantage-worker"
    
    # Database settings
    database_path: str = "/app/data/metrics.db"
    batch_size: int = 100
    
    # Worker settings
    debug: bool = False
    
    class Config:
        env_prefix = "WORKER_"
        case_sensitive = False


settings = Settings()