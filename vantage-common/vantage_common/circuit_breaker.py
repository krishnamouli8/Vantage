"""Circuit breaker implementation for Kafka connections.

Implements circuit breaker pattern to prevent cascading failures when Kafka is unavailable.
"""

import time
import logging
from enum import Enum
from typing import Callable, Any
from dataclasses import dataclass
from vantage_common.exceptions import CircuitBreakerOpenError

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 2  # Successes to close from half-open
    timeout_seconds: int = 60  # Time before attempting recovery
    half_open_max_calls: int = 1  # Max calls in half-open state


class CircuitBreaker:
    """Circuit breaker for preventing cascading failures.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests rejected immediately
    - HALF_OPEN: Testing if service recovered, limited requests allowed
    """
    
    def __init__(self, config: CircuitBreakerConfig | None = None):
        """Initialize circuit breaker.
        
        Args:
            config: Circuit breaker configuration
        """
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.half_open_calls = 0
        
        logger.info(
            f"Circuit breaker initialized: "
            f"failure_threshold={self.config.failure_threshold}, "
            f"timeout={self.config.timeout_seconds}s"
        )
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection.
        
        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._move_to_half_open()
            else:
                raise CircuitBreakerOpenError(
                    "Circuit breaker is OPEN",
                    details={
                        "failures": self.failure_count,
                        "retry_after": self._time_until_retry()
                    }
                )
        
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.config.half_open_max_calls:
                raise CircuitBreakerOpenError(
                    "Circuit breaker is HALF_OPEN with max calls reached"
                )
            self.half_open_calls += 1
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise
    
    def _on_success(self) -> None:
        """Handle successful call."""
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._move_to_closed()
        
        logger.debug(f"Circuit breaker call succeeded, state={self.state.value}")
    
    def _on_failure(self, error: Exception) -> None:
        """Handle failed call.
        
        Args:
            error: The exception that occurred
        """
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            # Failed during recovery attempt
            self._move_to_open()
        elif self.failure_count >= self.config.failure_threshold:
            self._move_to_open()
        
        logger.warning(
            f"Circuit breaker call failed: {error}, "
            f"failures={self.failure_count}/{self.config.failure_threshold}, "
            f"state={self.state.value}"
        )
    
    def _move_to_open(self) -> None:
        """Move circuit to OPEN state."""
        self.state = CircuitState.OPEN
        self.success_count = 0
        self.half_open_calls = 0
        logger.error(
            f"Circuit breaker OPENED after {self.failure_count} failures, "
            f"will retry in {self.config.timeout_seconds}s"
        )
    
    def _move_to_half_open(self) -> None:
        """Move circuit to HALF_OPEN state."""
        self.state = CircuitState.HALF_OPEN
        self.half_open_calls = 0
        self.success_count = 0
        logger.info("Circuit breaker moved to HALF_OPEN, testing recovery")
    
    def _move_to_closed(self) -> None:
        """Move circuit to CLOSED state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        logger.info("Circuit breaker CLOSED, service recovered")
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset.
        
        Returns:
            True if should attempt reset
        """
        return (time.time() - self.last_failure_time) >= self.config.timeout_seconds
    
    def _time_until_retry(self) -> int:
        """Calculate seconds until retry attempt.
        
        Returns:
            Seconds until retry
        """
        elapsed = time.time() - self.last_failure_time
        remaining = max(0, self.config.timeout_seconds - elapsed)
        return int(remaining)
    
    def reset(self) -> None:
        """Manually reset circuit breaker."""
        self._move_to_closed()
        logger.info("Circuit breaker manually reset")
    
    def get_state(self) -> dict:
        """Get current circuit breaker state.
        
        Returns:
            State dictionary
        """
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "time_until_retry": self._time_until_retry() if self.state == CircuitState.OPEN else 0
        }
