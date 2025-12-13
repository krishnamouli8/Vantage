"""
Smart Alerting with Adaptive Thresholds

Dynamic thresholds based on historical patterns using statistical methods.
Reduces alert fatigue by detecting real anomalies, not static threshold violations.
"""

import time
import uuid
import logging
import sqlite3
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Severity(str, Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert status"""

    FIRING = "firing"
    RESOLVED = "resolved"


@dataclass
class Alert:
    """Alert data structure"""

    alert_id: str
    service_name: str
    metric_name: str
    severity: Severity
    status: AlertStatus
    message: str
    current_value: float
    expected_min: float
    expected_max: float
    first_triggered: int
    last_triggered: int
    threshold_breach_count: int = 1
    resolved_at: Optional[int] = None


class AdaptiveThresholdCalculator:
    """
    Calculate dynamic thresholds using statistical methods
    No ML needed - just good statistics!
    """

    def __init__(self, sensitivity: str = "medium"):
        """
        Initialize calculator with sensitivity level
        
        Args:
            sensitivity: 'low', 'medium', 'high', 'very_high'
        """
        self.sensitivity_map = {
            "low": 3.0,  # Very few alerts (3 std dev)
            "medium": 2.5,  # Balanced (2.5 std dev)
            "high": 2.0,  # More sensitive (2 std dev)
            "very_high": 1.5,  # Very sensitive (1.5 std dev)
        }
        self.sigma = self.sensitivity_map.get(sensitivity, 2.5)

    def calculate_threshold(
        self, historical_data: List[float]
    ) -> Optional[Tuple[float, float]]:
        """
        Calculate upper/lower bounds using statistical methods
        
        Returns: (lower_bound, upper_bound) or None if insufficient data
        """
        try:
            if len(historical_data) < 10:
                return None

            # Remove outliers using IQR method
            cleaned_data = self._remove_outliers(historical_data)

            if len(cleaned_data) < 5:
                return None

            # Calculate statistics
            mean = np.mean(cleaned_data)
            std = np.std(cleaned_data)

            # Calculate bounds
            lower_bound = max(0, mean - (self.sigma * std))
            upper_bound = mean + (self.sigma * std)

            return (lower_bound, upper_bound)

        except Exception as e:
            logger.error(f"Error calculating threshold: {e}")
            return None

    def _remove_outliers(self, data: List[float]) -> List[float]:
        """Remove outliers using IQR method"""
        try:
            sorted_data = sorted(data)
            n = len(sorted_data)

            if n < 4:
                return sorted_data

            q1_idx = n // 4
            q3_idx = 3 * n // 4

            q1 = sorted_data[q1_idx]
            q3 = sorted_data[q3_idx]
            iqr = q3 - q1

            lower_fence = q1 - (1.5 * iqr)
            upper_fence = q3 + (1.5 * iqr)

            return [x for x in data if lower_fence <= x <= upper_fence]

        except Exception as e:
            logger.error(f"Error removing outliers: {e}")
            return data


class AlertEngine:
    """
    Evaluate metrics against adaptive thresholds and manage alerts
    """

    def __init__(self, db_path: str, sensitivity: str = "medium"):
        self.db_path = db_path
        self.calculator = AdaptiveThresholdCalculator(sensitivity)
        self.alert_cooldown_minutes = 5  # Don't re-alert for same issue within 5 min

    def evaluate_metrics(
        self, service_name: str, metric_name: str
    ) -> List[Alert]:
        """
        Check if metrics violate adaptive thresholds
        
        Returns: List of triggered alerts
        """
        triggered_alerts = []

        try:
            # Get recent metrics (last hour)
            recent_metrics = self._get_recent_metrics(service_name, metric_name, hours=1)

            if not recent_metrics:
                return []

            # Get historical baseline (last 7 days, same hour of day)
            historical = self._get_historical_baseline(
                service_name, metric_name, days=7
            )

            if not historical:
                logger.debug(
                    f"No historical data for {service_name}.{metric_name}, skipping"
                )
                return []

            # Calculate threshold
            threshold = self.calculator.calculate_threshold(historical)

            if not threshold:
                return []

            lower, upper = threshold

            # Check current value
            current_value = recent_metrics[-1] if recent_metrics else None

            if current_value is None:
                return []

            # Check if value is outside expected range
            if current_value < lower or current_value > upper:
                # Check if alert already exists
                existing_alert = self._get_active_alert(service_name, metric_name)

                if existing_alert:
                    # Update existing alert
                    self._update_alert(existing_alert, current_value)
                else:
                    # Create new alert
                    severity = self._calculate_severity(current_value, lower, upper)

                    alert = Alert(
                        alert_id=str(uuid.uuid4()),
                        service_name=service_name,
                        metric_name=metric_name,
                        severity=severity,
                        status=AlertStatus.FIRING,
                        current_value=current_value,
                        expected_min=lower,
                        expected_max=upper,
                        message=self._generate_message(
                            metric_name, current_value, lower, upper
                        ),
                        first_triggered=int(time.time() * 1000),
                        last_triggered=int(time.time() * 1000),
                    )

                    self._save_alert(alert)
                    triggered_alerts.append(alert)

                    logger.warning(
                        f"Alert triggered: {service_name}.{metric_name} = {current_value:.2f}, "
                        f"expected {lower:.2f}-{upper:.2f} ({severity})"
                    )
            else:
                # Value is within range, resolve any active alerts
                active_alert = self._get_active_alert(service_name, metric_name)
                if active_alert:
                    self._resolve_alert(active_alert)
                    logger.info(
                        f"Alert resolved: {service_name}.{metric_name} back to normal"
                    )

        except Exception as e:
            logger.error(f"Error evaluating metrics: {e}")

        return triggered_alerts

    def _calculate_severity(
        self, value: float, lower: float, upper: float
    ) -> Severity:
        """Calculate alert severity based on how far from threshold"""
        try:
            if value > upper:
                deviation = (value - upper) / upper if upper != 0 else 1.0
            else:
                deviation = (lower - value) / lower if lower != 0 else 1.0

            if deviation > 0.5:
                return Severity.CRITICAL
            elif deviation > 0.3:
                return Severity.WARNING
            else:
                return Severity.INFO

        except Exception as e:
            logger.error(f"Error calculating severity: {e}")
            return Severity.WARNING

    def _generate_message(
        self, metric_name: str, current: float, lower: float, upper: float
    ) -> str:
        """Generate human-readable alert message"""
        if current > upper:
            return (
                f"{metric_name} is abnormally high: {current:.2f} "
                f"(expected max: {upper:.2f})"
            )
        else:
            return (
                f"{metric_name} is abnormally low: {current:.2f} "
                f"(expected min: {lower:.2f})"
            )

    def _get_recent_metrics(
        self, service_name: str, metric_name: str, hours: int = 1
    ) -> List[float]:
        """Get recent metric values"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            start_time = int(time.time() * 1000) - (hours * 3600 * 1000)

            cursor.execute(
                """
                SELECT value FROM metrics
                WHERE service_name = ? AND metric_name = ?
                AND timestamp > ?
                AND aggregated = 0
                ORDER BY timestamp DESC
                """,
                (service_name, metric_name, start_time),
            )

            values = [row[0] for row in cursor.fetchall() if row[0] is not None]
            conn.close()

            return values

        except Exception as e:
            logger.error(f"Error fetching recent metrics: {e}")
            return []

    def _get_historical_baseline(
        self, service_name: str, metric_name: str, days: int = 7
    ) -> List[float]:
        """Get historical baseline for same hour of day"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get metrics from last N days, excluding the most recent day
            end_time = int(time.time() * 1000) - (24 * 3600 * 1000)
            start_time = end_time - (days * 24 * 3600 * 1000)

            cursor.execute(
                """
                SELECT value FROM metrics
                WHERE service_name = ? AND metric_name = ?
                AND timestamp >= ? AND timestamp < ?
                AND aggregated = 0
                """,
                (service_name, metric_name, start_time, end_time),
            )

            values = [row[0] for row in cursor.fetchall() if row[0] is not None]
            conn.close()

            return values

        except Exception as e:
            logger.error(f"Error fetching historical baseline: {e}")
            return []

    def _get_active_alert(
        self, service_name: str, metric_name: str
    ) -> Optional[Alert]:
        """Get active alert for service/metric"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT alert_id, severity, status, message, current_value,
                       expected_min, expected_max, first_triggered, last_triggered,
                       threshold_breach_count
                FROM alerts
                WHERE service_name = ? AND metric_name = ?
                AND status = 'firing'
                ORDER BY last_triggered DESC
                LIMIT 1
                """,
                (service_name, metric_name),
            )

            row = cursor.fetchone()
            conn.close()

            if row:
                return Alert(
                    alert_id=row[0],
                    service_name=service_name,
                    metric_name=metric_name,
                    severity=Severity(row[1]),
                    status=AlertStatus(row[2]),
                    message=row[3],
                    current_value=row[4],
                    expected_min=row[5],
                    expected_max=row[6],
                    first_triggered=row[7],
                    last_triggered=row[8],
                    threshold_breach_count=row[9],
                )

            return None

        except Exception as e:
            logger.error(f"Error fetching active alert: {e}")
            return None

    def _save_alert(self, alert: Alert):
        """Save new alert to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO alerts (
                    alert_id, service_name, metric_name, severity, status,
                    message, current_value, expected_min, expected_max,
                    threshold_breach_count, first_triggered, last_triggered
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    alert.alert_id,
                    alert.service_name,
                    alert.metric_name,
                    alert.severity.value,
                    alert.status.value,
                    alert.message,
                    alert.current_value,
                    alert.expected_min,
                    alert.expected_max,
                    alert.threshold_breach_count,
                    alert.first_triggered,
                    alert.last_triggered,
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error saving alert: {e}")

    def _update_alert(self, alert: Alert, current_value: float):
        """Update existing alert"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE alerts
                SET current_value = ?,
                    last_triggered = ?,
                    threshold_breach_count = threshold_breach_count + 1
                WHERE alert_id = ?
                """,
                (current_value, int(time.time() * 1000), alert.alert_id),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error updating alert: {e}")

    def _resolve_alert(self, alert: Alert):
        """Resolve an active alert"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE alerts
                SET status = 'resolved',
                    resolved_at = ?
                WHERE alert_id = ?
                """,
                (int(time.time() * 1000), alert.alert_id),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
