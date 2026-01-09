"""Weekly Plan API Router.

Endpoints for managing weekly workout plans and daily workouts.
"""

import os
import sys
import logging
from datetime import date, datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from src.clients.supabase_client import get_supabase_admin_client
from .auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


# --- Schemas ---


class DailyWorkoutResponse(BaseModel):
    """Single daily workout in a plan."""

    id: Optional[str] = None
    workout_date: str
    day_name: str
    planned_name: Optional[str] = None
    planned_type: Optional[str] = None
    planned_duration: Optional[int] = None
    planned_tss: Optional[int] = None
    planned_rationale: Optional[str] = None
    actual_name: Optional[str] = None
    actual_type: Optional[str] = None
    status: str = "planned"


class WeeklyPlanResponse(BaseModel):
    """Weekly plan with daily workouts."""

    id: str
    week_start: str
    week_end: str
    status: str
    training_style: Optional[str] = None
    total_planned_tss: Optional[int] = None
    daily_workouts: List[DailyWorkoutResponse]


class GenerateWeeklyPlanRequest(BaseModel):
    """Request to generate a weekly plan."""

    week_start: Optional[str] = None  # YYYY-MM-DD, default: next Monday


class TodayWorkoutResponse(BaseModel):
    """Today's workout info."""

    has_plan: bool
    workout: Optional[DailyWorkoutResponse] = None
    wellness_hint: Optional[str] = None
    can_regenerate: bool = True


class RegenerateRequest(BaseModel):
    """Request to regenerate today's workout."""

    reason: Optional[str] = None  # Optional reason for regeneration


# --- Helper Functions ---


def get_week_dates(target_date: Optional[date] = None) -> tuple:
    """Get Monday and Sunday of a week."""
    if target_date is None:
        target_date = date.today()

    # Get Monday (start of ISO week)
    days_since_monday = target_date.weekday()
    week_start = target_date - timedelta(days=days_since_monday)
    week_end = week_start + timedelta(days=6)

    return week_start, week_end


def get_next_week_dates() -> tuple:
    """Get next week's Monday and Sunday."""
    today = date.today()
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7  # Next Monday if today is Monday
    week_start = today + timedelta(days=days_until_monday)
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


# --- Endpoints ---


@router.get("/plans/weekly", response_model=Optional[WeeklyPlanResponse])
async def get_current_weekly_plan(user: dict = Depends(get_current_user)):
    """Get the current week's plan."""
    supabase = get_supabase_admin_client()
    week_start, week_end = get_week_dates()

    # Get weekly plan
    plan_result = (
        supabase.table("weekly_plans")
        .select("*")
        .eq("user_id", user["id"])
        .eq("week_start", week_start.isoformat())
        .maybe_single()
        .execute()
    )

    if not plan_result.data:
        return None

    plan = plan_result.data

    # Get daily workouts for this plan
    workouts_result = (
        supabase.table("daily_workouts")
        .select("*")
        .eq("plan_id", plan["id"])
        .order("workout_date")
        .execute()
    )

    day_names = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    daily_workouts = []

    for workout in workouts_result.data:
        workout_date = datetime.strptime(workout["workout_date"], "%Y-%m-%d").date()
        day_index = (workout_date - week_start).days

        daily_workouts.append(
            DailyWorkoutResponse(
                id=workout["id"],
                workout_date=workout["workout_date"],
                day_name=day_names[day_index] if 0 <= day_index < 7 else "Unknown",
                planned_name=workout.get("planned_name"),
                planned_type=workout.get("planned_type"),
                planned_duration=workout.get("planned_duration"),
                planned_tss=workout.get("planned_tss"),
                planned_rationale=workout.get("planned_rationale"),
                actual_name=workout.get("actual_name"),
                actual_type=workout.get("actual_type"),
                status=workout.get("status", "planned"),
            )
        )

    return WeeklyPlanResponse(
        id=plan["id"],
        week_start=plan["week_start"],
        week_end=plan["week_end"],
        status=plan["status"],
        training_style=plan.get("training_style"),
        total_planned_tss=plan.get("total_planned_tss"),
        daily_workouts=daily_workouts,
    )


