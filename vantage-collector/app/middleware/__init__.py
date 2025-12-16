"""Middleware package for Vantage Collector."""

from app.middleware.rate_limiter import RateLimitMiddleware

__all__ = ["RateLimitMiddleware"]
