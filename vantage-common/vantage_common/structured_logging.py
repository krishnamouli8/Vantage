"""Structured logging configuration using structlog.

Provides consistent, structured JSON logging across all services
with automatic trace ID injection and standardized field names.
"""

import logging
import sys
from typing import Any
import structlog
from structlog.types import EventDict, Processor


def add_service_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add service name to all log entries.
    
    Should be configured with service name in setup_logging().
    """
    # Service name will be added via configure(context_class=dict)
    return event_dict


def add_timestamp(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add ISO timestamp to log entries."""
    import datetime
    event_dict["timestamp"] = datetime.datetime.utcnow().isoformat() + "Z"
    return event_dict


def add_log_level(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add log level to event dict."""
    event_dict["level"] = method_name
    return event_dict


def setup_logging(
    service_name: str,
    level: str = "INFO",
    json_output: bool = True
) -> None:
    """Configure structured logging for a service.
    
    Args:
        service_name: Name of the service (e.g., "vantage-collector")
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: If True, output JSON. If False, use human-readable format.
    
    Example:
        >>> from vantage_common.structured_logging import setup_logging, get_logger
        >>> setup_logging("vantage-collector", level="DEBUG")
        >>> logger = get_logger(__name__)
        >>> logger.info("request_received", endpoint="/v1/metrics", method="POST")
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configure stdlib logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=numeric_level,
    )
    
    # Processors pipeline
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        add_timestamp,
        add_log_level,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
    ]
    
    if json_output:
        # Production: JSON output
        processors.extend([
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ])
    else:
        # Development: Human-readable output with colors
        processors.extend([
            structlog.dev.ConsoleRenderer()
        ])
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Bind service name to all loggers
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(service=service_name)


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured structlog logger
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("event_occurred", user_id=123, action="login")
        {
            "event": "event_occurred",
            "user_id": 123,
            "action": "login",
            "service": "vantage-api",
            "timestamp": "2025-12-13T15:00:00Z",
            "level": "info"
        }
    """
    return structlog.get_logger(name)


def bind_trace_id(trace_id: str) -> None:
    """Bind trace ID to context for all subsequent log calls.
    
    Args:
        trace_id: Distributed trace ID
    
    Example:
        >>> bind_trace_id("abc-123-def")
        >>> logger.info("processing_request")
        # Will include "trace_id": "abc-123-def" in output
    """
    structlog.contextvars.bind_contextvars(trace_id=trace_id)


def unbind_trace_id() -> None:
    """Remove trace ID from logging context."""
    structlog.contextvars.unbind_contextvars("trace_id")
