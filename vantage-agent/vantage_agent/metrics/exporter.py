"""
Background metric exporter with exponential backoff.

Runs in a daemon thread and periodically flushes metrics to the collector API.
"""

import threading
import time
import json
from typing import Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from vantage_agent.config import AgentConfig
from vantage_agent.metrics.collector import MetricCollector
from vantage_agent.metrics.models import MetricBatch
from vantage_agent.utils.logger import get_logger

logger = get_logger(__name__)


class MetricExporter:
    """
    Background thread that exports metrics to the collector API.
    
    Runs as a daemon thread and flushes metrics at regular intervals.
    Uses exponential backoff for retries on failures.
    
    Example:
        >>> config = AgentConfig(service_name="my-service")
        >>> collector = MetricCollector(config)
        >>> exporter = MetricExporter(config, collector)
        >>> exporter.start()
        >>> # ... metrics are automatically exported ...
        >>> exporter.stop()
    """
    
    def __init__(self, config: AgentConfig, collector: MetricCollector):
        """
        Initialize the metric exporter.
        
        Args:
            config: Agent configuration
            collector: Metric collector instance
        """
        self.config = config
        self.collector = collector
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._session: Optional[requests.Session] = None
        
        # Statistics
        self._batches_sent = 0
        self._batches_failed = 0
        self._metrics_sent = 0
        
        logger.info(
            f"Initialized MetricExporter with flush_interval={config.flush_interval}s"
        )
    
    def _create_session(self) -> requests.Session:
        """
        Create a requests session with retry logic.
        
        Returns:
            Configured requests session
        """
        session = requests.Session()
        
        # Configure retries with exponential backoff
        retry_strategy = Retry(
            total=self.config.retry_attempts,
            backoff_factor=self.config.retry_backoff,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": f"vantage-agent/0.1.0",
        })
        
        return session
    
    def start(self) -> None:
        """Start the background exporter thread."""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("Exporter thread is already running")
            return
        
        self._stop_event.clear()
        self._session = self._create_session()
        
        self._thread = threading.Thread(
            target=self._run,
            name="VantageMetricExporter",
            daemon=True,
        )
        self._thread.start()
        
        logger.info("Started metric exporter thread")
    
    def stop(self, timeout: float = 10.0) -> None:
        """
        Stop the exporter thread and flush remaining metrics.
        
        Args:
            timeout: Maximum time to wait for thread to stop (seconds)
        """
        if self._thread is None or not self._thread.is_alive():
            logger.warning("Exporter thread is not running")
            return
        
        logger.info("Stopping metric exporter...")
        
        # Signal thread to stop
        self._stop_event.set()
        
        # Wait for thread to finish
        self._thread.join(timeout=timeout)
        
        if self._thread.is_alive():
            logger.warning("Exporter thread did not stop gracefully")
        else:
            logger.info("Metric exporter stopped")
        
        # Flush any remaining metrics
        self._flush_remaining_metrics()
        
        # Close session
        if self._session:
            self._session.close()
    
    def _run(self) -> None:
        """Main loop for the exporter thread."""
        logger.info("Metric exporter thread started")
        
        while not self._stop_event.is_set():
            try:
                # Wait for flush interval or stop event
                if self._stop_event.wait(timeout=self.config.flush_interval):
                    # Stop event was set
                    break
                
                # Flush metrics
                self._flush_metrics()
                
            except Exception as e:
                logger.error(f"Error in exporter thread: {e}", exc_info=True)
        
        logger.info("Metric exporter thread stopped")
    
    def _flush_metrics(self) -> None:
        """Flush metrics from the collector to the API."""
        # Get batch of metrics
        metrics = self.collector.get_batch()
        
        if not metrics:
            logger.debug("No metrics to flush")
            return
        
        # Create batch
        batch = MetricBatch(
            metrics=metrics,
            service_name=self.config.service_name,
            environment=self.config.environment or "development",
        )
        
        logger.debug(f"Flushing {len(batch)} metrics to collector")
        
        # Send to collector
        success = self._send_batch(batch)
        
        if success:
            self._batches_sent += 1
            self._metrics_sent += len(batch)
            logger.debug(f"Successfully sent {len(batch)} metrics")
        else:
            self._batches_failed += 1
            logger.warning(f"Failed to send {len(batch)} metrics")
    
    def _flush_remaining_metrics(self) -> None:
        """Flush all remaining metrics on shutdown."""
        logger.info("Flushing remaining metrics...")
        
        metrics = self.collector.get_all()
        
        if not metrics:
            logger.info("No remaining metrics to flush")
            return
        
        # Send in batches
        batch_size = self.config.batch_size
        for i in range(0, len(metrics), batch_size):
            batch_metrics = metrics[i:i + batch_size]
            
            batch = MetricBatch(
                metrics=batch_metrics,
                service_name=self.config.service_name,
                environment=self.config.environment or "development",
            )
            
            self._send_batch(batch)
        
        logger.info(f"Flushed {len(metrics)} remaining metrics")
    
    def _send_batch(self, batch: MetricBatch) -> bool:
        """
        Send a batch of metrics to the collector API.
        
        Args:
            batch: Batch of metrics to send
        
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self._session.post(
                self.config.collector_endpoint,
                json=batch.to_dict(),
                timeout=self.config.timeout,
            )
            
            response.raise_for_status()
            
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Failed to send metrics to collector: {e}",
                extra={
                    "collector_url": self.config.collector_endpoint,
                    "batch_size": len(batch),
                }
            )
            return False
        
        except Exception as e:
            logger.error(f"Unexpected error sending metrics: {e}", exc_info=True)
            return False
    
    def get_stats(self) -> dict:
        """
        Get exporter statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "batches_sent": self._batches_sent,
            "batches_failed": self._batches_failed,
            "metrics_sent": self._metrics_sent,
            "success_rate": (
                self._batches_sent / (self._batches_sent + self._batches_failed)
                if (self._batches_sent + self._batches_failed) > 0
                else 0.0
            ),
        }
