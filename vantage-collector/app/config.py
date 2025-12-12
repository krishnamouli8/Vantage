"""
Configuration for the Vantage Collector service.

Handles all service configuration with environment variable support.
"""

from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Collector service configuration.
    
    All settings can be overridden via environment variables with
    the VANTAGE_ prefix (e.g., VANTAGE_KAFKA_BOOTSTRAP_SERVERS).
    """
    
    # Service settings
    service_name: str = "vantage-collector"
    environment: str = "development"
    debug: bool = False
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    
    # Kafka/Redpanda settings
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "metrics-raw"
    kafka_compression_type: str = "gzip"
    kafka_max_batch_size: int = 1000000  # 1MB
    kafka_linger_ms: int = 10  # Wait 10ms to batch messages
    kafka_acks: int = 1  # Leader acknowledgment (0, 1, or -1 for all)
    kafka_retries: int = 3
    
    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 1000  # requests per minute
    rate_limit_window: int = 60  # seconds
    
    # Batch limits
    max_batch_size: int = 1000  # Max metrics per request
    max_request_size_mb: int = 10  # Max request size
    
    # Monitoring
    enable_metrics: bool = True
    enable_health_checks: bool = True
    
    # CORS
    cors_enabled: bool = True
    cors_origins: list[str] = ["*"]
    
    # Authentication
    api_key: str | None = None
    auth_enabled: bool = False
    
    class Config:
        env_prefix = "VANTAGE_"
        case_sensitive = False


# Global settings instance
settings = Settings()
