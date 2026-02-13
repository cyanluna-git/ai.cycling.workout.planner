"""User settings router."""

import os
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, List

import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from src.clients.supabase_client import get_supabase_client, get_supabase_admin_client
from .auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


# --- Schemas ---


class UserSettings(BaseModel):
    ftp: int = 200
    max_hr: int = 190
    lthr: int = 170
    training_goal: str = "지구력 강화"
    exclude_barcode_workouts: bool = False
    # New fields for weekly planning
    training_style: str = (
        "auto"  # auto, polarized, norwegian, sweetspot, threshold, endurance
    )
    training_focus: str = "maintain"  # recovery, maintain, build
    preferred_duration: int = 60  # Default workout duration in minutes
    weekly_tss_target: Optional[int] = None  # Manual weekly TSS target (300-700), None=auto
    weekly_plan_enabled: bool = False  # Opt-in for weekly plan auto-generation
    weekly_plan_day: int = 0  # Day to generate (0=Sunday)
    weekly_availability: Dict[str, str] = {
        "0": "available", "1": "available", "2": "available",
        "3": "available", "4": "available", "5": "available",
        "6": "available",
    }  # Day availability: available | unavailable | rest


class UserApiKeys(BaseModel):
    intervals_api_key: Optional[str] = None
    athlete_id: Optional[str] = None


class UserSettingsResponse(BaseModel):
    settings: UserSettings
    api_keys_configured: bool  # Don't expose actual keys


# --- Endpoints ---


@router.get("/settings", response_model=UserSettingsResponse)
async def get_settings(user: dict = Depends(get_current_user)):
    """Get current user's settings."""
    supabase = get_supabase_admin_client()

    # Get settings
    settings_result = (
        supabase.table("user_settings")
        .select("*")
        .eq("user_id", user["id"])
        .maybe_single()
        .execute()
    )

    # Get api keys (just check if configured)
    api_keys_result = (
        supabase.table("user_api_keys")
        .select("intervals_api_key, athlete_id")
        .eq("user_id", user["id"])
        .maybe_single()
        .execute()
    )

    settings_data = settings_result.data if settings_result else {}
    api_keys_data = api_keys_result.data if api_keys_result else {}

    return UserSettingsResponse(
        settings=UserSettings(
            ftp=settings_data.get("ftp", 200),
            max_hr=settings_data.get("max_hr", 190),
            lthr=settings_data.get("lthr", 170),
            training_goal=settings_data.get("training_goal", "지구력 강화"),
            exclude_barcode_workouts=settings_data.get(
                "exclude_barcode_workouts", False
            ),
            # New weekly planning fields
            training_style=settings_data.get("training_style", "auto"),
            training_focus=settings_data.get("training_focus", "maintain"),
            preferred_duration=settings_data.get("preferred_duration", 60),
            weekly_tss_target=settings_data.get("weekly_tss_target"),
            weekly_plan_enabled=settings_data.get("weekly_plan_enabled", False),
            weekly_plan_day=settings_data.get("weekly_plan_day", 0),
            weekly_availability=settings_data.get("weekly_availability", {
                "0": "available", "1": "available", "2": "available",
                "3": "available", "4": "available", "5": "available",
                "6": "available",
            }),
        ),
        api_keys_configured=bool(
            api_keys_data.get("intervals_api_key") and api_keys_data.get("athlete_id")
        ),
    )


@router.put("/settings")
async def update_settings(
    settings: UserSettings, user: dict = Depends(get_current_user)
):
    """Update user settings."""
    # Validate weekly_availability
    valid_statuses = {"available", "unavailable", "rest"}
    valid_keys = {str(i) for i in range(7)}
    for key, val in settings.weekly_availability.items():
        if key not in valid_keys:
            raise HTTPException(status_code=422, detail=f"Invalid day key: {key}. Must be '0'-'6'.")
        if val not in valid_statuses:
            raise HTTPException(status_code=422, detail=f"Invalid status: {val}. Must be available|unavailable|rest.")
    if not any(v == "available" for v in settings.weekly_availability.values()):
        raise HTTPException(status_code=422, detail="At least one day must be 'available'.")

    supabase = get_supabase_admin_client()

    try:
        supabase.table("user_settings").upsert(
            {
                "user_id": user["id"],
                "ftp": settings.ftp,
                "max_hr": settings.max_hr,
                "lthr": settings.lthr,
                "training_goal": settings.training_goal,
                "exclude_barcode_workouts": settings.exclude_barcode_workouts,
                # New weekly planning fields
                "training_style": settings.training_style,
                "training_focus": settings.training_focus,
                "preferred_duration": settings.preferred_duration,
                "weekly_tss_target": settings.weekly_tss_target,
                "weekly_plan_enabled": settings.weekly_plan_enabled,
                "weekly_plan_day": settings.weekly_plan_day,
                "weekly_availability": settings.weekly_availability,
            },
            on_conflict="user_id",
        ).execute()

        return {"message": "Settings updated successfully"}
    except Exception as e:
        logger.exception(f"Failed to update settings for user {user['id']}: {e}")
        raise HTTPException(status_code=400, detail=str(e))


from ..services.cache_service import clear_user_cache


@router.put("/settings/api-keys")
async def update_api_keys(
    api_keys: UserApiKeys, user: dict = Depends(get_current_user)
):
    """Update user API keys."""
    supabase = get_supabase_admin_client()

    try:
        logger.info(f"Updating API keys for user {user['id']}")

        # In production, encrypt these keys before storing
        supabase.table("user_api_keys").upsert(
            {
                "user_id": user["id"],
                "intervals_api_key": api_keys.intervals_api_key,
                "athlete_id": api_keys.athlete_id,
            },
            on_conflict="user_id",
        ).execute()

        # Clear cache so new API keys are used immediately
        clear_user_cache(user["id"])

        logger.info(
            f"Successfully updated API keys and cleared cache for user {user['id']}"
        )
        return {"message": "API keys updated successfully"}
    except Exception as e:
        logger.exception(f"Failed to update API keys for user {user['id']}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/settings/api-keys/check")
async def check_api_keys(user: dict = Depends(get_current_user)):
    """Check if Intervals.icu API keys are configured."""
    supabase = get_supabase_admin_client()

    result = (
        supabase.table("user_api_keys")
        .select("intervals_api_key, athlete_id")
        .eq("user_id", user["id"])
        .maybe_single()
        .execute()
    )

    print(f"[DEBUG] check_api_keys result: {result}")
    data = result.data if result else {}
    print(f"[DEBUG] check_api_keys data: {data}")

    return {
        "intervals_configured": bool(
            data.get("intervals_api_key") and data.get("athlete_id")
        ),
    }
