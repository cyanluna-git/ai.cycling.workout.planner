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
from ..services.cache_service import clear_user_cache

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
    planned_modules: Optional[List[str]] = None  # Module keys for power profile
    planned_steps: Optional[List[dict]] = None  # WorkoutStep[] for chart rendering
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
    weekly_tss_target: Optional[int] = None
    daily_workouts: List[DailyWorkoutResponse]
    used_modules: Optional[List[str]] = None


class GenerateWeeklyPlanRequest(BaseModel):
    """Request to generate a weekly plan."""

    week_start: Optional[str] = None  # YYYY-MM-DD, default: next Monday
    weekly_tss_target: Optional[int] = None  # Weekly TSS target (300-700)
    ftp: Optional[float] = None  # Override profile FTP (watts)
    weight: Optional[float] = None  # Override profile weight (kg)
    wellness_score: Optional[float] = None  # Daily wellness 0-10
    indoor_outdoor_pref: Optional[str] = None  # indoor|outdoor|mixed


class TodayWorkoutResponse(BaseModel):
    """Today's workout info."""

    has_plan: bool
    workout: Optional[DailyWorkoutResponse] = None
    wellness_hint: Optional[str] = None
    can_regenerate: bool = True
    # Weekly TSS tracking
    weekly_tss_target: Optional[int] = None
    weekly_tss_accumulated: Optional[int] = None
    weekly_tss_remaining: Optional[int] = None
    days_remaining_in_week: Optional[int] = None
    target_achievable: bool = True
    achievement_warning: Optional[str] = None


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


def _smart_fallback_for_unknown_block(block_type: str, block: dict) -> Optional[dict]:
    """Smart fallback for unknown block types based on naming patterns.

    Args:
        block_type: The unknown block type string
        block: The block data dictionary

    Returns:
        A WorkoutStep dict if fallback is found, None otherwise
    """
    # Pattern matching for common variations
    type_lower = block_type.lower()

    # Warmup patterns
    if any(
        keyword in type_lower for keyword in ["warmup", "warm_up", "warm-up", "ramp_up"]
    ):
        return {
            "duration": block.get("duration_minutes", 10) * 60,
            "power": {
                "start": block.get("start_power", 45),
                "end": block.get("end_power", 75),
                "units": "%ftp",
            },
            "ramp": True,
            "warmup": True,
        }

    # Cooldown patterns
    if any(
        keyword in type_lower
        for keyword in ["cooldown", "cool_down", "cool-down", "ramp_down"]
    ):
        return {
            "duration": block.get("duration_minutes", 10) * 60,
            "power": {
                "start": block.get("start_power", 70),
                "end": block.get("end_power", 40),
                "units": "%ftp",
            },
            "ramp": True,
            "cooldown": True,
        }

    # Interval patterns
    if any(keyword in type_lower for keyword in ["interval", "repeat", "set"]):
        # Try to extract work/rest pattern
        work_power = block.get("work_power") or block.get("power", 95)
        rest_power = block.get("rest_power", 50)
        reps = block.get("repetitions") or block.get("reps", 1)
        work_duration = block.get("work_duration_seconds") or block.get(
            "work_duration", 300
        )
        rest_duration = block.get("rest_duration_seconds") or block.get(
            "rest_duration", 120
        )

        # Single work/rest pair - repetitions handled by repeat key
        work_step = {
            "duration": work_duration,
            "power": {"value": work_power, "units": "%ftp"},
        }
        rest_step = {
            "duration": rest_duration,
            "power": {"value": rest_power, "units": "%ftp"},
        }

        return {
            "duration": 0,
            "repeat": reps,
            "steps": [work_step, rest_step],  # Single pair, not expanded
        }

    # Rest patterns
    if any(keyword in type_lower for keyword in ["rest", "recovery", "easy"]):
        return {
            "duration": block.get("duration_minutes", 1) * 60,
            "power": {"value": block.get("power", 50), "units": "%ftp"},
        }

    # Steady state patterns (default fallback)
    if "duration_minutes" in block and "power" in block:
        return {
            "duration": block["duration_minutes"] * 60,
            "power": {"value": block["power"], "units": "%ftp"},
        }

    # No fallback found
    return None


