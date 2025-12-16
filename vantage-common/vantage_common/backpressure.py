"""Backpressure handling for message processing.

Implements adaptive backpressure based on queue depth and processing capacity.
"""

import time
import logging
from dataclasses import dataclass
from vantage_common.constants import (
    BATCH_SIZE_DEFAULT,
    MAX_QUEUE_DEPTH,
    BACKPRESSURE_THRESHOLD_RATIO,
)

logger = logging.getLogger(__name__)


@dataclass
class BackpressureConfig:
    """Configuration for backpressure handling."""
    max_queue_depth: int = MAX_QUEUE_DEPTH  # 10000
    threshold_ratio: float = BACKPRESSURE_THRESHOLD_RATIO  # 0.8
    min_batch_size: int = 10
    max_batch_size: int = BATCH_SIZE_DEFAULT  # 100
    cooldown_seconds: int = 5


class BackpressureManager:
    """Manages backpressure for message processing.
    
    Adjusts batch sizes and introduces delays based on queue depth
    to prevent system overload.
    """
    
    def __init__(self, config: BackpressureConfig | None = None):
        """Initialize backpressure manager.
        
        Args:
            config: Backpressure configuration
        """
        self.config = config or BackpressureConfig()
        self.current_batch_size = self.config.max_batch_size
        self.last_adjustment_time = 0
        
        logger.info(
            f"Backpressure manager initialized: "
            f"max_queue={self.config.max_queue_depth}, "
            f"threshold={self.config.threshold_ratio}"
        )
    
    def should_throttle(self, queue_depth: int) -> bool:
        """Check if processing should be throttled.
        
        Args:
            queue_depth: Current queue depth
            
        Returns:
            True if should throttle
        """
        threshold = self.config.max_queue_depth * self.config.threshold_ratio
        return queue_depth >= threshold
    
    def get_batch_size(self, queue_depth: int) -> int:
        """Calculate adaptive batch size based on queue depth.
        
        Args:
            queue_depth: Current queue depth
            
        Returns:
            Recommended batch size
        """
        if queue_depth == 0:
            return self.config.min_batch_size
        
        # Calculate pressure ratio (0.0 to 1.0+)
        pressure_ratio = queue_depth / self.config.max_queue_depth
        
        if pressure_ratio < 0.3:
            # Low pressure: use smaller batches for lower latency
            batch_size = self.config.min_batch_size
        elif pressure_ratio < 0.7:
            # Medium pressure: use medium batches
            batch_size = (self.config.min_batch_size + self.config.max_batch_size) // 2
        else:
            # High pressure: use larger batches for throughput
            batch_size = self.config.max_batch_size
        
        # Smooth adjustment
        if abs(batch_size - self.current_batch_size) > 10:
            self.current_batch_size = batch_size
            logger.info(
                f"Batch size adjusted to {batch_size} "
                f"(queue_depth={queue_depth}, pressure={pressure_ratio:.2f})"
            )
        
        return self.current_batch_size
    
    def get_delay(self, queue_depth: int) -> float:
        """Calculate processing delay based on queue depth.
        
        Args:
            queue_depth: Current queue depth
            
        Returns:
            Delay in seconds (0 if no delay needed)
        """
        if not self.should_throttle(queue_depth):
            return 0.0
        
        # Calculate how far over threshold we are
        threshold = self.config.max_queue_depth * self.config.threshold_ratio
        over_threshold = (queue_depth - threshold) / threshold
        
        # Exponential delay: 0.1s to 2s
        delay = min(2.0, 0.1 * (2 ** over_threshold))
        
        return delay
    
    def apply_backpressure(self, queue_depth: int) -> dict:
        """Apply backpressure based on queue depth.
        
        Args:
            queue_depth: Current queue depth
            
        Returns:
            Backpressure metrics
        """
        batch_size = self.get_batch_size(queue_depth)
        delay = self.get_delay(queue_depth)
        throttled = self.should_throttle(queue_depth)
        
        if throttled and delay > 0:
            logger.warning(
                f"Backpressure active: queue_depth={queue_depth}, "
                f"delay={delay:.2f}s, batch_size={batch_size}"
            )
            time.sleep(delay)
        
        return {
            "queue_depth": queue_depth,
            "batch_size": batch_size,
            "delay_seconds": delay,
            "throttled": throttled,
            "pressure_ratio": queue_depth / self.config.max_queue_depth
        }
    
    def get_metrics(self, queue_depth: int) -> dict:
        """Get current backpressure metrics without applying delay.
        
        Args:
            queue_depth: Current queue depth
            
        Returns:
            Metrics dictionary
        """
        return {
            "queue_depth": queue_depth,
            "max_queue_depth": self.config.max_queue_depth,
            "pressure_ratio": queue_depth / self.config.max_queue_depth,
            "throttled": self.should_throttle(queue_depth),
            "recommended_batch_size": self.get_batch_size(queue_depth),
            "recommended_delay": self.get_delay(queue_depth)
        }
