"""User settings router."""

import os
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

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
    supabase = get_supabase_admin_client()

    try:
        supabase.table("user_settings").upsert(
            {
                "user_id": user["id"],
                "ftp": settings.ftp,
                "max_hr": settings.max_hr,
                "lthr": settings.lthr,
                "training_goal": settings.training_goal,
            },
            on_conflict="user_id",
        ).execute()

        return {"message": "Settings updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/settings/api-keys")
async def update_api_keys(
    api_keys: UserApiKeys, user: dict = Depends(get_current_user)
):
    """Update user API keys."""
    supabase = get_supabase_admin_client()

    try:
        logger.info(f"Updating API keys for user {user['id']}")
        logger.debug(f"Received athlete_id: {api_keys.athlete_id}")

        # In production, encrypt these keys before storing
        result = (
            supabase.table("user_api_keys")
            .upsert(
                {
                    "user_id": user["id"],
                    "intervals_api_key": api_keys.intervals_api_key,
                    "athlete_id": api_keys.athlete_id,
                },
                on_conflict="user_id",
            )
            .execute()
        )

        logger.info(f"API keys upsert result: {result}")
        logger.debug(f"Stored data: {result.data}")

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
