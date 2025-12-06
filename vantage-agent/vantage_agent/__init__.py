"""
Vantage Agent - Production-Grade APM Library

A lightweight, non-blocking application performance monitoring agent
that auto-instruments Python applications with <1ms overhead.

Usage:
    from vantage_agent import init_agent
    
    init_agent(
        service_name="my-service",
        collector_url="http://localhost:8000",
        auto_instrument=["requests", "flask"]
    )
"""

__version__ = "0.1.0"
__author__ = "Vantage Team"

from vantage_agent.config import AgentConfig
from vantage_agent.metrics.collector import MetricCollector
from vantage_agent.metrics.exporter import MetricExporter
from vantage_agent.instrumentation.requests_patch import RequestsInstrumentor
from vantage_agent.instrumentation.httpx_patch import HttpxInstrumentor
from vantage_agent.instrumentation.flask_patch import FlaskInstrumentor
from vantage_agent.instrumentation.fastapi_patch import FastAPIInstrumentor
from vantage_agent.utils.logger import get_logger

logger = get_logger(__name__)

# Global instances
_collector = None
_exporter = None
_instrumentors = {}


def init_agent(
    service_name: str,
    collector_url: str = "http://localhost:8000",
    auto_instrument: list[str] = None,
    flush_interval: int = 5,
    batch_size: int = 100,
    max_queue_size: int = 10000,
    enabled: bool = True,
    debug: bool = False,
) -> None:
    """
    Initialize the Vantage APM agent.
    
    Args:
        service_name: Name of the service being monitored
        collector_url: URL of the Vantage collector API
        auto_instrument: List of libraries to auto-instrument 
                        (e.g., ["requests", "flask", "fastapi"])
        flush_interval: Seconds between metric flushes (default: 5)
        batch_size: Number of metrics to batch before flushing (default: 100)
        max_queue_size: Maximum metrics in queue (default: 10000)
        enabled: Whether the agent is enabled (default: True)
        debug: Enable debug logging (default: False)
    
    Example:
        >>> init_agent(
        ...     service_name="api-gateway",
        ...     collector_url="http://collector:8000",
        ...     auto_instrument=["requests", "flask"]
        ... )
    """
    global _collector, _exporter, _instrumentors
    
    if not enabled:
        logger.info("Vantage agent is disabled")
        return
    
    # Create configuration
    config = AgentConfig(
        service_name=service_name,
        collector_url=collector_url,
        flush_interval=flush_interval,
        batch_size=batch_size,
        max_queue_size=max_queue_size,
        debug=debug,
    )
    
    logger.info(
        f"Initializing Vantage agent for service '{service_name}'",
        extra={"collector_url": collector_url}
    )
    
    # Initialize metric collector (thread-safe queue)
    _collector = MetricCollector(config)
    
    # Initialize and start background exporter
    _exporter = MetricExporter(config, _collector)
    _exporter.start()
    
    # Auto-instrument requested libraries
    if auto_instrument:
        for library in auto_instrument:
            _instrument_library(library, config, _collector)
    
    logger.info(
        f"Vantage agent initialized successfully",
        extra={
            "auto_instrument": auto_instrument,
            "flush_interval": flush_interval,
            "batch_size": batch_size,
        }
    )


def _instrument_library(library: str, config: AgentConfig, collector: MetricCollector) -> None:
    """
    Instrument a specific library.
    
    Args:
        library: Name of the library to instrument
        config: Agent configuration
        collector: Metric collector instance
    """
    global _instrumentors
    
    library = library.lower()
    
    if library in _instrumentors:
        logger.warning(f"Library '{library}' is already instrumented")
        return
    
    try:
        if library == "requests":
            instrumentor = RequestsInstrumentor(config, collector)
        elif library == "httpx":
            instrumentor = HttpxInstrumentor(config, collector)
        elif library == "flask":
            instrumentor = FlaskInstrumentor(config, collector)
        elif library == "fastapi":
            instrumentor = FastAPIInstrumentor(config, collector)
        else:
            logger.warning(f"Unknown library '{library}' - skipping instrumentation")
            return
        
        instrumentor.instrument()
        _instrumentors[library] = instrumentor
        logger.info(f"Successfully instrumented '{library}'")
        
    except ImportError:
        logger.warning(f"Library '{library}' not found - skipping instrumentation")
    except Exception as e:
        logger.error(f"Failed to instrument '{library}': {e}", exc_info=True)


def shutdown() -> None:
    """
    Gracefully shutdown the agent, flushing any remaining metrics.
    
    This is automatically called on process exit, but can be called
    manually if needed.
    """
    global _exporter, _instrumentors
    
    logger.info("Shutting down Vantage agent")
    
    # Uninstrument all libraries
    for library, instrumentor in _instrumentors.items():
        try:
            instrumentor.uninstrument()
            logger.debug(f"Uninstrumented '{library}'")
        except Exception as e:
            logger.error(f"Error uninstrumenting '{library}': {e}")
    
    # Stop exporter and flush remaining metrics
    if _exporter:
        _exporter.stop()
    
    logger.info("Vantage agent shutdown complete")


# Register shutdown handler
import atexit
atexit.register(shutdown)


__all__ = [
    "init_agent",
    "shutdown",
    "__version__",
]
