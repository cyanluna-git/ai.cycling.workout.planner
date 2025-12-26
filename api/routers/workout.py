"""Workout router - generate and create workouts."""

from fastapi import APIRouter, HTTPException, Depends
from datetime import date

from ..schemas import (
    WorkoutGenerateRequest,
    WorkoutGenerateResponse,
    GeneratedWorkout,
    WorkoutCreateRequest,
    WorkoutCreateResponse,
)

import sys

sys.path.insert(0, str(__file__).replace("/api/routers/workout.py", ""))

from src.clients.intervals import IntervalsAPIError
from src.services.workout_generator import WorkoutGenerator
from .auth import get_current_user
from ..services.user_api_service import (
    get_user_intervals_client,
    get_server_llm_client,
    get_user_profile,
    get_data_processor,
    check_rate_limit,
    increment_usage,
    UserApiServiceError,
    RateLimitExceededError,
)
from ..services.cache_service import clear_user_cache

router = APIRouter()


@router.post("/workout/generate", response_model=WorkoutGenerateResponse)
async def generate_workout(
    request: WorkoutGenerateRequest, user: dict = Depends(get_current_user)
):
    """Generate a workout using AI with user-specific API keys."""
    try:
        # Check rate limit
        await check_rate_limit(user["id"])

        # Get user-specific clients
        intervals = await get_user_intervals_client(user["id"])
        llm = get_server_llm_client()
        user_profile = await get_user_profile(user["id"])
        processor = get_data_processor()

        # Parse target date
        if request.target_date:
            target_date = date.fromisoformat(request.target_date)
        else:
            target_date = date.today()

        # Get current metrics
        activities = intervals.get_recent_activities(days=42)
        wellness_data = intervals.get_recent_wellness(days=7)

        training_metrics = processor.calculate_training_metrics(activities)
        wellness_metrics = processor.analyze_wellness(wellness_data)

        # Generate workout
        generator = WorkoutGenerator(
            llm, user_profile, max_duration_minutes=request.duration
        )

        workout = generator.generate(
            training_metrics,
            wellness_metrics,
            target_date,
            style=request.style,
            notes=request.notes,
            intensity=request.intensity,
            indoor=request.indoor,
        )

        # Parse workout text to extract steps
        warmup, main, cooldown = _parse_workout_sections(workout.workout_text)

        # Increment usage count on success
        await increment_usage(user["id"])

        return WorkoutGenerateResponse(
            success=True,
            workout=GeneratedWorkout(
                name=workout.name,
                workout_type=workout.workout_type,
                estimated_tss=workout.estimated_tss,
                estimated_duration_minutes=workout.estimated_duration_minutes,
                workout_text=workout.workout_text,
                warmup=warmup,
                main=main,
                cooldown=cooldown,
            ),
        )
    except RateLimitExceededError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except UserApiServiceError as e:
        return WorkoutGenerateResponse(success=False, error=str(e))
    except Exception as e:
        return WorkoutGenerateResponse(success=False, error=str(e))


@router.post("/workout/create", response_model=WorkoutCreateResponse)
async def create_workout(
    request: WorkoutCreateRequest, user: dict = Depends(get_current_user)
):
    """Create workout on Intervals.icu with user-specific API keys."""
    try:
        # Get user-specific Intervals client
        intervals = await get_user_intervals_client(user["id"])

        target_date = date.fromisoformat(request.target_date)

        # Check for existing workout
        existing = intervals.check_workout_exists(target_date)

        if existing and not request.force:
            return WorkoutCreateResponse(
                success=False,
                error=f"Workout already exists: {existing.get('name')}. Use force=true to replace.",
            )

        # Delete existing if force
        if existing and request.force:
            intervals.delete_event(existing["id"])

        # Create new workout
        event = intervals.create_workout(
            name=request.name,
            description=request.workout_text,
            target_date=target_date,
            moving_time=request.duration_minutes * 60,  # Convert minutes to seconds
            training_load=request.estimated_tss,
        )

        # Clear cache for this user (calendar will have new workout)
        clear_user_cache(user["id"], keys=["calendar", "fitness"])

        return WorkoutCreateResponse(
            success=True,
            event_id=event.get("id"),
        )
    except UserApiServiceError as e:
        return WorkoutCreateResponse(success=False, error=str(e))
    except IntervalsAPIError as e:
        return WorkoutCreateResponse(success=False, error=f"Intervals.icu error: {e}")
    except Exception as e:
        return WorkoutCreateResponse(success=False, error=str(e))


def _parse_workout_sections(workout_text: str) -> tuple:
    """Parse workout text into sections."""
    warmup = []
    main = []
    cooldown = []

    current_section = None

    for line in workout_text.split("\n"):
        line = line.strip()

        if line.lower() == "warmup":
            current_section = "warmup"
        elif line.lower() == "main set":
            current_section = "main"
        elif line.lower() == "cooldown":
            current_section = "cooldown"
        elif line.startswith("- "):
            step = line[2:].strip()
            if current_section == "warmup":
                warmup.append(step)
            elif current_section == "main":
                main.append(step)
            elif current_section == "cooldown":
                cooldown.append(step)

    return warmup, main, cooldown
