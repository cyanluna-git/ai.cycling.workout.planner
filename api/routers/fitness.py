"""Fitness router - CTL/ATL/TSB and wellness data."""

from fastapi import APIRouter, HTTPException, Depends
from datetime import date, timedelta

from ..schemas import (
    FitnessResponse,
    TrainingMetrics,
    TrainingHistoryPoint,
    WellnessMetrics,
    AthleteProfile,
    ActivitiesResponse,
    Activity,
    WeeklyCalendarResponse,
    WeeklyEvent,
    SportSettings,
    PowerZone,
    HRZone,
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
    # Use granular cache key for complete fitness data
    cache_key = "fitness:complete"

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
        ctl_history_raw = processor.calculate_ctl_history(activities, days=7)
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

        # Get eFTP and VO2max from mmp_model if available
        mmp_model = ride_settings.get("mmp_model", {}) or {}
        eftp = mmp_model.get("ftp") if mmp_model else None
        vo2max_estimate = mmp_model.get("vo2max") if mmp_model else None

        # Calculate W/kg if both FTP and weight are available
        w_per_kg = round(ftp / weight, 2) if ftp and weight else None

        training_data = TrainingMetrics(
            ctl=training.ctl,
            atl=training.atl,
            tsb=training.tsb,
            form_status=training.form_status,
            ctl_history=[
                TrainingHistoryPoint(**point) for point in ctl_history_raw
            ],
        )

        wellness_data = WellnessMetrics(
            readiness=wellness.readiness,
            hrv=wellness.hrv,
            hrv_sdnn=wellness.hrv_sdnn,
            rhr=wellness.rhr,
            sleep_hours=wellness.sleep_hours,
            sleep_score=wellness.sleep_score,
            sleep_quality=wellness.sleep_quality,
            weight=wellness.weight,
            body_fat=wellness.body_fat,
            vo2max=wellness.vo2max or vo2max_estimate,  # Fallback to mmp_model
            soreness=wellness.soreness,
            fatigue=wellness.fatigue,
            stress=wellness.stress,
            mood=wellness.mood,
            motivation=wellness.motivation,
            spo2=wellness.spo2,
            systolic=wellness.systolic,
            diastolic=wellness.diastolic,
            respiration=wellness.respiration,
            readiness_score=wellness.readiness_score,
        )

        profile_data = AthleteProfile(
            ftp=ftp,
            max_hr=max_hr,
            lthr=lthr,
            weight=weight,
            w_per_kg=w_per_kg,
            vo2max=vo2max_estimate,
        )

        response = FitnessResponse(
            training=training_data,
            wellness=wellness_data,
            profile=profile_data,
        )

        # Cache the complete response
        set_cached(user_id, cache_key, response)

        # Also cache individual components with their own TTLs
        set_cached(user_id, "fitness:training", training_data)
        set_cached(user_id, "fitness:wellness", wellness_data)
        set_cached(user_id, "fitness:profile", profile_data)

        return response
    except UserApiServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IntervalsAPIError as e:
        raise HTTPException(status_code=502, detail=f"Intervals.icu API error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sport-settings", response_model=SportSettings)
async def get_sport_settings(
    sport: str = "Ride",
    refresh: bool = False,
    user: dict = Depends(get_current_user),
):
    """Get sport-specific settings (FTP, power zones, HR zones) from Intervals.icu.

    Args:
        sport: Sport type to get settings for (default: 'Ride').
        refresh: If True, bypass cache and fetch fresh data.
    """
    user_id = user["id"]
    cache_key = f"sport_settings:{sport}"

    # Check cache first (unless refresh is requested)
    if not refresh:
        cached = get_cached(user_id, cache_key)
        if cached:
            return cached

    try:
        client = await get_user_intervals_client(user_id)
        athlete_data = client.get_athlete_profile()

        # Find sport settings for requested sport
        sport_settings = athlete_data.get("sportSettings", [])
        ride_settings = next(
            (s for s in sport_settings if sport in s.get("types", [])),
            sport_settings[0] if sport_settings else {},
        )

        # Extract FTP and related
        ftp = ride_settings.get("ftp")
        mmp_model = ride_settings.get("mmp_model", {}) or {}
        eftp = mmp_model.get("ftp") if mmp_model else None
        ftp_source = "mmp_model" if eftp else "manual"

        # HR settings
        max_hr = ride_settings.get("max_hr")
        lthr = ride_settings.get("lthr")
        resting_hr = ride_settings.get("resting_hr")

        # Extract power zones
        power_zones_raw = ride_settings.get("power_zones", []) or []
        power_zones = []
        for i, z in enumerate(power_zones_raw):
            if isinstance(z, dict):
                power_zones.append(
                    PowerZone(
                        id=i + 1,
                        name=z.get("name", f"Z{i+1}"),
                        min_watts=z.get("min"),
                        max_watts=z.get("max"),
                    )
                )
            elif isinstance(z, list) and len(z) >= 2:
                zone_names = [
                    "Recovery",
                    "Endurance",
                    "Tempo",
                    "Threshold",
                    "VO2max",
                    "Anaerobic",
                    "Neuromuscular",
                ]
                power_zones.append(
                    PowerZone(
                        id=i + 1,
                        name=zone_names[i] if i < len(zone_names) else f"Z{i+1}",
                        min_watts=int(z[0]) if z[0] else None,
                        max_watts=int(z[1]) if len(z) > 1 and z[1] else None,
                    )
                )

        # Extract HR zones
        hr_zones_raw = ride_settings.get("hr_zones", []) or []
        hr_zones = []
        for i, z in enumerate(hr_zones_raw):
            if isinstance(z, dict):
                hr_zones.append(
                    HRZone(
                        id=i + 1,
                        name=z.get("name", f"Z{i+1}"),
                        min_bpm=z.get("min"),
                        max_bpm=z.get("max"),
                    )
                )
            elif isinstance(z, list) and len(z) >= 2:
                hr_zone_names = [
                    "Recovery",
                    "Endurance",
                    "Tempo",
                    "Threshold",
                    "VO2max",
                ]
                hr_zones.append(
                    HRZone(
                        id=i + 1,
                        name=hr_zone_names[i] if i < len(hr_zone_names) else f"Z{i+1}",
                        min_bpm=int(z[0]) if z[0] else None,
                        max_bpm=int(z[1]) if len(z) > 1 and z[1] else None,
                    )
                )

        # Calculate W/kg
        weight = athlete_data.get("icu_weight")
        w_per_kg = round(ftp / weight, 2) if ftp and weight else None

        response = SportSettings(
            ftp=ftp,
            eftp=eftp,
            ftp_source=ftp_source,
            max_hr=max_hr,
            lthr=lthr,
            resting_hr=resting_hr,
            power_zones=power_zones,
            hr_zones=hr_zones,
            weight=weight,
            w_per_kg=w_per_kg,
            pace_threshold=ride_settings.get("threshold_pace"),
            sport_types=ride_settings.get("types", []),
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

        # Fetch events (Planned) AND activities (Actual)
        events_data = client.get_events(oldest=week_start, newest=week_end)
        activities_data = client.get_recent_activities(
            days=60
        )  # Fetch ample history then filter

        # Filter activities for this week
        week_activities = []
        for a in activities_data:
            a_date = a.get("start_date_local", "")[:10]
            if week_start.isoformat() <= a_date <= week_end.isoformat():
                week_activities.append(a)

        combined_events = []
        planned_tss = 0
        actual_tss = 0

        # Process Planned Events
        for e in events_data:
            category = e.get("category", "")
            if category != "WORKOUT":
                continue

            tss = e.get("icu_training_load") or 0
            # Only add to planned TSS if not completed?
            # Or just sum all planned. Usually "Planned TSS" includes everything on the plan.
            planned_tss += tss

            # Parse date
            start_date = e.get("start_date_local", "")[:10]

            # Get duration
            moving_time = e.get("moving_time")
            duration_minutes = moving_time // 60 if moving_time else None

            combined_events.append(
                WeeklyEvent(
                    id=str(e.get("id")),
                    date=start_date,
                    name=e.get("name", "Workout"),
                    category="WORKOUT",
                    workout_type=e.get("type"),
                    duration_minutes=duration_minutes,
                    tss=tss,
                    description=e.get("description"),
                    is_actual=False,
                    is_indoor=False,  # Planned doesn't usually specify indoor unless in name
                )
            )

            # Sync to local DB (only planned workouts that might have definitions)
            from ..services.user_api_service import sync_workout_from_intervals

            # Await sync to ensure data is available for detailed view
            await sync_workout_from_intervals(user_id, e)

        # Cleanup stale workouts that no longer exist in Intervals.icu
        from ..services.user_api_service import cleanup_stale_workouts

        valid_event_ids = [
            e.get("id") for e in events_data if e.get("category") == "WORKOUT"
        ]
        await cleanup_stale_workouts(
            user_id,
            week_start.isoformat(),
            week_end.isoformat(),
            valid_event_ids,
        )

        # Process Actual Activities
        for a in week_activities:
            tss = a.get("icu_training_load") or 0
            actual_tss += tss

            start_date = a.get("start_date_local", "")[:10]
            moving_time = a.get("moving_time")
            duration_minutes = moving_time // 60 if moving_time else None

            # Check if indoor
            # Intervals often puts " VirtualRide" or similar in type, or `trainer` flag
            is_indoor = a.get("trainer") is True or "Virtual" in a.get("type", "")

            combined_events.append(
                WeeklyEvent(
                    id=f"act_{a.get('id')}",  # Prefix to distinguish
                    date=start_date,
                    name=a.get("name", "Activity"),
                    category="ACTIVITY",
                    workout_type=a.get("type"),
                    duration_minutes=duration_minutes,
                    tss=tss,
                    description=None,  # Activities don't have descriptions in the same way
                    is_actual=True,
                    is_indoor=is_indoor,
                )
            )

        response = WeeklyCalendarResponse(
            week_start=week_start.isoformat(),
            week_end=week_end.isoformat(),
            events=combined_events,
            planned_tss=int(planned_tss),
            actual_tss=int(actual_tss),
        )

        # Cache the response
        set_cached(user_id, cache_key, response)

        return response
    except UserApiServiceError as e:
        raise HTTPException(status_code=502, detail=f"Intervals.icu API error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
