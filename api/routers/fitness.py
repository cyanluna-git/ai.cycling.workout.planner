"""Fitness router - CTL/ATL/TSB and wellness data."""

from fastapi import APIRouter, HTTPException
from datetime import date, timedelta

from ..schemas import (
    FitnessResponse,
    TrainingMetrics,
    WellnessMetrics,
    ActivitiesResponse,
    Activity,
)

import sys

sys.path.insert(0, str(__file__).replace("/api/routers/fitness.py", ""))

from src.config import load_config
from src.clients.intervals import IntervalsClient, IntervalsAPIError
from src.services.data_processor import DataProcessor

router = APIRouter()


def get_intervals_client():
    """Get configured Intervals.icu client."""
    config = load_config()
    return IntervalsClient(config.intervals)


@router.get("/fitness", response_model=FitnessResponse)
async def get_fitness():
    """Get current training and wellness metrics."""
    try:
        client = get_intervals_client()
        processor = DataProcessor()

        # Fetch data
        activities = client.get_recent_activities(days=42)
        wellness_data = client.get_recent_wellness(days=7)

        # Calculate metrics
        training = processor.calculate_training_metrics(activities)
        wellness = processor.analyze_wellness(wellness_data)

        return FitnessResponse(
            training=TrainingMetrics(
                ctl=training.ctl,
                atl=training.atl,
                tsb=training.tsb,
                form_status=training.form_status,
            ),
            wellness=WellnessMetrics(
                readiness=wellness.readiness,
                hrv=wellness.hrv,
                rhr=wellness.rhr,
                sleep_hours=wellness.sleep_hours,
            ),
        )
    except IntervalsAPIError as e:
        raise HTTPException(status_code=502, detail=f"Intervals.icu API error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activities", response_model=ActivitiesResponse)
async def get_activities(days: int = 30):
    """Get recent activities."""
    try:
        client = get_intervals_client()
        activities = client.get_recent_activities(days=days)

        result = []
        for a in activities:
            # Skip empty activities
            name = a.get("name") or a.get("type") or ""
            if not name:
                continue

            duration = a.get("moving_time", 0)
            result.append(
                Activity(
                    id=str(a.get("id", "")),
                    date=str(a.get("start_date_local", ""))[:10],
                    name=name,
                    type=a.get("type", "Ride"),
                    duration_minutes=duration // 60 if duration else None,
                    tss=a.get("icu_training_load"),
                    distance_km=(
                        round(a.get("distance", 0) / 1000, 1)
                        if a.get("distance")
                        else None
                    ),
                )
            )

        return ActivitiesResponse(activities=result, total=len(result))
    except IntervalsAPIError as e:
        raise HTTPException(status_code=502, detail=f"Intervals.icu API error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
