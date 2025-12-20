"""Fitness router - CTL/ATL/TSB and wellness data."""

from fastapi import APIRouter, HTTPException, Depends
from datetime import date, timedelta

from ..schemas import (
    FitnessResponse,
    TrainingMetrics,
    WellnessMetrics,
    AthleteProfile,
    ActivitiesResponse,
    Activity,
)

import sys

sys.path.insert(0, str(__file__).replace("/api/routers/fitness.py", ""))

from src.clients.intervals import IntervalsAPIError
from src.services.data_processor import DataProcessor
from .auth import get_current_user
from ..services.user_api_service import (
    get_user_intervals_client,
    UserApiServiceError,
)

router = APIRouter()


@router.get("/fitness", response_model=FitnessResponse)
async def get_fitness(user: dict = Depends(get_current_user)):
    """Get current training and wellness metrics with user-specific API keys."""
    try:
        client = await get_user_intervals_client(user["id"])
        processor = DataProcessor()

        # Fetch data
        activities = client.get_recent_activities(days=42)
        wellness_data = client.get_recent_wellness(days=7)
        athlete_data = client.get_athlete_profile()

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
            profile=AthleteProfile(
                ftp=athlete_data.get("ftp"),
                max_hr=athlete_data.get("maxHr"),
                lthr=athlete_data.get("lthr"),
                weight=athlete_data.get("weight"),
            ),
        )
    except UserApiServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IntervalsAPIError as e:
        raise HTTPException(status_code=502, detail=f"Intervals.icu API error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activities", response_model=ActivitiesResponse)
async def get_activities(days: int = 30, user: dict = Depends(get_current_user)):
    """Get recent activities with user-specific API keys."""
    try:
        client = await get_user_intervals_client(user["id"])
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
    except UserApiServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IntervalsAPIError as e:
        raise HTTPException(status_code=502, detail=f"Intervals.icu API error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
