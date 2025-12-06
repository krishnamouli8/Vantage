"""
Configuration management for Vantage Agent.

Handles all agent configuration with validation and sensible defaults.
"""

from dataclasses import dataclass, field
from typing import Optional
import os


@dataclass
class AgentConfig:
    """
    Configuration for the Vantage APM agent.
    
    Attributes:
        service_name: Unique identifier for the service
        collector_url: URL of the Vantage collector API
        flush_interval: Seconds between metric flushes
        batch_size: Number of metrics to batch before flushing
        max_queue_size: Maximum number of metrics in queue
        debug: Enable debug logging
        environment: Deployment environment (e.g., "production", "staging")
        tags: Additional tags to attach to all metrics
        timeout: HTTP timeout for collector requests (seconds)
        retry_attempts: Number of retry attempts for failed exports
        retry_backoff: Exponential backoff multiplier for retries
    """
    
    service_name: str
    collector_url: str = "http://localhost:8000"
    flush_interval: int = 5
    batch_size: int = 100
    max_queue_size: int = 10000
    debug: bool = False
    environment: Optional[str] = None
    tags: dict[str, str] = field(default_factory=dict)
    timeout: int = 10
    retry_attempts: int = 3
    retry_backoff: float = 2.0
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate()
        self._apply_env_overrides()
    
    def _validate(self) -> None:
        """Validate configuration values."""
        if not self.service_name:
            raise ValueError("service_name is required")
        
        if not self.collector_url:
            raise ValueError("collector_url is required")
        
        if self.flush_interval <= 0:
            raise ValueError("flush_interval must be positive")
        
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        
        if self.max_queue_size <= 0:
            raise ValueError("max_queue_size must be positive")
        
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")
        
        if self.retry_attempts < 0:
            raise ValueError("retry_attempts must be non-negative")
        
        if self.retry_backoff < 1.0:
            raise ValueError("retry_backoff must be >= 1.0")
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides."""
        # Allow environment to be set via env var
        if not self.environment:
            self.environment = os.getenv("VANTAGE_ENVIRONMENT", "development")
        
        # Allow collector URL override
        env_collector_url = os.getenv("VANTAGE_COLLECTOR_URL")
        if env_collector_url:
            self.collector_url = env_collector_url
        
        # Allow debug override
        env_debug = os.getenv("VANTAGE_DEBUG", "").lower()
        if env_debug in ("true", "1", "yes"):
            self.debug = True
    
    @property
    def collector_endpoint(self) -> str:
        """Get the full collector endpoint URL."""
        return f"{self.collector_url.rstrip('/')}/v1/metrics"
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "service_name": self.service_name,
            "collector_url": self.collector_url,
            "flush_interval": self.flush_interval,
            "batch_size": self.batch_size,
            "max_queue_size": self.max_queue_size,
            "debug": self.debug,
            "environment": self.environment,
            "tags": self.tags,
            "timeout": self.timeout,
            "retry_attempts": self.retry_attempts,
            "retry_backoff": self.retry_backoff,
        }
