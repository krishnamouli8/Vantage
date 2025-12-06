"""
Instrumentation for the requests library.

Monkey-patches requests.request() to automatically track HTTP calls.
"""

import functools
from typing import Any, Callable
from vantage_agent.instrumentation.base import BaseInstrumentor
from vantage_agent.metrics.models import Metric
from vantage_agent.utils.timing import Timer
from vantage_agent.utils.logger import get_logger

logger = get_logger(__name__)


class RequestsInstrumentor(BaseInstrumentor):
    """
    Instrumentor for the requests library.
    
    Monkey-patches requests.request() to automatically collect metrics
    for all HTTP requests made through the requests library.
    
    Tracks:
    - Request duration
    - HTTP method
    - URL/endpoint
    - Status code
    - Errors
    """
    
    def instrument(self) -> None:
        """Instrument the requests library."""
        if self._instrumented:
            logger.warning("requests library is already instrumented")
            return
        
        try:
            import requests
        except ImportError:
            logger.error("requests library not found - cannot instrument")
            raise
        
        # Store original function
        self._original_functions["request"] = requests.request
        
        # Create wrapped function
        @functools.wraps(requests.request)
        def wrapped_request(*args, **kwargs):
            return self._traced_request(
                self._original_functions["request"],
                *args,
                **kwargs
            )
        
        # Monkey-patch
        requests.request = wrapped_request
        requests.api.request = wrapped_request
        
        self._mark_instrumented()
        logger.info("Successfully instrumented requests library")
    
    def uninstrument(self) -> None:
        """Restore the requests library to its original state."""
        if not self._instrumented:
            logger.warning("requests library is not instrumented")
            return
        
        try:
            import requests
            
            # Restore original function
            if "request" in self._original_functions:
                requests.request = self._original_functions["request"]
                requests.api.request = self._original_functions["request"]
            
            self._mark_uninstrumented()
            logger.info("Successfully uninstrumented requests library")
            
        except Exception as e:
            logger.error(f"Error uninstrumenting requests: {e}", exc_info=True)
    
    def _traced_request(
        self,
        original_func: Callable,
        method: str,
        url: str,
        **kwargs
    ) -> Any:
        """
        Traced version of requests.request().
        
        Args:
            original_func: Original requests.request function
            method: HTTP method
            url: Request URL
            **kwargs: Additional arguments
        
        Returns:
            Response object
        """
        timer = Timer()
        timer.start()
        
        error = None
        status_code = None
        response = None
        
        try:
            # Call original function
            response = original_func(method, url, **kwargs)
            status_code = response.status_code
            return response
            
        except Exception as e:
            # Capture error
            error = str(e)
            raise
            
        finally:
            # Stop timer
            duration_ms = timer.stop()
            
            # Extract endpoint (remove query params and fragments)
            endpoint = self._extract_endpoint(url)
            
            # Create metric
            metric = Metric.create_http_request_metric(
                service_name=self.config.service_name,
                endpoint=endpoint,
                method=method.upper(),
                status_code=status_code or 0,
                duration_ms=duration_ms,
                tags={
                    "library": "requests",
                    "environment": self.config.environment or "development",
                    **self.config.tags,
                },
                error=error,
            )
            
            # Collect metric (non-blocking)
            self.collector.collect(metric)
            
            # Log if debug enabled
            if self.config.debug:
                logger.debug(
                    f"Traced request: {method} {endpoint} -> {status_code} ({duration_ms:.2f}ms)"
                )
    
    def _extract_endpoint(self, url: str) -> str:
        """
        Extract endpoint from URL (remove query params and fragments).
        
        Args:
            url: Full URL
        
        Returns:
            Endpoint without query params
        """
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        
        # Return path only (without query or fragment)
        endpoint = parsed.path or "/"
        
        # Limit length to prevent cardinality explosion
        if len(endpoint) > 200:
            endpoint = endpoint[:200] + "..."
        
        return endpoint
