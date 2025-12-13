"""
Metric Comparison Engine for A/B Testing

Compares metrics between two time periods or service versions
with statistical significance testing.
"""

import logging
import sqlite3
import statistics
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import math

logger = logging.getLogger(__name__)


@dataclass
class ComparisonResult:
    """Result of comparing two metric datasets"""
    
    metric_name: str
    baseline_avg: float
    candidate_avg: float
    baseline_p95: Optional[float]
    candidate_p95: Optional[float]
    change_percent: float
    is_significant: bool
    verdict: str  # "better", "worse", "neutral"
    confidence: float


class MetricComparison:
    """Compare metrics for A/B testing"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def compare_services(
        self,
        baseline_service: str,
        candidate_service: str,
        metric_name: str,
        time_start: int,
        time_end: int
    ) -> ComparisonResult:
        """Compare metric between baseline and candidate services"""
        
        baseline_data = self._fetch_metric_data(
            baseline_service, metric_name, time_start, time_end
        )
        candidate_data = self._fetch_metric_data(
            candidate_service, metric_name, time_start, time_end
        )
        
        return self._analyze_comparison(
            metric_name, baseline_data, candidate_data
        )
    
    def compare_time_periods(
        self,
        service_name: str,
        metric_name: str,
        baseline_start: int,
        baseline_end: int,
        candidate_start: int,
        candidate_end: int
    ) -> ComparisonResult:
        """Compare metric across two time periods"""
        
        baseline_data = self._fetch_metric_data(
            service_name, metric_name, baseline_start, baseline_end
        )
        candidate_data = self._fetch_metric_data(
            service_name, metric_name, candidate_start, candidate_end
        )
        
        return self._analyze_comparison(
            metric_name, baseline_data, candidate_data
        )
    
    def _fetch_metric_data(
        self,
        service_name: str,
        metric_name: str,
        time_start: int,
        time_end: int
    ) -> List[float]:
        """Fetch metric values from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT value
            FROM metrics
            WHERE service_name = ?
              AND metric_name = ?
              AND timestamp >= ?
              AND timestamp <= ?
              AND value IS NOT NULL
            ORDER BY timestamp
        """, (service_name, metric_name, time_start, time_end))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [row[0] for row in rows]
    
    def _analyze_comparison(
        self,
        metric_name: str,
        baseline: List[float],
        candidate: List[float]
    ) -> ComparisonResult:
        """Analyze and compare two datasets"""
        
        if not baseline or not candidate:
            raise ValueError("Insufficient data for comparison")
        
        # Calculate statistics
        baseline_avg = statistics.mean(baseline)
        candidate_avg = statistics.mean(candidate)
        
        baseline_p95 = self._percentile(baseline, 95) if len(baseline) > 20 else None
        candidate_p95 = self._percentile(candidate, 95) if len(candidate) > 20 else None
        
        # Calculate change
        change_percent = ((candidate_avg - baseline_avg) / baseline_avg) * 100
        
        # Test statistical significance
        is_significant = self._is_significant(baseline, candidate)
        
        # Determine verdict
        verdict, confidence = self._determine_verdict(
            metric_name, change_percent, is_significant
        )
        
        return ComparisonResult(
            metric_name=metric_name,
            baseline_avg=baseline_avg,
            candidate_avg=candidate_avg,
            baseline_p95=baseline_p95,
            candidate_p95=candidate_p95,
            change_percent=change_percent,
            is_significant=is_significant,
            verdict=verdict,
            confidence=confidence
        )
    
    def _is_significant(self, baseline: List[float], candidate: List[float]) -> bool:
        """
        Simple t-test for statistical significance
        Returns True if difference is statistically significant (p < 0.05)
        """
        if len(baseline) < 10 or len(candidate) < 10:
            return False
        
        # Calculate means
        mean1 = statistics.mean(baseline)
        mean2 = statistics.mean(candidate)
        
        # Calculate standard deviations
        std1 = statistics.stdev(baseline) if len(baseline) > 1 else 0
        std2 = statistics.stdev(candidate) if len(candidate) > 1 else 0
        
        # Pooled standard error
        n1, n2 = len(baseline), len(candidate)
        se = math.sqrt((std1 ** 2 / n1) + (std2 ** 2 / n2))
        
        if se == 0:
            return False
        
        # T-statistic
        t_stat = abs(mean1 - mean2) / se
        
        # Simplified: t > 2 is roughly p < 0.05 for large samples
        return t_stat > 2.0
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _determine_verdict(
        self,
        metric_name: str,
        change_percent: float,
        is_significant: bool
    ) -> tuple:
        """
        Determine if change is better, worse, or neutral
        
        Returns: (verdict, confidence)
        """
        # For latency/duration metrics, lower is better
        is_latency_metric = any(x in metric_name.lower() for x in [
            'latency', 'duration', 'time', 'delay'
        ])
        
        # For error metrics, lower is better
        is_error_metric = 'error' in metric_name.lower()
        
        # Determine threshold
        threshold = 5.0  # 5% change threshold
        
        if not is_significant:
            return "neutral", 0.5
        
        if is_latency_metric or is_error_metric:
            # Lower is better
            if change_percent < -threshold:
                return "better", 0.9
            elif change_percent > threshold:
                return "worse", 0.9
            else:
                return "neutral", 0.7
        else:
            # Higher is better (e.g., throughput)
            if change_percent > threshold:
                return "better", 0.9
            elif change_percent < -threshold:
                return "worse", 0.9
            else:
                return "neutral", 0.7