def convert_structure_to_steps(module_keys: List[str], ftp: int) -> List[dict]:
    """Convert workout module keys to WorkoutStep[] format for frontend chart rendering.

    Args:
        module_keys: List of module keys like ["warmup_ramp", "sst_10min", "flush_and_fade"]
        ftp: User's FTP for power calculations

    Returns:
        List of workout step dictionaries compatible with frontend WorkoutStep type
    """
    from src.services.workout_modules import (
        ALL_MODULES,
        get_module_category,
    )

    # Use the combined module dictionary
    all_modules = ALL_MODULES

    steps = []

    # Fallback mapping for common LLM-invented module names
    fallback_modules = {
        "progressive_warmup_20min": "progressive_warmup_15min",
        "progressive_warmup_10min": "stepped_warmup_10min",
        "standard_warmup": "ramp_standard",
        "basic_cooldown": "flush_and_fade",
        "easy_cooldown": "flush_and_fade",
    }

    # CRITICAL: Validate warmup/cooldown order before processing
    # Warmup modules must come first, cooldown modules must come last
    logger.info(f"🔍 Validating module order for: {module_keys}")

    warmup_indices = []
    cooldown_indices = []

    for idx, module_key in enumerate(module_keys):
        category = get_module_category(module_key)
        if category == "Warmup":
            warmup_indices.append(idx)
            logger.debug(f"  Found WARMUP module '{module_key}' at position {idx}")
        elif category == "Cooldown":
            cooldown_indices.append(idx)
            logger.debug(f"  Found COOLDOWN module '{module_key}' at position {idx}")

    # Check if warmup modules are at the beginning
    if warmup_indices and warmup_indices[0] != 0:
        logger.error(
            f"❌ INVALID STRUCTURE: Warmup module '{module_keys[warmup_indices[0]]}' found at position {warmup_indices[0]}, should be at position 0"
        )
        logger.error(f"   Original order: {module_keys}")
        # Auto-fix: Move warmup modules to the beginning
        warmup_modules = [module_keys[i] for i in warmup_indices]
        other_modules = [
            module_keys[i] for i in range(len(module_keys)) if i not in warmup_indices
        ]
        module_keys = warmup_modules + other_modules
        logger.warning(f"🔧 AUTO-FIX: Reordered modules to: {module_keys}")
        # Recalculate indices after reordering
        cooldown_indices = [
            i for i, k in enumerate(module_keys) if get_module_category(k) == "Cooldown"
        ]

    # Check if cooldown modules are at the end
    if cooldown_indices:
        expected_start = len(module_keys) - len(cooldown_indices)
        if cooldown_indices[0] != expected_start:
            logger.error(
                f"❌ INVALID STRUCTURE: Cooldown module '{module_keys[cooldown_indices[0]]}' found at position {cooldown_indices[0]}, should be at position {expected_start}"
            )
            logger.error(f"   Original order: {module_keys}")
            # Auto-fix: Move cooldown modules to the end
            cooldown_modules = [module_keys[i] for i in cooldown_indices]
            other_modules = [
                module_keys[i]
                for i in range(len(module_keys))
                if i not in cooldown_indices
            ]
            module_keys = other_modules + cooldown_modules
            logger.warning(f"🔧 AUTO-FIX: Reordered modules to: {module_keys}")

    logger.info(f"✅ Final validated order: {module_keys}")

    for module_key in module_keys:
        module = all_modules.get(module_key)
        if not module:
            # Try fallback mapping
            fallback_key = fallback_modules.get(module_key)
            if fallback_key:
                module = all_modules.get(fallback_key)
                logger.info(
                    f"Module not found: {module_key}, using fallback: {fallback_key}"
                )
            else:
                logger.warning(
                    f"Module not found: {module_key}, no fallback available. Skipping."
                )
                continue

        # Convert each block in module structure to WorkoutStep
        for block in module.get("structure", []):
            block_type = block.get("type")

            if block_type == "warmup_ramp":
                # Ramp from start_power to end_power
                steps.append(
                    {
                        "duration": block["duration_minutes"] * 60,
                        "power": {
                            "start": block["start_power"],
                            "end": block["end_power"],
                            "units": "%ftp",
                        },
                        "ramp": True,
                        "warmup": True,
                    }
                )

            elif block_type == "cooldown_ramp":
                # Cooldown ramp
                steps.append(
                    {
                        "duration": block["duration_minutes"] * 60,
                        "power": {
                            "start": block["start_power"],
                            "end": block["end_power"],
                            "units": "%ftp",
                        },
                        "ramp": True,
                        "cooldown": True,
                    }
                )

            elif block_type == "steady":
                # Steady state power
                steps.append(
                    {
                        "duration": block["duration_minutes"] * 60,
                        "power": {"value": block["power"], "units": "%ftp"},
                    }
                )

            elif block_type == "main_set_classic":
                # Interval block: single work + rest pair, repetitions handled by repeat key
                # Frontend stepsToChartData() and ZWO converter both use repeat to loop
                work_step = {
                    "duration": block["work_duration_seconds"],
                    "power": {"value": block["work_power"], "units": "%ftp"},
                }
                rest_step = {
                    "duration": block["rest_duration_seconds"],
                    "power": {"value": block["rest_power"], "units": "%ftp"},
                }

                steps.append(
                    {
                        "duration": 0,  # Duration handled by nested steps
                        "repeat": block["repetitions"],
                        "steps": [work_step, rest_step],  # Single pair, not expanded
                    }
                )

            elif block_type == "rest":
                # Simple rest block
                steps.append(
                    {
                        "duration": block.get("duration_minutes", 1) * 60,
                        "power": {"value": block.get("power", 50), "units": "%ftp"},
                    }
                )

            elif block_type == "over_under":
                # Over/Under intervals: single over + under pair, repetitions handled by repeat key
                over_step = {
                    "duration": block.get("over_duration_seconds", 120),
                    "power": {
                        "value": block.get("over_power", 105),
                        "units": "%ftp",
                    },
                }
                under_step = {
                    "duration": block.get("under_duration_seconds", 120),
                    "power": {
                        "value": block.get("under_power", 95),
                        "units": "%ftp",
                    },
                }

                steps.append(
                    {
                        "duration": 0,  # Duration handled by nested steps
                        "repeat": block.get("repetitions", 1),
                        "steps": [over_step, under_step],  # Single pair, not expanded
                    }
                )

            else:
                # Unknown block type - try smart fallback based on type name
                logger.warning(
                    f"Unknown block type: {block_type}, attempting smart fallback"
                )
                fallback_step = _smart_fallback_for_unknown_block(block_type, block)
                if fallback_step:
                    steps.append(fallback_step)
                    logger.info(
                        f"Applied smart fallback for '{block_type}': {fallback_step}"
                    )
                else:
                    logger.error(f"No fallback available for block type: {block_type}")

    return steps


