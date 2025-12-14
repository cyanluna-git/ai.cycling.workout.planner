"""Workout router - generate and create workouts."""

from fastapi import APIRouter, HTTPException
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

from src.config import load_config
from src.clients.intervals import IntervalsClient, IntervalsAPIError
from src.clients.llm import LLMClient
from src.services.data_processor import DataProcessor
from src.services.workout_generator import WorkoutGenerator

router = APIRouter()


def get_components():
    """Get configured components."""
    config = load_config()
    intervals = IntervalsClient(config.intervals)
    llm = LLMClient.from_config(config.llm)
    processor = DataProcessor()
    return config, intervals, llm, processor


@router.post("/workout/generate", response_model=WorkoutGenerateResponse)
async def generate_workout(request: WorkoutGenerateRequest):
    """Generate a workout using AI."""
    try:
        config, intervals, llm, processor = get_components()

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
            llm, config.user_profile, max_duration_minutes=request.duration
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
    except Exception as e:
        return WorkoutGenerateResponse(success=False, error=str(e))


@router.post("/workout/create", response_model=WorkoutCreateResponse)
async def create_workout(request: WorkoutCreateRequest):
    """Create workout on Intervals.icu."""
    try:
        config, intervals, _, _ = get_components()

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
            duration_minutes=request.duration_minutes,
        )

        return WorkoutCreateResponse(
            success=True,
            event_id=event.get("id"),
        )
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
