"""
Base instrumentor class for all instrumentation modules.

Provides common functionality for monkey-patching libraries.
"""

from abc import ABC, abstractmethod
from typing import Optional
from vantage_agent.config import AgentConfig
from vantage_agent.metrics.collector import MetricCollector
from vantage_agent.utils.logger import get_logger

logger = get_logger(__name__)


class BaseInstrumentor(ABC):
    """
    Base class for all instrumentors.
    
    Provides common functionality for instrumenting libraries,
    including state management and lifecycle hooks.
    """
    
    def __init__(self, config: AgentConfig, collector: MetricCollector):
        """
        Initialize the instrumentor.
        
        Args:
            config: Agent configuration
            collector: Metric collector instance
        """
        self.config = config
        self.collector = collector
        self._instrumented = False
        self._original_functions = {}
    
    @abstractmethod
    def instrument(self) -> None:
        """
        Instrument the library.
        
        This method should monkey-patch the library and store
        references to original functions in self._original_functions.
        """
        pass
    
    @abstractmethod
    def uninstrument(self) -> None:
        """
        Restore the library to its original state.
        
        This method should restore all monkey-patched functions
        using the references stored in self._original_functions.
        """
        pass
    
    def is_instrumented(self) -> bool:
        """
        Check if the library is currently instrumented.
        
        Returns:
            True if instrumented, False otherwise
        """
        return self._instrumented
    
    def _mark_instrumented(self) -> None:
        """Mark the library as instrumented."""
        self._instrumented = True
    
    def _mark_uninstrumented(self) -> None:
        """Mark the library as uninstrumented."""
        self._instrumented = False
