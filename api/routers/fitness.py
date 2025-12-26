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
    WeeklyCalendarResponse,
    WeeklyEvent,
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
from ..services.cache_service import (
    get_cached,
    set_cached,
    CACHE_KEYS,
)

router = APIRouter()


@router.get("/fitness", response_model=FitnessResponse)
async def get_fitness(
    refresh: bool = False,
    user: dict = Depends(get_current_user),
):
    """Get current training and wellness metrics with user-specific API keys.

    Args:
        refresh: If True, bypass cache and fetch fresh data.
    """
    user_id = user["id"]
    cache_key = CACHE_KEYS["fitness"]

    # Check cache first (unless refresh is requested)
    if not refresh:
        cached = get_cached(user_id, cache_key)
        if cached:
            return cached

    try:
        client = await get_user_intervals_client(user_id)
        processor = DataProcessor()

        # Fetch data
        activities = client.get_recent_activities(days=42)
        wellness_data = client.get_recent_wellness(days=7)
        athlete_data = client.get_athlete_profile()

        # Calculate metrics
        training = processor.calculate_training_metrics(activities)
        wellness = processor.analyze_wellness(wellness_data)

        # Extract profile data from nested structure
        # sportSettings[0] is typically "Ride" settings
        sport_settings = athlete_data.get("sportSettings", [])
        ride_settings = next(
            (s for s in sport_settings if "Ride" in s.get("types", [])),
            sport_settings[0] if sport_settings else {},
        )

        ftp = ride_settings.get("ftp")
        lthr = ride_settings.get("lthr")
        max_hr = ride_settings.get("max_hr")
        weight = athlete_data.get("icu_weight")  # weight is in icu_weight, not weight

        # Get eFTP from mmp_model if available
        mmp_model = ride_settings.get("mmp_model", {}) or {}
        eftp = mmp_model.get("ftp") if mmp_model else None

        # Calculate W/kg if both FTP and weight are available
        w_per_kg = round(ftp / weight, 2) if ftp and weight else None

        response = FitnessResponse(
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
                ftp=ftp,
                max_hr=max_hr,
                lthr=lthr,
                weight=weight,
                w_per_kg=w_per_kg,
            ),
        )

        # Cache the response
        set_cached(user_id, cache_key, response)

        return response
    except UserApiServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IntervalsAPIError as e:
        raise HTTPException(status_code=502, detail=f"Intervals.icu API error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activities", response_model=ActivitiesResponse)
async def get_activities(
    days: int = 30,
    refresh: bool = False,
    user: dict = Depends(get_current_user),
):
    """Get recent activities with user-specific API keys.

    Args:
        days: Number of days to look back.
        refresh: If True, bypass cache and fetch fresh data.
    """
    user_id = user["id"]
    cache_key = f"{CACHE_KEYS['activities']}:{days}"

    # Check cache first (unless refresh is requested)
    if not refresh:
        cached = get_cached(user_id, cache_key)
        if cached:
            return cached

    try:
        client = await get_user_intervals_client(user_id)
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

        response = ActivitiesResponse(activities=result, total=len(result))

        # Cache the response
        set_cached(user_id, cache_key, response)

        return response
    except UserApiServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IntervalsAPIError as e:
        raise HTTPException(status_code=502, detail=f"Intervals.icu API error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weekly-calendar", response_model=WeeklyCalendarResponse)
async def get_weekly_calendar(
    refresh: bool = False,
    user: dict = Depends(get_current_user),
):
    """Get this week's planned workouts from Intervals.icu.

    Args:
        refresh: If True, bypass cache and fetch fresh data.
    """
    user_id = user["id"]
    cache_key = CACHE_KEYS["calendar"]

    # Check cache first (unless refresh is requested)
    if not refresh:
        cached = get_cached(user_id, cache_key)
        if cached:
            return cached

    try:
        client = await get_user_intervals_client(user_id)

        # Get this week's date range (Monday to Sunday)
        today = date.today()
        week_start = today - timedelta(days=today.weekday())  # Monday
        week_end = week_start + timedelta(days=6)  # Sunday

        # Fetch events from Intervals.icu
        events_data = client.get_events(oldest=week_start, newest=week_end)

        events = []
        for e in events_data:
            # Only include WORKOUT category
            category = e.get("category", "")
            if category != "WORKOUT":
                continue

            # Parse date
            start_date = e.get("start_date_local", "")[:10]

            # Get duration in minutes
            moving_time = e.get("moving_time")
            duration_minutes = moving_time // 60 if moving_time else None

            events.append(
                WeeklyEvent(
                    id=e.get("id"),
                    date=start_date,
                    name=e.get("name", "Workout"),
                    category=category,
                    workout_type=e.get("type"),
                    duration_minutes=duration_minutes,
                    tss=e.get("icu_training_load"),
                    description=e.get("description"),
                )
            )

        response = WeeklyCalendarResponse(
            week_start=week_start.isoformat(),
            week_end=week_end.isoformat(),
            events=events,
        )

        # Cache the response
        set_cached(user_id, cache_key, response)

        return response
    except UserApiServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IntervalsAPIError as e:
        raise HTTPException(status_code=502, detail=f"Intervals.icu API error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
