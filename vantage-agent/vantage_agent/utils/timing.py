"""
High-precision timing utilities for performance measurement.

Uses time.perf_counter() for nanosecond precision.
"""

import time
from typing import Optional


class Timer:
    """
    High-precision timer for measuring code execution time.
    
    Uses time.perf_counter() which provides the highest available resolution
    for measuring short durations.
    
    Example:
        >>> timer = Timer()
        >>> timer.start()
        >>> # ... do some work ...
        >>> elapsed_ms = timer.stop()
        >>> print(f"Took {elapsed_ms:.2f}ms")
        
        >>> # Or use as context manager
        >>> with Timer() as timer:
        ...     # ... do some work ...
        >>> print(f"Took {timer.elapsed_ms:.2f}ms")
    """
    
    def __init__(self):
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
    
    def start(self) -> None:
        """Start the timer."""
        self._start_time = time.perf_counter()
        self._end_time = None
    
    def stop(self) -> float:
        """
        Stop the timer and return elapsed time in milliseconds.
        
        Returns:
            Elapsed time in milliseconds
        """
        if self._start_time is None:
            raise RuntimeError("Timer was not started")
        
        self._end_time = time.perf_counter()
        return self.elapsed_ms
    
    @property
    def elapsed_ms(self) -> float:
        """
        Get elapsed time in milliseconds.
        
        Returns:
            Elapsed time in milliseconds
        """
        if self._start_time is None:
            return 0.0
        
        end_time = self._end_time if self._end_time is not None else time.perf_counter()
        return (end_time - self._start_time) * 1000.0
    
    @property
    def elapsed_seconds(self) -> float:
        """
        Get elapsed time in seconds.
        
        Returns:
            Elapsed time in seconds
        """
        return self.elapsed_ms / 1000.0
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False
    
    def reset(self) -> None:
        """Reset the timer."""
        self._start_time = None
        self._end_time = None
