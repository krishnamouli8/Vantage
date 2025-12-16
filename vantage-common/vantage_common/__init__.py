"""Vantage Common - Shared utilities for Vantage platform."""

__version__ = "0.1.0"

# Import and expose key components
from vantage_common.exceptions import (
    VantageException,
    DatabaseConnectionError,
    KafkaConnectionError,
    ValidationError,
    RateLimitExceeded,
    AuthenticationError,
    CircuitBreakerOpenError,
)

from vantage_common.constants import (
    BATCH_SIZE_DEFAULT,
    MAX_RETRY_ATTEMPTS,
    RETRY_BACKOFF_BASE_SECONDS,
    DATABASE_CONNECTION_TIMEOUT_SECONDS,
    DEFAULT_DATA_RETENTION_DAYS,
    RATE_LIMIT_MAX_REQUESTS,
    CIRCUIT_BREAKER_FAILURE_THRESHOLD,
)

from vantage_common.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState
from vantage_common.backpressure import BackpressureManager, BackpressureConfig

__all__ = [
    # Version
    "__version__",
    # Exceptions
    "VantageException",
    "DatabaseConnectionError",
    "KafkaConnectionError",
    "ValidationError",
    "RateLimitExceeded",
    "AuthenticationError",
    "CircuitBreakerOpenError",
    # Constants
    "BATCH_SIZE_DEFAULT",
    "MAX_RETRY_ATTEMPTS",
    "RETRY_BACKOFF_BASE_SECONDS",
    "DATABASE_CONNECTION_TIMEOUT_SECONDS",
    "DEFAULT_DATA_RETENTION_DAYS",
    "RATE_LIMIT_MAX_REQUESTS",
    "CIRCUIT_BREAKER_FAILURE_THRESHOLD",
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitState",
    # Backpressure
    "BackpressureManager",
    "BackpressureConfig",
]
