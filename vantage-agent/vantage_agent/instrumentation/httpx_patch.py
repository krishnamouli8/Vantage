"""
Instrumentation for the httpx library.

Monkey-patches httpx.Client and httpx.AsyncClient to track HTTP calls.
"""

import functools
from typing import Any, Callable
from vantage_agent.instrumentation.base import BaseInstrumentor
from vantage_agent.metrics.models import Metric
from vantage_agent.utils.timing import Timer
from vantage_agent.utils.logger import get_logger

logger = get_logger(__name__)


class HttpxInstrumentor(BaseInstrumentor):
    """
    Instrumentor for the httpx library.
    
    Monkey-patches httpx.Client.request() and httpx.AsyncClient.request()
    to automatically collect metrics for all HTTP requests.
    
    Supports both sync and async clients.
    """
    
    def instrument(self) -> None:
        """Instrument the httpx library."""
        if self._instrumented:
            logger.warning("httpx library is already instrumented")
            return
        
        try:
            import httpx
        except ImportError:
            logger.error("httpx library not found - cannot instrument")
            raise
        
        # Store original functions
        self._original_functions["client_request"] = httpx.Client.request
        self._original_functions["async_client_request"] = httpx.AsyncClient.request
        
        # Wrap sync client
        @functools.wraps(httpx.Client.request)
        def wrapped_sync_request(client_self, *args, **kwargs):
            return self._traced_sync_request(
                self._original_functions["client_request"],
                client_self,
                *args,
                **kwargs
            )
        
        # Wrap async client
        @functools.wraps(httpx.AsyncClient.request)
        async def wrapped_async_request(client_self, *args, **kwargs):
            return await self._traced_async_request(
                self._original_functions["async_client_request"],
                client_self,
                *args,
                **kwargs
            )
        
        # Monkey-patch
        httpx.Client.request = wrapped_sync_request
        httpx.AsyncClient.request = wrapped_async_request
        
        self._mark_instrumented()
        logger.info("Successfully instrumented httpx library")
    
    def uninstrument(self) -> None:
        """Restore the httpx library to its original state."""
        if not self._instrumented:
            logger.warning("httpx library is not instrumented")
            return
        
        try:
            import httpx
            
            # Restore original functions
            if "client_request" in self._original_functions:
                httpx.Client.request = self._original_functions["client_request"]
            
            if "async_client_request" in self._original_functions:
                httpx.AsyncClient.request = self._original_functions["async_client_request"]
            
            self._mark_uninstrumented()
            logger.info("Successfully uninstrumented httpx library")
            
        except Exception as e:
            logger.error(f"Error uninstrumenting httpx: {e}", exc_info=True)
    
    def _traced_sync_request(
        self,
        original_func: Callable,
        client_self: Any,
        method: str,
        url: Any,
        **kwargs
    ) -> Any:
        """
        Traced version of httpx.Client.request().
        
        Args:
            original_func: Original request function
            client_self: Client instance
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
            response = original_func(client_self, method, url, **kwargs)
            status_code = response.status_code
            return response
            
        except Exception as e:
            error = str(e)
            raise
            
        finally:
            duration_ms = timer.stop()
            
            # Convert URL to string
            url_str = str(url)
            endpoint = self._extract_endpoint(url_str)
            
            # Create and collect metric
            metric = Metric.create_http_request_metric(
                service_name=self.config.service_name,
                endpoint=endpoint,
                method=method.upper(),
                status_code=status_code or 0,
                duration_ms=duration_ms,
                tags={
                    "library": "httpx",
                    "client_type": "sync",
                    "environment": self.config.environment or "development",
                    **self.config.tags,
                },
                error=error,
            )
            
            self.collector.collect(metric)
            
            if self.config.debug:
                logger.debug(
                    f"Traced httpx request: {method} {endpoint} -> {status_code} ({duration_ms:.2f}ms)"
                )
    
    async def _traced_async_request(
        self,
        original_func: Callable,
        client_self: Any,
        method: str,
        url: Any,
        **kwargs
    ) -> Any:
        """
        Traced version of httpx.AsyncClient.request().
        
        Args:
            original_func: Original request function
            client_self: AsyncClient instance
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
            # Call original async function
            response = await original_func(client_self, method, url, **kwargs)
            status_code = response.status_code
            return response
            
        except Exception as e:
            error = str(e)
            raise
            
        finally:
            duration_ms = timer.stop()
            
            url_str = str(url)
            endpoint = self._extract_endpoint(url_str)
            
            # Create and collect metric
            metric = Metric.create_http_request_metric(
                service_name=self.config.service_name,
                endpoint=endpoint,
                method=method.upper(),
                status_code=status_code or 0,
                duration_ms=duration_ms,
                tags={
                    "library": "httpx",
                    "client_type": "async",
                    "environment": self.config.environment or "development",
                    **self.config.tags,
                },
                error=error,
            )
            
            self.collector.collect(metric)
            
            if self.config.debug:
                logger.debug(
                    f"Traced async httpx request: {method} {endpoint} -> {status_code} ({duration_ms:.2f}ms)"
                )
    
    def _extract_endpoint(self, url: str) -> str:
        """Extract endpoint from URL."""
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        endpoint = parsed.path or "/"
        
        if len(endpoint) > 200:
            endpoint = endpoint[:200] + "..."
        
        return endpoint
