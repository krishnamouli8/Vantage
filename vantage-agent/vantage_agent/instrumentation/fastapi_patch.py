"""
Instrumentation for FastAPI applications.

Automatically tracks all incoming HTTP requests to FastAPI apps.
"""

import functools
from typing import Any, Callable
from vantage_agent.instrumentation.base import BaseInstrumentor
from vantage_agent.metrics.models import Metric
from vantage_agent.utils.timing import Timer
from vantage_agent.utils.logger import get_logger

logger = get_logger(__name__)


class FastAPIInstrumentor(BaseInstrumentor):
    """
    Instrumentor for FastAPI applications.
    
    Uses middleware to track all incoming HTTP requests.
    
    Tracks:
    - Request duration
    - HTTP method
    - Route/endpoint
    - Status code
    - Errors
    """
    
    def instrument(self) -> None:
        """Instrument FastAPI."""
        if self._instrumented:
            logger.warning("FastAPI is already instrumented")
            return
        
        try:
            from fastapi import FastAPI
            from starlette.middleware.base import BaseHTTPMiddleware
            from starlette.requests import Request
            from starlette.responses import Response
        except ImportError:
            logger.error("FastAPI not found - cannot instrument")
            raise
        
        # Store original __init__
        self._original_functions["fastapi_init"] = FastAPI.__init__
        
        # Create middleware class
        class VantageMiddleware(BaseHTTPMiddleware):
            def __init__(self, app, instrumentor):
                super().__init__(app)
                self.instrumentor = instrumentor
            
            async def dispatch(self, request: Request, call_next):
                return await self.instrumentor._traced_request(request, call_next)
        
        # Store middleware class
        self._middleware_class = VantageMiddleware
        
        # Wrap FastAPI.__init__ to automatically add middleware
        original_init = self._original_functions["fastapi_init"]
        
        @functools.wraps(original_init)
        def wrapped_init(app_self, *args, **kwargs):
            # Call original __init__
            original_init(app_self, *args, **kwargs)
            
            # Add our middleware
            app_self.add_middleware(VantageMiddleware, instrumentor=self)
        
        # Monkey-patch
        FastAPI.__init__ = wrapped_init
        
        self._mark_instrumented()
        logger.info("Successfully instrumented FastAPI")
    
    def uninstrument(self) -> None:
        """Restore FastAPI to its original state."""
        if not self._instrumented:
            logger.warning("FastAPI is not instrumented")
            return
        
        try:
            from fastapi import FastAPI
            
            if "fastapi_init" in self._original_functions:
                FastAPI.__init__ = self._original_functions["fastapi_init"]
            
            self._mark_uninstrumented()
            logger.info("Successfully uninstrumented FastAPI")
            
        except Exception as e:
            logger.error(f"Error uninstrumenting FastAPI: {e}", exc_info=True)
    
    async def _traced_request(self, request: Any, call_next: Callable) -> Any:
        """
        Traced request handler for FastAPI middleware.
        
        Args:
            request: Starlette Request object
            call_next: Next middleware in chain
        
        Returns:
            Response object
        """
        timer = Timer()
        timer.start()
        
        # Extract request info
        method = request.method
        path = request.url.path
        
        status_code = None
        error = None
        response = None
        
        try:
            # Call next middleware/route handler
            response = await call_next(request)
            status_code = response.status_code
            return response
            
        except Exception as e:
            error = str(e)
            status_code = 500
            raise
            
        finally:
            duration_ms = timer.stop()
            
            # Try to get the matched route pattern
            endpoint = self._get_route_pattern(request) or path
            
            # Create and collect metric
            metric = Metric.create_http_request_metric(
                service_name=self.config.service_name,
                endpoint=endpoint,
                method=method,
                status_code=status_code or 500,
                duration_ms=duration_ms,
                tags={
                    "framework": "fastapi",
                    "environment": self.config.environment or "development",
                    **self.config.tags,
                },
                error=error,
            )
            
            self.collector.collect(metric)
            
            if self.config.debug:
                logger.debug(
                    f"Traced FastAPI request: {method} {endpoint} -> {status_code} ({duration_ms:.2f}ms)"
                )
    
    def _get_route_pattern(self, request: Any) -> str:
        """
        Try to get the FastAPI route pattern.
        
        Args:
            request: Starlette Request object
        
        Returns:
            Route pattern or None
        """
        try:
            # Get the matched route from request scope
            if hasattr(request, "scope"):
                route = request.scope.get("route")
                if route and hasattr(route, "path"):
                    return route.path
        except Exception:
            pass
        
        return None
