"""
Trace Helper for Collector

Helper functions for instrumenting the collector with distributed tracing.
"""

import json
import logging
from typing import Optional, Dict
from fastapi import Request

logger = logging.getLogger(__name__)


def extract_trace_context(request: Request) -> Optional[Dict[str, str]]:
    """
    Extract trace context from HTTP headers
    
    Returns dict with trace_id, span_id, or None
    """
    try:
        trace_id = request.headers.get("X-Vantage-Trace-Id")
        span_id = request.headers.get("X-Vantage-Span-Id")

        if trace_id and span_id:
            return {
                "trace_id": trace_id,
                "span_id": span_id,
            }

        return None

    except Exception as e:
        logger.warning(f"Error extracting trace context: {e}")
        return None


def add_trace_info_to_metric(metric: Dict, trace_context: Optional[Dict]) -> Dict:
    """
    Add trace information to metric if available
    
    Args:
        metric: Metric dictionary
        trace_context: Optional trace context from extract_trace_context
        
    Returns:
        Modified metric with trace info
    """
    if not trace_context:
        return metric

    try:
        # Add trace IDs to metric tags
        if "tags" not in metric:
            metric["tags"] = {}

        metric["tags"]["trace_id"] = trace_context.get("trace_id")
        metric["tags"]["span_id"] = trace_context.get("span_id")

        # Also set top-level fields for easier querying
        metric["trace_id"] = trace_context.get("trace_id")
        metric["span_id"] = trace_context.get("span_id")

        return metric

    except Exception as e:
        logger.warning(f"Error adding trace info to metric: {e}")
        return metric
