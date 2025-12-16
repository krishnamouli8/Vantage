"""Vantage Common Utilities Package.

Shared utilities and components used across all Vantage services.
"""

__version__ = "0.1.0"

from vantage_common.exceptions import (
    VantageException,
    DatabaseConnectionError,
    KafkaConnectionError,
    ValidationError,
    RateLimitExceeded,
    AuthenticationError,
)
from vantage_common.constants import (
    BATCH_SIZE_DEFAULT,
    RETRY_BACKOFF_BASE_SECONDS,
    MAX_RETRY_ATTEMPTS,
    DOWNSAMPLING_RESOLUTION_MINUTES,
    DEFAULT_DATA_RETENTION_DAYS,
    KAFKA_CONSUMER_TIMEOUT_MS,
    DATABASE_CONNECTION_TIMEOUT_SECONDS,
    RATE_LIMIT_WINDOW_SECONDS,
    RATE_LIMIT_MAX_REQUESTS,
)

__all__ = [
    "VantageException",
    "DatabaseConnectionError",
    "KafkaConnectionError",
    "ValidationError",
    "RateLimitExceeded",
    "AuthenticationError",
    "BATCH_SIZE_DEFAULT",
    "RETRY_BACKOFF_BASE_SECONDS",
    "MAX_RETRY_ATTEMPTS",
    "DOWNSAMPLING_RESOLUTION_MINUTES",
    "DEFAULT_DATA_RETENTION_DAYS",
    "KAFKA_CONSUMER_TIMEOUT_MS",
    "DATABASE_CONNECTION_TIMEOUT_SECONDS",
    "RATE_LIMIT_WINDOW_SECONDS",
    "RATE_LIMIT_MAX_REQUESTS",
]
