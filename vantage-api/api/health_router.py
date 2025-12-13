"""
Health Score API Router
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import List
from api.config import settings
from api.health_score import HealthScoreCalculator, HealthScore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


@router.get("/score/{service_name}")
async def get_health_score(
    service_name: str,
    time_window_seconds: int = Query(3600, description="Time window in seconds (default: 1 hour)")
) -> HealthScore:
    """
    Get health score for a service
    
    Returns a score from 0-100 based on:
    - Error rate (weight: 50%)
    - P95 latency (weight: 30%)
    - Traffic stability (weight: 20%)
    """
    try:
        calculator = HealthScoreCalculator(settings.database_path)
        score = calculator.calculate(service_name, time_window_seconds)
        return score
    except Exception as e:
        logger.error(f"Error calculating health score: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scores")
async def get_all_health_scores(
    time_window_seconds: int = Query(3600)
) -> List[HealthScore]:
    """Get health scores for all services"""
    try:
        import sqlite3
        
        # Get all unique services
        conn = sqlite3.connect(settings.database_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT service_name FROM metrics")
        services = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # Calculate scores
        calculator = HealthScoreCalculator(settings.database_path)
        scores = [
            calculator.calculate(service, time_window_seconds)
            for service in services
        ]
        
        # Sort by score (worst first)
        scores.sort(key=lambda x: x.overall_score)
        
        return scores
        
    except Exception as e:
        logger.error(f"Error calculating health scores: {e}")
        raise HTTPException(status_code=500, detail=str(e))
