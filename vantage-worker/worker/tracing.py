"""
Distributed Trace Correlation

Lightweight distributed tracing using HTTP header propagation.
Captures request flows across microservices without OpenTelemetry dependency.
"""

import uuid
import time
import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from contextvars import ContextVar

logger = logging.getLogger(__name__)

# Thread-local trace context
_trace_context: ContextVar[Optional["TraceContext"]] = ContextVar(
    "trace_context", default=None
)


@dataclass
class TraceContext:
    """Lightweight distributed tracing context"""

    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    service_name: str = ""
    start_time: float = field(default_factory=time.time)
    baggage: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def create_root(cls, service_name: str) -> "TraceContext":
        """Create root trace context"""
        return cls(
            trace_id=str(uuid.uuid4()),
            span_id=str(uuid.uuid4()),
            service_name=service_name,
        )

    @classmethod
    def from_headers(cls, headers: Dict[str, str], service_name: str) -> "TraceContext":
        """Extract trace context from HTTP headers"""
        trace_id = headers.get("X-Vantage-Trace-Id")
        parent_span_id = headers.get("X-Vantage-Span-Id")
        baggage_header = headers.get("X-Vantage-Baggage", "{}")

        try:
            baggage = json.loads(baggage_header)
        except json.JSONDecodeError:
            baggage = {}

        if trace_id:
            return cls(
                trace_id=trace_id,
                span_id=str(uuid.uuid4()),
                parent_span_id=parent_span_id,
                service_name=service_name,
                baggage=baggage,
            )

        return cls.create_root(service_name)

    def to_headers(self) -> Dict[str, str]:
        """Convert to HTTP headers for propagation"""
        headers = {
            "X-Vantage-Trace-Id": self.trace_id,
            "X-Vantage-Span-Id": self.span_id,
        }

        if self.baggage:
            try:
                headers["X-Vantage-Baggage"] = json.dumps(self.baggage)
            except Exception as e:
                logger.warning(f"Failed to serialize baggage: {e}")

        return headers

    def create_child_span(self, operation_name: str) -> "Span":
        """Create child span for operation"""
        return Span(
            trace_id=self.trace_id,
            parent_span_id=self.span_id,
            service_name=self.service_name,
            operation_name=operation_name,
        )


@dataclass
class Span:
    """Individual span in distributed trace"""

    trace_id: str
    service_name: str
    operation_name: str
    span_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_span_id: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    tags: Dict[str, str] = field(default_factory=dict)
    logs: List[Dict] = field(default_factory=list)
    status: str = "ok"
    error: bool = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error = True
            self.status = "error"
            self.set_tag("error.type", exc_type.__name__)
            self.set_tag("error.message", str(exc_val))

        self.finish()
        return False

    def finish(self):
        """Complete the span"""
        if self.end_time is None:
            self.end_time = time.time()
            self.duration_ms = (self.end_time - self.start_time) * 1000

    def set_tag(self, key: str, value: str):
        """Add tag to span"""
        try:
            self.tags[key] = str(value)
        except Exception as e:
            logger.warning(f"Failed to set tag {key}: {e}")

    def log(self, message: str, **kwargs):
        """Add log to span"""
        try:
            log_entry = {
                "timestamp": time.time(),
                "message": message,
                **kwargs,
            }
            self.logs.append(log_entry)
        except Exception as e:
            logger.warning(f"Failed to add log: {e}")

    def to_dict(self) -> Dict:
        """Convert span to dictionary"""
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "service_name": self.service_name,
            "operation_name": self.operation_name,
            "start_time": int(self.start_time * 1000),
            "end_time": int(self.end_time * 1000) if self.end_time else None,
            "duration_ms": self.duration_ms,
            "tags": json.dumps(self.tags),
            "logs": json.dumps(self.logs),
            "status": self.status,
            "error": 1 if self.error else 0,
        }


class Tracer:
    """Tracer for creating and managing spans"""

    def __init__(self, service_name: str):
        self.service_name = service_name

    def start_trace(
        self, operation_name: str, headers: Optional[Dict[str, str]] = None
    ) -> Span:
        """Start a new trace or continue existing one"""
        if headers:
            ctx = TraceContext.from_headers(headers, self.service_name)
        else:
            ctx = TraceContext.create_root(self.service_name)

        _trace_context.set(ctx)

        span = Span(
            trace_id=ctx.trace_id,
            parent_span_id=ctx.parent_span_id,
            service_name=self.service_name,
            operation_name=operation_name,
        )

        return span

    def start_span(self, operation_name: str) -> Span:
        """Start a child span"""
        ctx = _trace_context.get()

        if not ctx:
            # No active trace, create root
            return self.start_trace(operation_name)

        span = ctx.create_child_span(operation_name)
        return span

    @staticmethod
    def get_current_context() -> Optional[TraceContext]:
        """Get current trace context"""
        return _trace_context.get()

    @staticmethod
    def inject_headers(headers: Dict[str, str]) -> Dict[str, str]:
        """Inject trace headers into outgoing request"""
        ctx = _trace_context.get()
        if ctx:
            headers.update(ctx.to_headers())
        return headers


# Global tracer instance
_tracer: Optional[Tracer] = None


def init_tracer(service_name: str):
    """Initialize global tracer"""
    global _tracer
    _tracer = Tracer(service_name)
    logger.info(f"Tracer initialized for service: {service_name}")


def get_tracer() -> Optional[Tracer]:
    """Get global tracer instance"""
    return _tracer
