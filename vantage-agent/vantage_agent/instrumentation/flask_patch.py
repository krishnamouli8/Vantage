"""
Instrumentation for Flask applications.

Automatically tracks all incoming HTTP requests to Flask apps.
"""

import functools
from typing import Any, Callable
from vantage_agent.instrumentation.base import BaseInstrumentor
from vantage_agent.metrics.models import Metric
from vantage_agent.utils.timing import Timer
from vantage_agent.utils.logger import get_logger

logger = get_logger(__name__)


class FlaskInstrumentor(BaseInstrumentor):
    """
    Instrumentor for Flask applications.
    
    Instruments Flask's request handling to automatically track
    all incoming HTTP requests.
    
    Tracks:
    - Request duration
    - HTTP method
    - Route/endpoint
    - Status code
    - Errors
    """
    
    def instrument(self) -> None:
        """Instrument Flask."""
        if self._instrumented:
            logger.warning("Flask is already instrumented")
            return
        
        try:
            from flask import Flask
        except ImportError:
            logger.error("Flask not found - cannot instrument")
            raise
        
        # Store original function
        self._original_functions["wsgi_app"] = Flask.wsgi_app
        
        # Create wrapper
        def wrapped_wsgi_app(app_self, environ, start_response):
            return self._traced_wsgi_app(
                self._original_functions["wsgi_app"],
                app_self,
                environ,
                start_response
            )
        
        # Monkey-patch
        Flask.wsgi_app = wrapped_wsgi_app
        
        self._mark_instrumented()
        logger.info("Successfully instrumented Flask")
    
    def uninstrument(self) -> None:
        """Restore Flask to its original state."""
        if not self._instrumented:
            logger.warning("Flask is not instrumented")
            return
        
        try:
            from flask import Flask
            
            if "wsgi_app" in self._original_functions:
                Flask.wsgi_app = self._original_functions["wsgi_app"]
            
            self._mark_uninstrumented()
            logger.info("Successfully uninstrumented Flask")
            
        except Exception as e:
            logger.error(f"Error uninstrumenting Flask: {e}", exc_info=True)
    
    def _traced_wsgi_app(
        self,
        original_func: Callable,
        app_self: Any,
        environ: dict,
        start_response: Callable
    ) -> Any:
        """
        Traced version of Flask.wsgi_app().
        
        Args:
            original_func: Original wsgi_app function
            app_self: Flask app instance
            environ: WSGI environ dict
            start_response: WSGI start_response callable
        
        Returns:
            WSGI response
        """
        timer = Timer()
        timer.start()
        
        # Extract request info from environ
        method = environ.get("REQUEST_METHOD", "GET")
        path = environ.get("PATH_INFO", "/")
        
        status_code = None
        error = None
        
        # Wrap start_response to capture status code
        def wrapped_start_response(status, headers, exc_info=None):
            nonlocal status_code
            # Extract status code from status string (e.g., "200 OK")
            status_code = int(status.split()[0])
            return start_response(status, headers, exc_info)
        
        try:
            # Call original function
            response = original_func(app_self, environ, wrapped_start_response)
            return response
            
        except Exception as e:
            error = str(e)
            raise
            
        finally:
            duration_ms = timer.stop()
            
            # Try to get the matched route
            endpoint = self._get_flask_endpoint(app_self, environ) or path
            
            # Create and collect metric
            metric = Metric.create_http_request_metric(
                service_name=self.config.service_name,
                endpoint=endpoint,
                method=method,
                status_code=status_code or 500,
                duration_ms=duration_ms,
                tags={
                    "framework": "flask",
                    "environment": self.config.environment or "development",
                    **self.config.tags,
                },
                error=error,
            )
            
            self.collector.collect(metric)
            
            if self.config.debug:
                logger.debug(
                    f"Traced Flask request: {method} {endpoint} -> {status_code} ({duration_ms:.2f}ms)"
                )
    
    def _get_flask_endpoint(self, app: Any, environ: dict) -> str:
        """
        Try to get the Flask route pattern.
        
        Args:
            app: Flask app instance
            environ: WSGI environ dict
        
        Returns:
            Route pattern or None
        """
        try:
            from flask import Flask
            from flask.ctx import RequestContext
            
            # Create a request context to access the matched route
            with app.request_context(environ):
                from flask import request
                
                # Get the matched endpoint
                if request.url_rule:
                    return str(request.url_rule)
                
        except Exception:
            # If we can't get the route, just return None
            pass
        
        return None