# --- Endpoints ---


@router.get("/plans/weekly", response_model=Optional[WeeklyPlanResponse])
async def get_current_weekly_plan(
    user: dict = Depends(get_current_user), week_start_date: Optional[str] = None
):
    """Get the current week's plan (or specific week if week_start_date provided)."""
    supabase = get_supabase_admin_client()

    if week_start_date:
        week_start = datetime.strptime(week_start_date, "%Y-%m-%d").date()
        week_end = week_start + timedelta(days=6)
    else:
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

    if not plan_result or not plan_result.data:
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

    # Get user profile for FTP (needed for power calculations)
    from api.services.user_api_service import get_user_profile

    try:
        user_profile = await get_user_profile(user["id"])
        ftp = user_profile.ftp
    except Exception as e:
        logger.error(f"Failed to get user profile: {e}")
        ftp = 200  # Default FTP if profile fetch fails

    for workout in workouts_result.data:
        workout_date = datetime.strptime(workout["workout_date"], "%Y-%m-%d").date()
        day_index = (workout_date - week_start).days

        # Convert planned_modules to planned_steps for chart rendering
        planned_modules = workout.get("planned_modules", [])
        planned_steps = None
        if planned_modules and len(planned_modules) > 0:
            try:
                planned_steps = convert_structure_to_steps(planned_modules, ftp)
            except Exception as e:
                logger.error(
                    f"Failed to convert modules to steps for {workout['id']}: {e}"
                )
                # Gracefully handle errors - workout will show without chart

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
                planned_modules=planned_modules if planned_modules else None,
                planned_steps=planned_steps,
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
        weekly_tss_target=plan.get("weekly_tss_target"),
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

    user_settings = (
        settings_result.data if settings_result and settings_result.data else {}
    )

    # Get current fitness metrics from Intervals.icu
    try:
        from ..services.user_api_service import get_user_intervals_client
        from src.services.data_processor import DataProcessor

        intervals_client = await get_user_intervals_client(user["id"])
        processor = DataProcessor()
        activities = intervals_client.get_recent_activities(days=42)
        training = processor.calculate_training_metrics(activities)

        ctl = training.ctl
        atl = training.atl
        tsb = training.tsb
        form_status = training.form_status
    except Exception as e:
        logger.warning(f"Failed to get fitness data, using defaults: {e}")
        ctl, atl, tsb = 50.0, 50.0, 0.0
        form_status = "Neutral"

    # Generate plan with AI
    from ..services.weekly_plan_service import WeeklyPlanGenerator
    from ..services.user_api_service import get_server_llm_client

    llm_client = get_server_llm_client()

    # Resolve weekly_tss_target: request param > user_settings
    weekly_tss_target = request.weekly_tss_target or user_settings.get("weekly_tss_target")

    generator = WeeklyPlanGenerator(llm_client, user_settings)
    weekly_plan = generator.generate_weekly_plan(
        ctl=ctl,
        atl=atl,
        tsb=tsb,
        form_status=form_status,
        ftp=request.ftp,
        weight=request.weight,
        wellness_score=request.wellness_score,
        indoor_outdoor_pref=request.indoor_outdoor_pref,
        week_start=week_start,
        exclude_barcode=user_settings.get("exclude_barcode_workouts", False),
        weekly_tss_target=weekly_tss_target,
    )

    # Delete existing plan for this week if any
    supabase.table("weekly_plans").delete().eq("user_id", user["id"]).eq(
        "week_start", week_start.isoformat()
    ).execute()

    # Delete existing daily_workouts for this week's date range
    for i in range(7):
        workout_date = (week_start + timedelta(days=i)).isoformat()
        supabase.table("daily_workouts").delete().eq("user_id", user["id"]).eq(
            "workout_date", workout_date
        ).execute()

    # Save weekly plan to DB
    plan_insert_data = {
        "user_id": user["id"],
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "status": "active",
        "training_style": weekly_plan.training_style,
        "total_planned_tss": weekly_plan.total_planned_tss,
    }
    if weekly_tss_target is not None:
        plan_insert_data["weekly_tss_target"] = weekly_tss_target
    plan_result = (
        supabase.table("weekly_plans")
        .insert(plan_insert_data)
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

    # Clear cache to ensure fresh data on next request
    # Clear both granular and complete fitness cache keys
    clear_user_cache(
        user["id"],
        keys=["calendar", "fitness:complete", "fitness:training", "fitness:wellness"],
    )
    logger.info(f"Cleared cache for user {user['id'][:8]}... after plan generation")

    # Return the created plan - pass the week_start we just generated
    return await get_current_weekly_plan(user, week_start_date=week_start.isoformat())


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

    # --- Weekly TSS tracking ---
    week_start, week_end = get_week_dates(today)

    # Get all workouts for this week
    week_workouts_result = (
        supabase.table("daily_workouts")
        .select("*")
        .eq("user_id", user["id"])
        .gte("workout_date", week_start.isoformat())
        .lte("workout_date", week_end.isoformat())
        .execute()
    )
    week_workouts = week_workouts_result.data if week_workouts_result and week_workouts_result.data else []

    # Accumulated TSS (completed workouts only)
    accumulated_tss = sum(
        w.get("actual_tss") or w.get("planned_tss", 0)
        for w in week_workouts
        if w.get("status") == "completed"
    )

    # Get weekly plan for TSS target
    weekly_plan_result = (
        supabase.table("weekly_plans")
        .select("*")
        .eq("user_id", user["id"])
        .eq("week_start", week_start.isoformat())
        .maybe_single()
        .execute()
    )
    weekly_tss_target = None
    if weekly_plan_result and weekly_plan_result.data:
        weekly_tss_target = weekly_plan_result.data.get("weekly_tss_target")

    # Days remaining (including today)
    days_remaining = (week_end - today).days + 1

    # Remaining TSS and achievability
    remaining_tss = (weekly_tss_target or 0) - accumulated_tss
    MAX_DAILY_TSS = 150
    max_achievable = days_remaining * MAX_DAILY_TSS
    target_achievable = remaining_tss <= max_achievable

    achievement_warning = None
    if weekly_tss_target and not target_achievable:
        achievement_pct = int((accumulated_tss / weekly_tss_target) * 100)
        achievement_warning = (
            f"남은 {days_remaining}일로 목표 TSS {weekly_tss_target} 달성이 어렵습니다. "
            f"현재 {accumulated_tss}/{weekly_tss_target} ({achievement_pct}%). "
            f"목표를 조정하시겠습니까?"
        )

    if not workout_result or not workout_result.data:
        return TodayWorkoutResponse(
            has_plan=False,
            workout=None,
            can_regenerate=True,
            weekly_tss_target=weekly_tss_target,
            weekly_tss_accumulated=accumulated_tss,
            weekly_tss_remaining=max(remaining_tss, 0) if weekly_tss_target else None,
            days_remaining_in_week=days_remaining,
            target_achievable=target_achievable,
            achievement_warning=achievement_warning,
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
        from ..services.user_api_service import get_user_intervals_client
        from src.services.data_processor import DataProcessor

        intervals_client = await get_user_intervals_client(user["id"])
        processor = DataProcessor()
        activities = intervals_client.get_recent_activities(days=42)
        training = processor.calculate_training_metrics(activities)

        tsb = training.tsb

        if tsb < -20:
            wellness_hint = "⚠️ TSB가 매우 낮습니다. 가벼운 운동을 권장합니다."
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
        weekly_tss_target=weekly_tss_target,
        weekly_tss_accumulated=accumulated_tss,
        weekly_tss_remaining=max(remaining_tss, 0) if weekly_tss_target else None,
        days_remaining_in_week=days_remaining,
        target_achievable=target_achievable,
        achievement_warning=achievement_warning,
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

    if not workout_result or not workout_result.data:
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

    user_settings = (
        settings_result.data if settings_result and settings_result.data else {}
    )

    # Get current fitness metrics
    try:
        from ..services.user_api_service import get_user_intervals_client
        from src.services.data_processor import DataProcessor

        intervals_client = await get_user_intervals_client(user["id"])
        processor = DataProcessor()
        activities = intervals_client.get_recent_activities(days=42)
        training = processor.calculate_training_metrics(activities)

        ctl = training.ctl
        atl = training.atl
        tsb = training.tsb
        form_status = training.form_status
    except Exception as e:
        logger.warning(f"Failed to get fitness data: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get current fitness data"
        )

    # Generate single workout using enhanced generator
    from src.services.workout_generator import WorkoutGenerator
    from ..services.user_api_service import get_server_llm_client
    from src.config import UserProfile

    llm_client = get_server_llm_client()

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

    # Create training metrics (import at function scope to avoid issues)
    from src.services.data_processor import TrainingMetrics as TM, WellnessMetrics as WM

    training_metrics = TM(
        ctl=ctl,
        atl=atl,
        tsb=tsb,
    )

    # Create minimal wellness metrics (we don't have detailed data here)
    wellness_metrics = WM(
        readiness="Unknown",
        hrv=None,
        rhr=None,
        sleep_hours=None,
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

    # Clear cache to ensure fresh data on next request
    clear_user_cache(
        user["id"],
        keys=["calendar", "fitness:complete", "fitness:training", "fitness:wellness"],
    )
    logger.info(
        f"Cleared cache for user {user['id'][:8]}... after workout regeneration"
    )

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

    if not workout_result or not workout_result.data:
        raise HTTPException(status_code=404, detail="Workout not found")

    # Update status
    supabase.table("daily_workouts").update(
        {
            "status": "skipped",
        }
    ).eq("id", workout_id).execute()

    return {"success": True, "message": "Workout marked as skipped"}


@router.post("/plans/weekly/{plan_id}/register-all")
async def register_weekly_plan_to_intervals(
    plan_id: str, user: dict = Depends(get_current_user)
):
    """Register all workouts in a weekly plan to Intervals.icu."""
    from api.services.user_api_service import get_user_intervals_client

    supabase = get_supabase_admin_client()

    # Get the weekly plan
    plan_result = (
        supabase.table("weekly_plans")
        .select("*")
        .eq("id", plan_id)
        .eq("user_id", user["id"])
        .maybe_single()
        .execute()
    )

    if not plan_result or not plan_result.data:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Get all daily workouts for this plan
    workouts_result = (
        supabase.table("daily_workouts")
        .select("*")
        .eq("plan_id", plan_id)
        .order("workout_date")
        .execute()
    )

    if not workouts_result or not workouts_result.data:
        raise HTTPException(status_code=404, detail="No workouts found in plan")

    # Get user's Intervals.icu client
    intervals = await get_user_intervals_client(user["id"])

    # Get user profile for FTP
    from api.services.user_api_service import get_user_profile

    try:
        user_profile = await get_user_profile(user["id"])
        ftp = user_profile.ftp
    except Exception as e:
        logger.error(f"Failed to get user profile: {e}")
        ftp = 200

    registered_count = 0
    failed_count = 0
    errors = []

    for workout in workouts_result.data:
        # Skip rest days
        if workout.get("planned_type") == "Rest":
            continue

        # Skip if no modules (can't build workout)
        planned_modules = workout.get("planned_modules", [])
        if not planned_modules or len(planned_modules) == 0:
            logger.warning(f"Skipping workout {workout['id']}: no modules")
            continue

        try:
            # Convert modules to steps
            planned_steps = convert_structure_to_steps(planned_modules, ftp)

            if not planned_steps or len(planned_steps) == 0:
                logger.warning(f"Skipping workout {workout['id']}: no steps generated")
                continue

            workout_name = f"[AICoach] {workout.get('planned_name', 'Workout')}"
            workout_description = workout.get("planned_rationale", "")
            workout_date = workout.get("workout_date")

            # Calculate moving time from modules
            total_duration_minutes = workout.get("planned_duration", 60)
            moving_time = total_duration_minutes * 60  # Convert to seconds

            # Check if a workout already exists for this date and delete it
            existing_workout = intervals.check_workout_exists(workout_date)
            if existing_workout:
                existing_id = existing_workout.get("id")
                logger.info(
                    f"Found existing workout on {workout_date} (event_id: {existing_id}), deleting before registration"
                )
                intervals.delete_event(existing_id)

            # Register to Intervals.icu
            result = intervals.create_workout(
                target_date=workout_date,
                name=workout_name,
                description=workout_description,
                moving_time=moving_time,
                workout_type="Ride",
                training_load=workout.get("planned_tss"),
                steps=planned_steps,
            )

            # Store event_id for sync tracking
            event_id = result.get("id")
            if event_id:
                supabase.table("daily_workouts").update(
                    {
                        "intervals_event_id": event_id,
                        "status": "registered",
                        "updated_at": datetime.now().isoformat(),
                    }
                ).eq("id", workout["id"]).execute()
                logger.info(
                    f"Registered workout {workout_name} for {workout_date} (event_id: {event_id})"
                )
            else:
                logger.warning(
                    f"Registered workout {workout_name} but no event_id returned"
                )

            registered_count += 1

        except Exception as e:
            failed_count += 1
            error_msg = f"{workout.get('workout_date')}: {str(e)}"
            errors.append(error_msg)
            logger.error(
                f"Failed to register workout {workout.get('id')}: {e}", exc_info=True
            )

    # Clear cache after registering workouts to Intervals.icu
    if registered_count > 0:
        clear_user_cache(
            user["id"],
            keys=[
                "calendar",
                "fitness:complete",
                "fitness:training",
                "fitness:wellness",
            ],
        )
        logger.info(
            f"Cleared cache for user {user['id'][:8]}... after registering {registered_count} workouts"
        )

    return {
        "success": True,
        "registered": registered_count,
        "failed": failed_count,
        "errors": errors if errors else None,
        "message": f"Successfully registered {registered_count} workouts to Intervals.icu",
    }


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

    if not plan_result or not plan_result.data:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Delete (cascades to daily_workouts)
    supabase.table("weekly_plans").delete().eq("id", plan_id).execute()

    return {"success": True, "message": "Weekly plan deleted"}


@router.post("/plans/weekly/{plan_id}/sync")
async def sync_weekly_plan_with_intervals(
    plan_id: str, user: dict = Depends(get_current_user)
):
    """Sync a weekly plan with Intervals.icu to detect changes.

    Compares local daily_workouts with Intervals.icu events to detect:
    - Deleted workouts (exist in DB but not in Intervals.icu)
    - Moved workouts (date changed in Intervals.icu)
    - Modified workouts (name/duration changed)
    """
    from api.services.user_api_service import get_user_intervals_client

    supabase = get_supabase_admin_client()

    # Get the weekly plan
    plan_result = (
        supabase.table("weekly_plans")
        .select("*")
        .eq("id", plan_id)
        .eq("user_id", user["id"])
        .maybe_single()
        .execute()
    )

    if not plan_result or not plan_result.data:
        raise HTTPException(status_code=404, detail="Plan not found")

    plan = plan_result.data
    week_start = plan["week_start"]
    week_end = plan["week_end"]

    # Get daily workouts with intervals_event_id
    workouts_result = (
        supabase.table("daily_workouts")
        .select("*")
        .eq("plan_id", plan_id)
        .not_.is_("intervals_event_id", "null")
        .execute()
    )

    workouts = workouts_result.data if workouts_result and workouts_result.data else []

    if not workouts:
        return {
            "success": True,
            "changes": {"deleted": [], "moved": [], "modified": []},
            "synced": 0,
            "message": "No registered workouts to sync",
        }

    # Get Intervals.icu client
    intervals = get_user_intervals_client(user["id"])
    if not intervals:
        raise HTTPException(status_code=400, detail="Intervals.icu not configured")

    # Fetch events from Intervals.icu for the week
    try:
        events = intervals.get_events(oldest=week_start, newest=week_end)
    except Exception as e:
        logger.error(f"Failed to fetch events from Intervals.icu: {e}")
        raise HTTPException(
            status_code=502, detail=f"Failed to fetch from Intervals.icu: {str(e)}"
        )

    # Build event lookup by ID
    events_by_id = {str(event.get("id")): event for event in events if event.get("id")}

    # Detect changes
    deleted = []
    moved = []
    modified = []
    synced = 0

    for workout in workouts:
        event_id = str(workout.get("intervals_event_id"))
        workout_date = workout.get("workout_date")
        workout_name = workout.get("planned_name", "")

        if event_id not in events_by_id:
            # Workout was deleted from Intervals.icu
            deleted.append(
                {"date": workout_date, "name": workout_name, "event_id": event_id}
            )
            # Clear the event_id in DB
            supabase.table("daily_workouts").update(
                {
                    "intervals_event_id": None,
                    "status": "planned",  # Revert to planned status
                    "updated_at": datetime.now().isoformat(),
                }
            ).eq("id", workout["id"]).execute()
        else:
            # Check if moved or modified
            event = events_by_id[event_id]
            event_date = event.get("start_date_local", "")[:10]  # Extract YYYY-MM-DD
            event_name = event.get("name", "")

            if event_date != workout_date:
                # Workout was moved to a different date
                moved.append(
                    {
                        "from_date": workout_date,
                        "to_date": event_date,
                        "name": event_name,
                        "event_id": event_id,
                    }
                )
                # Note: We don't auto-update the date as it might conflict with another workout
                # Just report the change for now

            if event_name and event_name != workout_name:
                # Workout name was modified
                modified.append(
                    {
                        "date": workout_date,
                        "old_name": workout_name,
                        "new_name": event_name,
                        "event_id": event_id,
                    }
                )

            synced += 1

    # Build message
    changes_count = len(deleted) + len(moved) + len(modified)
    if changes_count == 0:
        message = f"All {synced} workouts are in sync with Intervals.icu"
    else:
        parts = []
        if deleted:
            parts.append(f"{len(deleted)} deleted")
        if moved:
            parts.append(f"{len(moved)} moved")
        if modified:
            parts.append(f"{len(modified)} modified")
        message = f"{changes_count} changes detected: {', '.join(parts)}"

    return {
        "success": True,
        "changes": {"deleted": deleted, "moved": moved, "modified": modified},
        "synced": synced,
        "message": message,
    }