@router.post("/plans/weekly/generate", response_model=WeeklyPlanResponse)
async def generate_weekly_plan(
    request: GenerateWeeklyPlanRequest, user: dict = Depends(get_current_user)
):
    """Generate a new weekly plan (or regenerate existing)."""
    supabase = get_supabase_admin_client()

    # Determine target week
    if request.week_start:
        week_start = datetime.strptime(request.week_start, "%Y-%m-%d").date()
    else:
        week_start, _ = get_next_week_dates()

    week_end = week_start + timedelta(days=6)

    # Get user settings
    settings_result = (
        supabase.table("user_settings")
        .select("*")
        .eq("user_id", user["id"])
        .maybe_single()
        .execute()
    )

    user_settings = settings_result.data or {}

    # Get current fitness metrics from Intervals.icu
    try:
        from ..services.user_api_service import UserApiService

        api_service = UserApiService(user["id"])
        fitness_data = api_service.get_fitness_data()

        ctl = fitness_data.get("training", {}).get("ctl", 50.0)
        atl = fitness_data.get("training", {}).get("atl", 50.0)
        tsb = fitness_data.get("training", {}).get("tsb", 0.0)
        form_status = fitness_data.get("training", {}).get("form_status", "Neutral")
    except Exception as e:
        logger.warning(f"Failed to get fitness data, using defaults: {e}")
        ctl, atl, tsb = 50.0, 50.0, 0.0
        form_status = "Neutral"

    # Generate plan with AI
    from .weekly_plan_service import WeeklyPlanGenerator
    from src.clients.llm import LLMClient
    from src.config import load_config

    config = load_config()
    llm_client = LLMClient.from_config(config.llm)

    generator = WeeklyPlanGenerator(llm_client, user_settings)
    weekly_plan = generator.generate_weekly_plan(
        ctl=ctl,
        atl=atl,
        tsb=tsb,
        form_status=form_status,
        week_start=week_start,
        exclude_barcode=user_settings.get("exclude_barcode_workouts", False),
    )

    # Delete existing plan for this week if any
    supabase.table("weekly_plans").delete().eq("user_id", user["id"]).eq(
        "week_start", week_start.isoformat()
    ).execute()

    # Save weekly plan to DB
    plan_result = (
        supabase.table("weekly_plans")
        .insert(
            {
                "user_id": user["id"],
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "status": "active",
                "training_style": weekly_plan.training_style,
                "total_planned_tss": weekly_plan.total_planned_tss,
            }
        )
        .execute()
    )

    plan_id = plan_result.data[0]["id"]

    # Save daily workouts
    daily_workouts_data = []
    for dp in weekly_plan.daily_plans:
        daily_workouts_data.append(
            {
                "plan_id": plan_id,
                "user_id": user["id"],
                "workout_date": dp.workout_date.isoformat(),
                "planned_name": dp.workout_name,
                "planned_type": dp.workout_type,
                "planned_duration": dp.duration_minutes,
                "planned_tss": dp.estimated_tss,
                "planned_modules": dp.selected_modules,
                "planned_rationale": dp.rationale,
                "status": "planned",
            }
        )

    supabase.table("daily_workouts").insert(daily_workouts_data).execute()

    logger.info(f"Generated weekly plan {plan_id} for user {user['id']}")

    # Return the created plan
    return await get_current_weekly_plan(user)


@router.get("/plans/today", response_model=TodayWorkoutResponse)
async def get_today_workout(user: dict = Depends(get_current_user)):
    """Get today's planned workout."""
    supabase = get_supabase_admin_client()
    today = date.today()

    # Get today's workout
    workout_result = (
        supabase.table("daily_workouts")
        .select("*")
        .eq("user_id", user["id"])
        .eq("workout_date", today.isoformat())
        .maybe_single()
        .execute()
    )

    if not workout_result.data:
        return TodayWorkoutResponse(
            has_plan=False,
            workout=None,
            can_regenerate=True,
        )

    workout = workout_result.data
    day_names = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    day_name = day_names[today.weekday()]

    # Get wellness hint (if available)
    wellness_hint = None
    try:
        from ..services.user_api_service import UserApiService

        api_service = UserApiService(user["id"])
        fitness_data = api_service.get_fitness_data()

        tsb = fitness_data.get("training", {}).get("tsb", 0)
        hrv = fitness_data.get("wellness", {}).get("hrv")

        if tsb < -20:
            wellness_hint = "⚠️ TSB가 매우 낮습니다. 가벼운 운동을 권장합니다."
        elif hrv and hrv < 40:
            wellness_hint = "💤 HRV가 평소보다 낮습니다. 컨디션을 고려해주세요."
    except Exception:
        pass

    return TodayWorkoutResponse(
        has_plan=True,
        workout=DailyWorkoutResponse(
            id=workout["id"],
            workout_date=workout["workout_date"],
            day_name=day_name,
            planned_name=workout.get("planned_name"),
            planned_type=workout.get("planned_type"),
            planned_duration=workout.get("planned_duration"),
            planned_tss=workout.get("planned_tss"),
            planned_rationale=workout.get("planned_rationale"),
            actual_name=workout.get("actual_name"),
            actual_type=workout.get("actual_type"),
            status=workout.get("status", "planned"),
        ),
        wellness_hint=wellness_hint,
        can_regenerate=workout.get("status") not in ["completed", "skipped"],
    )


