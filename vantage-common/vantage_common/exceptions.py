"""Custom exception hierarchy for Vantage platform.

Provides consistent, specific exception types across all services
instead of using generic Exception class.
"""


class VantageException(Exception):
    """Base exception for all Vantage-specific errors.
    
    All custom exceptions should inherit from this class to allow
    for consistent error handling and logging across services.
    """
    
    def __init__(self, message: str, details: dict | None = None):
        """Initialize exception with message and optional details.
        
        Args:
            message: Human-readable error message
            details: Optional dictionary with additional context
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def to_dict(self) -> dict:
        """Convert exception to dictionary format for structured logging."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class DatabaseConnectionError(VantageException):
    """Raised when database connection fails or is lost.
    
    Used for both SQLite and ClickHouse connection issues.
    Includes automatic retry logic in most handlers.
    """
    pass


class KafkaConnectionError(VantageException):
    """Raised when Kafka/Redpanda connection fails.
    
    Triggers circuit breaker logic to prevent cascading failures.
    Services should degrade gracefully when this occurs.
    """
    pass


class ValidationError(VantageException):
    """Raised when input validation fails.
    
    Used for Pydantic validation errors, VQL syntax errors,
    and any other input validation failures.
    """
    pass


class RateLimitExceeded(VantageException):
    """Raised when rate limit threshold is exceeded.
    
    Should result in HTTP 429 response with Retry-After header.
    """
    
    def __init__(self, message: str, retry_after_seconds: int, details: dict | None = None):
        """Initialize with retry timing information.
        
        Args:
            message: Error message
            retry_after_seconds: Seconds until rate limit resets
            details: Additional context
        """
        super().__init__(message, details)
        self.retry_after_seconds = retry_after_seconds


class AuthenticationError(VantageException):
    """Raised when authentication fails.
    
    Used for invalid API keys, missing credentials,
    or expired tokens.
    """
    pass


class CircuitBreakerOpenError(VantageException):
    """Raised when circuit breaker is in OPEN state.
    
    Prevents additional requests to a failing service
    to allow it time to recover.
    """
    
    def __init__(self, message: str, retry_after_seconds: int):
        """Initialize with circuit breaker timing.
        
        Args:
            message: Error message
            retry_after_seconds: Seconds until circuit breaker allows retry
        """
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds
