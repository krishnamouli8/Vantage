"""
Adaptive Metric Downsampling Engine

Intelligently downsample metrics based on importance to reduce storage costs
while preserving critical debugging data.
"""

import math
import time
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import sqlite3

logger = logging.getLogger(__name__)


@dataclass
class MetricSample:
    """Represents a single metric sample"""
    timestamp: int
    service_name: str
    metric_name: str
    metric_type: str
    value: float
    status_code: Optional[int] = None
    endpoint: Optional[str] = None


@dataclass
class Stats:
    """Statistical summary of metrics"""
    count: int
    mean: float
    median: float
    p50: float
    p95: float
    p99: float
    min: float
    max: float
    std: float


class MetricImportanceCalculator:
    """
    Calculate metric importance based on:
    1. Variance (high variance = important)
    2. Error rate (high errors = important)
    3. Access frequency (often queried = important)
    """

    def __init__(self, db_path: str):
        self.db_path = db_path

    def calculate_importance_score(self, metrics: List[MetricSample]) -> float:
        """
        Score from 0-100:
        - 80-100: Critical (keep all data points)
        - 50-80: Important (1-min avg after 24h)
        - 20-50: Normal (5-min avg after 7d)
        - 0-20: Low (1-hour avg after 30d)
        """
        if not metrics:
            return 50.0

        try:
            variance_score = self._calculate_variance(metrics)
            error_score = self._calculate_error_rate(metrics)
            access_score = self._get_access_frequency(
                metrics[0].service_name, metrics[0].metric_name
            )

            # Weighted average
            importance = variance_score * 0.4 + error_score * 0.4 + access_score * 0.2
            return min(100.0, max(0.0, importance))

        except Exception as e:
            logger.error(f"Error calculating importance score: {e}")
            return 50.0  # Default to medium importance on error

    def _calculate_variance(self, metrics: List[MetricSample]) -> float:
        """High variance = interesting behavior"""
        try:
            values = [m.value for m in metrics if m.value is not None]
            if len(values) < 2:
                return 50.0

            mean = sum(values) / len(values)
            if mean == 0:
                return 50.0

            variance = sum((x - mean) ** 2 for x in values) / len(values)

            # Normalize to 0-100 using sigmoid
            normalized = 100 / (1 + math.exp(-variance / abs(mean)))
            return normalized

        except Exception as e:
            logger.error(f"Error calculating variance: {e}")
            return 50.0

    def _calculate_error_rate(self, metrics: List[MetricSample]) -> float:
        """High error rate = critical to keep"""
        try:
            total = len(metrics)
            if total == 0:
                return 0.0

            errors = sum(
                1 for m in metrics if m.status_code and m.status_code >= 500
            )

            error_rate = errors / total
            # Scale: 50% errors = max score (100)
            return min(error_rate * 200, 100.0)

        except Exception as e:
            logger.error(f"Error calculating error rate: {e}")
            return 0.0

    def _get_access_frequency(self, service_name: str, metric_name: str) -> float:
        """Get how often this metric is queried (0-100)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check query log for access patterns in last 7 days
            week_ago = int(time.time() * 1000) - (7 * 24 * 60 * 60 * 1000)

            cursor.execute(
                """
                SELECT COUNT(*) FROM query_log
                WHERE service_name = ? AND metric_name = ?
                AND timestamp > ?
                """,
                (service_name, metric_name, week_ago),
            )

            count = cursor.fetchone()[0]
            conn.close()

            # Normalize: 10+ queries in a week = high importance (100)
            return min(count * 10, 100.0)

        except Exception as e:
            logger.warning(f"Could not get access frequency: {e}")
            return 20.0  # Default to low access


class DownsamplingEngine:
    """
    Downsample metrics based on age and importance
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.calculator = MetricImportanceCalculator(db_path)

        # (age_days, importance_threshold, resolution_minutes)
        self.rules = [
            (1, 0, 0),  # < 1 day: keep all
            (7, 80, 1),  # < 7 days, critical: keep all (but marked)
            (7, 50, 5),  # < 7 days, important: 5-min avg
            (7, 0, 15),  # < 7 days, normal: 15-min avg
            (30, 80, 5),  # < 30 days, critical: 5-min avg
            (30, 50, 60),  # < 30 days, important: 1-hour avg
            (30, 0, 360),  # < 30 days, normal: 6-hour avg
            (90, 0, 1440),  # < 90 days: daily avg
        ]

    async def downsample_old_metrics(self) -> Dict[str, int]:
        """
        Run periodically (e.g., every 6 hours) to downsample old metrics
        Returns stats about downsampling
        """
        stats = {
            "metrics_processed": 0,
            "metrics_downsampled": 0,
            "storage_saved_bytes": 0,
        }

        try:
            now = int(time.time() * 1000)

            for age_days, min_importance, resolution_min in self.rules:
                if resolution_min == 0:
                    continue  # Skip "keep all" rule

                start_time = now - (age_days * 86400 * 1000)
                end_time = now - ((age_days - 1) * 86400 * 1000) if age_days > 1 else now

                # Get metrics in this time window
                metrics = self._get_metrics_in_range(start_time, end_time)
                stats["metrics_processed"] += len(metrics)

                # Group by service and metric name
                grouped = self._group_by_service_metric(metrics)

                for (service_name, metric_name), service_metrics in grouped.items():
                    # Calculate importance
                    importance = self.calculator.calculate_importance_score(
                        service_metrics
                    )

                    if importance < min_importance:
                        # Downsample these metrics
                        downsampled = self._aggregate_metrics(
                            service_metrics, resolution_min
                        )

                        # Replace original metrics with aggregated ones
                        removed = self._replace_metrics(service_metrics, downsampled)

                        stats["metrics_downsampled"] += removed
                        stats["storage_saved_bytes"] += removed * 200  # Avg metric size

                        logger.info(
                            f"Downsampled {removed} metrics to {len(downsampled)} "
                            f"for {service_name}.{metric_name} "
                            f"(importance: {importance:.1f}, resolution: {resolution_min}min)"
                        )

            return stats

        except Exception as e:
            logger.error(f"Error during downsampling: {e}")
            return stats

    def _get_metrics_in_range(
        self, start_time: int, end_time: int
    ) -> List[MetricSample]:
        """Get all metrics in time range"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT timestamp, service_name, metric_name, metric_type, 
                       value, status_code, endpoint
                FROM metrics
                WHERE timestamp >= ? AND timestamp < ?
                AND aggregated = 0
                ORDER BY service_name, metric_name, timestamp
                """,
                (start_time, end_time),
            )

            metrics = []
            for row in cursor.fetchall():
                metrics.append(
                    MetricSample(
                        timestamp=row[0],
                        service_name=row[1],
                        metric_name=row[2],
                        metric_type=row[3],
                        value=row[4],
                        status_code=row[5],
                        endpoint=row[6],
                    )
                )

            conn.close()
            return metrics

        except Exception as e:
            logger.error(f"Error fetching metrics: {e}")
            return []

    def _group_by_service_metric(
        self, metrics: List[MetricSample]
    ) -> Dict[Tuple[str, str], List[MetricSample]]:
        """Group metrics by (service_name, metric_name)"""
        grouped = {}
        for metric in metrics:
            key = (metric.service_name, metric.metric_name)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(metric)
        return grouped

    def _aggregate_metrics(
        self, metrics: List[MetricSample], resolution_minutes: int
    ) -> List[Dict]:
        """
        Aggregate metrics into time buckets
        Keep: min, max, avg, p50, p95, p99, count
        """
        try:
            window_ms = resolution_minutes * 60 * 1000
            buckets = {}

            for metric in metrics:
                bucket_key = (metric.timestamp // window_ms) * window_ms
                if bucket_key not in buckets:
                    buckets[bucket_key] = []
                buckets[bucket_key].append(metric)

            aggregated = []
            for timestamp, bucket_metrics in buckets.items():
                values = sorted([m.value for m in bucket_metrics if m.value is not None])

                if not values:
                    continue

                # Calculate percentiles
                count = len(values)
                p50_idx = count // 2
                p95_idx = int(count * 0.95)
                p99_idx = int(count * 0.99)

                # Count errors
                error_count = sum(
                    1 for m in bucket_metrics if m.status_code and m.status_code >= 500
                )

                agg_metric = {
                    "timestamp": timestamp,
                    "service_name": bucket_metrics[0].service_name,
                    "metric_name": bucket_metrics[0].metric_name,
                    "metric_type": "aggregated",
                    "value": sum(values) / len(values),  # avg
                    "min": min(values),
                    "max": max(values),
                    "p50": values[p50_idx],
                    "p95": values[p95_idx],
                    "p99": values[p99_idx],
                    "count": count,
                    "error_count": error_count,
                    "resolution_minutes": resolution_minutes,
                }

                aggregated.append(agg_metric)

            return aggregated

        except Exception as e:
            logger.error(f"Error aggregating metrics: {e}")
            return []

    def _replace_metrics(
        self, original_metrics: List[MetricSample], aggregated_metrics: List[Dict]
    ) -> int:
        """Replace original metrics with aggregated ones"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get IDs of original metrics to delete
            if not original_metrics:
                conn.close()
                return 0

            timestamps = [m.timestamp for m in original_metrics]
            service_name = original_metrics[0].service_name
            metric_name = original_metrics[0].metric_name

            # Delete original metrics
            placeholders = ",".join("?" * len(timestamps))
            cursor.execute(
                f"""
                DELETE FROM metrics
                WHERE service_name = ? AND metric_name = ?
                AND timestamp IN ({placeholders})
                """,
                [service_name, metric_name] + timestamps,
            )

            deleted_count = cursor.rowcount

            # Insert aggregated metrics
            for agg in aggregated_metrics:
                cursor.execute(
                    """
                    INSERT INTO metrics (
                        timestamp, service_name, metric_name, metric_type, value,
                        aggregated, resolution_minutes, min_value, max_value,
                        p50, p95, p99, sample_count, error_count
                    ) VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        agg["timestamp"],
                        agg["service_name"],
                        agg["metric_name"],
                        agg["metric_type"],
                        agg["value"],
                        agg["resolution_minutes"],
                        agg["min"],
                        agg["max"],
                        agg["p50"],
                        agg["p95"],
                        agg["p99"],
                        agg["count"],
                        agg["error_count"],
                    ),
                )

            conn.commit()
            conn.close()

            return deleted_count

        except Exception as e:
            logger.error(f"Error replacing metrics: {e}")
            return 0
