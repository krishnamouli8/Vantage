"""
Health Score Algorithm

Calculates a health score (0-100) for each service based on:
- Error rate
- Latency (p95)
- Traffic volume changes
"""

import logging
import sqlite3
from typing import Dict, Any, Optional
from dataclasses import dataclass
import statistics

logger = logging.getLogger(__name__)


@dataclass
class HealthScore:
    """Service health score result"""
    
    service_name: str
    overall_score: int  # 0-100
    error_score: int  # 0-100
    latency_score: int  # 0-100
    traffic_score: int  # 0-100
    status: str  # "healthy", "degraded", "critical"
    details: Dict[str, Any]


class HealthScoreCalculator:
    """Calculate service health scores"""
    
    # Thresholds
    ERROR_RATE_GOOD = 0.01  # 1%
    ERROR_RATE_BAD = 0.05  # 5%
    
    LATENCY_GOOD_MS = 100
    LATENCY_BAD_MS = 500
    
    TRAFFIC_CHANGE_GOOD = 0.1  # 10%
    TRAFFIC_CHANGE_BAD = 0.5  # 50%
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def calculate(self, service_name: str, time_window_seconds: int = 3600) -> HealthScore:
        """
        Calculate health score for a service
        
        Args:
            service_name: Service to analyze
            time_window_seconds: Time window to analyze (default: 1 hour)
        """
        import time
        current_time = int(time.time() * 1000)
        start_time = current_time - (time_window_seconds * 1000)
        
        # Get metrics
        error_rate = self._calculate_error_rate(service_name, start_time, current_time)
        p95_latency = self._calculate_p95_latency(service_name, start_time, current_time)
        traffic_change = self._calculate_traffic_change(service_name, start_time, current_time)
        
        # Calculate individual scores
        error_score = self._score_error_rate(error_rate)
        latency_score = self._score_latency(p95_latency)
        traffic_score = self._score_traffic(traffic_change)
        
        # Overall score (weighted average)
        overall_score = int(
            0.5 * error_score +
            0.3 * latency_score +
            0.2 * traffic_score
        )
        
        # Determine status
        if overall_score >= 80:
            status = "healthy"
        elif overall_score >= 50:
            status = "degraded"
        else:
            status = "critical"
        
        details = {
            "error_rate": error_rate,
            "p95_latency_ms": p95_latency,
            "traffic_change_percent": traffic_change * 100,
            "time_window_seconds": time_window_seconds
        }
        
        return HealthScore(
            service_name=service_name,
            overall_score=overall_score,
            error_score=error_score,
            latency_score=latency_score,
            traffic_score=traffic_score,
            status=status,
            details=details
        )
    
    def _calculate_error_rate(self, service_name: str, start_time: int, end_time: int) -> float:
        """Calculate error rate (errors / total requests)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total requests
        cursor.execute("""
            SELECT COUNT(*)
            FROM metrics
            WHERE service_name = ?
              AND timestamp >= ?
              AND timestamp <= ?
              AND metric_name LIKE '%request%'
        """, (service_name, start_time, end_time))
        
        total = cursor.fetchone()[0]
        
        if total == 0:
            conn.close()
            return 0.0
        
        # Error requests (status code >= 400)
        cursor.execute("""
            SELECT COUNT(*)
            FROM metrics
            WHERE service_name = ?
              AND timestamp >= ?
              AND timestamp <= ?
              AND metric_name LIKE '%request%'
              AND status_code >= 400
        """, (service_name, start_time, end_time))
        
        errors = cursor.fetchone()[0]
        conn.close()
        
        return errors / total if total > 0 else 0.0
    
    def _calculate_p95_latency(self, service_name: str, start_time: int, end_time: int) -> Optional[float]:
        """Calculate p95 latency in milliseconds"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get duration values
        cursor.execute("""
            SELECT duration_ms
            FROM metrics
            WHERE service_name = ?
              AND timestamp >= ?
              AND timestamp <= ?
              AND duration_ms IS NOT NULL
            ORDER BY duration_ms
        """, (service_name, start_time, end_time))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return None
        
        values = [row[0] for row in rows]
        p95_index = int(len(values) * 0.95)
        
        return values[min(p95_index, len(values) - 1)]
    
    def _calculate_traffic_change(self, service_name: str, start_time: int, end_time: int) -> float:
        """
        Calculate traffic change compared to previous period
        Returns value between -1 and 1 (e.g., 0.5 = 50% increase)
        """
        period_duration = end_time - start_time
        previous_start = start_time - period_duration
        previous_end = start_time
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Current period traffic
        cursor.execute("""
            SELECT COUNT(*)
            FROM metrics
            WHERE service_name = ?
              AND timestamp >= ?
              AND timestamp <= ?
        """, (service_name, start_time, end_time))
        
        current_traffic = cursor.fetchone()[0]
        
        # Previous period traffic
        cursor.execute("""
            SELECT COUNT(*)
            FROM metrics
            WHERE service_name = ?
              AND timestamp >= ?
              AND timestamp <= ?
        """, (service_name, previous_start, previous_end))
        
        previous_traffic = cursor.fetchone()[0]
        conn.close()
        
        if previous_traffic == 0:
            return 0.0
        
        change = (current_traffic - previous_traffic) / previous_traffic
        return max(-1.0, min(1.0, change))  # Clamp to [-1, 1]
    
    def _score_error_rate(self, error_rate: float) -> int:
        """Score error rate (0-100, higher is better)"""
        if error_rate <= self.ERROR_RATE_GOOD:
            return 100
        elif error_rate >= self.ERROR_RATE_BAD:
            return 0
        else:
            # Linear interpolation
            ratio = (error_rate - self.ERROR_RATE_GOOD) / (self.ERROR_RATE_BAD - self.ERROR_RATE_GOOD)
            return int(100 * (1 - ratio))
    
    def _score_latency(self, latency: Optional[float]) -> int:
        """Score latency (0-100, higher is better)"""
        if latency is None:
            return 50  # Neutral if no data
        
        if latency <= self.LATENCY_GOOD_MS:
            return 100
        elif latency >= self.LATENCY_BAD_MS:
            return 0
        else:
            # Linear interpolation
            ratio = (latency - self.LATENCY_GOOD_MS) / (self.LATENCY_BAD_MS - self.LATENCY_GOOD_MS)
            return int(100 * (1 - ratio))
    
    def _score_traffic(self, traffic_change: float) -> int:
        """Score traffic stability (0-100, higher is better)"""
        # Prefer stable traffic, penalize large changes
        change_abs = abs(traffic_change)
        
        if change_abs <= self.TRAFFIC_CHANGE_GOOD:
            return 100
        elif change_abs >= self.TRAFFIC_CHANGE_BAD:
            return 50  # Large changes are concerning but not critical
        else:
            # Linear interpolation
            ratio = (change_abs - self.TRAFFIC_CHANGE_GOOD) / (self.TRAFFIC_CHANGE_BAD - self.TRAFFIC_CHANGE_GOOD)
            return int(100 - 50 * ratio)