@router.post("/plans/today/regenerate")
async def regenerate_today_workout(
    request: RegenerateRequest, user: dict = Depends(get_current_user)
):
    """Regenerate today's workout based on current condition."""
    supabase = get_supabase_admin_client()
    today = date.today()

    # Get today's existing workout
    workout_result = (
        supabase.table("daily_workouts")
        .select("*")
        .eq("user_id", user["id"])
        .eq("workout_date", today.isoformat())
        .maybe_single()
        .execute()
    )

    if not workout_result.data:
        raise HTTPException(status_code=404, detail="No workout found for today")

    workout_id = workout_result.data["id"]

    # Get user settings
    settings_result = (
        supabase.table("user_settings")
        .select("*")
        .eq("user_id", user["id"])
        .maybe_single()
        .execute()
    )

    user_settings = settings_result.data or {}

    # Get current fitness metrics
    try:
        from ..services.user_api_service import UserApiService

        api_service = UserApiService(user["id"])
        fitness_data = api_service.get_fitness_data()

        ctl = fitness_data.get("training", {}).get("ctl", 50.0)
        atl = fitness_data.get("training", {}).get("atl", 50.0)
        tsb = fitness_data.get("training", {}).get("tsb", 0.0)
        form_status = fitness_data.get("training", {}).get("form_status", "Neutral")
    except Exception as e:
        logger.warning(f"Failed to get fitness data: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get current fitness data"
        )

    # Generate single workout using enhanced generator
    from src.services.workout_generator import WorkoutGenerator
    from src.clients.llm import LLMClient
    from src.config import load_config, UserProfile

    config = load_config()
    llm_client = LLMClient.from_config(config.llm)

    # Build user profile
    profile = UserProfile(
        ftp=user_settings.get("ftp", 200),
        max_hr=user_settings.get("max_hr", 190),
        lthr=user_settings.get("lthr", 170),
        training_goal=user_settings.get("training_goal", "General"),
        exclude_barcode_workouts=user_settings.get("exclude_barcode_workouts", False),
    )

    generator = WorkoutGenerator(
        llm_client=llm_client,
        user_profile=profile,
        max_duration_minutes=user_settings.get("preferred_duration", 60),
    )

    # Create training metrics
    from src.services.data_processor import TrainingMetrics, WellnessMetrics

    training_metrics = TrainingMetrics(
        ctl=ctl,
        atl=atl,
        tsb=tsb,
        form_status=form_status,
    )

    wellness_data = fitness_data.get("wellness", {})
    wellness_metrics = WellnessMetrics(
        readiness=wellness_data.get("readiness", "Unknown"),
        hrv=wellness_data.get("hrv"),
        rhr=wellness_data.get("rhr"),
        sleep_hours=wellness_data.get("sleep_hours"),
    )

    # Generate new workout
    new_workout = generator.generate_enhanced(
        training_metrics=training_metrics,
        wellness_metrics=wellness_metrics,
        target_date=today,
        style=user_settings.get("training_style", "auto"),
        duration=user_settings.get("preferred_duration", 60),
    )

    # Update the daily workout with actual values
    supabase.table("daily_workouts").update(
        {
            "actual_name": new_workout.name,
            "actual_type": new_workout.workout_type,
            "actual_duration": new_workout.estimated_duration_minutes,
            "actual_tss": new_workout.estimated_tss,
            "actual_description": new_workout.description,
            "actual_steps": new_workout.steps,
            "actual_generated_at": datetime.now().isoformat(),
            "regeneration_reason": request.reason or "Condition-based regeneration",
            "status": "regenerated",
        }
    ).eq("id", workout_id).execute()

    logger.info(f"Regenerated workout {workout_id} for user {user['id']}")

    return {
        "success": True,
        "workout": {
            "name": new_workout.name,
            "type": new_workout.workout_type,
            "duration": new_workout.estimated_duration_minutes,
            "tss": new_workout.estimated_tss,
            "description": new_workout.description,
        },
    }


@router.put("/plans/daily/{workout_id}/skip")
async def skip_workout(workout_id: str, user: dict = Depends(get_current_user)):
    """Mark a workout as skipped."""
    supabase = get_supabase_admin_client()

    # Verify ownership
    workout_result = (
        supabase.table("daily_workouts")
        .select("*")
        .eq("id", workout_id)
        .eq("user_id", user["id"])
        .maybe_single()
        .execute()
    )

    if not workout_result.data:
        raise HTTPException(status_code=404, detail="Workout not found")

    # Update status
    supabase.table("daily_workouts").update(
        {
            "status": "skipped",
        }
    ).eq("id", workout_id).execute()

    return {"success": True, "message": "Workout marked as skipped"}


@router.delete("/plans/weekly/{plan_id}")
async def delete_weekly_plan(plan_id: str, user: dict = Depends(get_current_user)):
    """Delete a weekly plan and its workouts."""
    supabase = get_supabase_admin_client()

    # Verify ownership
    plan_result = (
        supabase.table("weekly_plans")
        .select("*")
        .eq("id", plan_id)
        .eq("user_id", user["id"])
        .maybe_single()
        .execute()
    )

    if not plan_result.data:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Delete (cascades to daily_workouts)
    supabase.table("weekly_plans").delete().eq("id", plan_id).execute()

    return {"success": True, "message": "Weekly plan deleted"}
