"""
Periodic Tasks

Runs background jobs like downsampling and alert evaluation.
"""

import logging
import asyncio
from typing import List
from worker.config import settings
from worker.downsampling import DownsamplingEngine
from worker.alerting import AlertEngine

logger = logging.getLogger(__name__)


class PeriodicTasks:
    """Manages periodic background tasks"""

    def __init__(self):
        self.running = False
        self.downsampling_engine = DownsamplingEngine(settings.database_path)
        self.alert_engine = AlertEngine(settings.database_path, sensitivity="medium")
        self.tasks = []

    async def start(self):
        """Start all periodic tasks"""
        self.running = True
        logger.info("Starting periodic tasks")

        # Start downsampling task (every 6 hours)
        self.tasks.append(
            asyncio.create_task(self._run_periodically(self._run_downsampling, 6 * 3600))
        )

        # Start alert evaluation task (every 1 minute)
        self.tasks.append(
            asyncio.create_task(self._run_periodically(self._run_alert_evaluation, 60))
        )

    async def stop(self):
        """Stop all periodic tasks"""
        self.running = False
        logger.info("Stopping periodic tasks")

        for task in self.tasks:
            task.cancel()

        await asyncio.gather(*self.tasks, return_exceptions=True)

    async def _run_periodically(self, func, interval_seconds: int):
        """Run a function periodically"""
        while self.running:
            try:
                await func()
            except Exception as e:
                logger.error(f"Error in periodic task {func.__name__}: {e}")

            # Wait for interval or until stopped
            try:
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break

    async def _run_downsampling(self):
        """Run metric downsampling"""
        try:
            logger.info("Running metric downsampling...")
            stats = await self.downsampling_engine.downsample_old_metrics()

            logger.info(
                f"Downsampling complete: processed={stats['metrics_processed']}, "
                f"downsampled={stats['metrics_downsampled']}, "
                f"saved={stats['storage_saved_bytes']} bytes"
            )

        except Exception as e:
            logger.error(f"Error during downsampling: {e}")

    async def _run_alert_evaluation(self):
        """Evaluate metrics for alerts"""
        try:
            # Get list of unique service/metric combinations to check
            service_metrics = self._get_service_metrics_to_check()

            alerts_triggered = 0
            for service_name, metric_name in service_metrics:
                try:
                    alerts = self.alert_engine.evaluate_metrics(service_name, metric_name)
                    alerts_triggered += len(alerts)
                except Exception as e:
                    logger.error(
                        f"Error evaluating {service_name}.{metric_name}: {e}"
                    )

            if alerts_triggered > 0:
                logger.info(f"Alert evaluation complete: {alerts_triggered} alerts triggered")

        except Exception as e:
            logger.error(f"Error during alert evaluation: {e}")

    def _get_service_metrics_to_check(self) -> List[tuple]:
        """Get list of (service_name, metric_name) to evaluate"""
        try:
            import sqlite3

            conn = sqlite3.connect(settings.database_path)
            cursor = conn.cursor()

            # Get unique service/metric combinations from last hour
            import time

            one_hour_ago = int(time.time() * 1000) - (3600 * 1000)

            cursor.execute(
                """
                SELECT DISTINCT service_name, metric_name
                FROM metrics
                WHERE timestamp > ?
                AND aggregated = 0
                AND metric_type IN ('gauge', 'histogram', 'counter')
                LIMIT 100
                """,
                (one_hour_ago,),
            )

            result = cursor.fetchall()
            conn.close()

            return result

        except Exception as e:
            logger.error(f"Error getting service metrics: {e}")
            return []
