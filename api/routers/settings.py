"""User settings router."""

import os
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from src.clients.supabase_client import get_supabase_client
from .auth import get_current_user

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
    llm_provider: str = "gemini"
    llm_api_key: Optional[str] = None


class UserSettingsResponse(BaseModel):
    settings: UserSettings
    api_keys_configured: bool  # Don't expose actual keys


# --- Endpoints ---


@router.get("/settings", response_model=UserSettingsResponse)
async def get_settings(user: dict = Depends(get_current_user)):
    """Get current user's settings."""
    supabase = get_supabase_client()

    # Get settings
    settings_result = (
        supabase.table("user_settings")
        .select("*")
        .eq("user_id", user["id"])
        .single()
        .execute()
    )

    # Get api keys (just check if configured)
    api_keys_result = (
        supabase.table("user_api_keys")
        .select("intervals_api_key, llm_api_key")
        .eq("user_id", user["id"])
        .single()
        .execute()
    )

    settings_data = settings_result.data or {}
    api_keys_data = api_keys_result.data or {}

    return UserSettingsResponse(
        settings=UserSettings(
            ftp=settings_data.get("ftp", 200),
            max_hr=settings_data.get("max_hr", 190),
            lthr=settings_data.get("lthr", 170),
            training_goal=settings_data.get("training_goal", "지구력 강화"),
        ),
        api_keys_configured=bool(
            api_keys_data.get("intervals_api_key") and api_keys_data.get("llm_api_key")
        ),
    )


@router.put("/settings")
async def update_settings(
    settings: UserSettings, user: dict = Depends(get_current_user)
):
    """Update user settings."""
    supabase = get_supabase_client()

    try:
        supabase.table("user_settings").upsert(
            {
                "user_id": user["id"],
                "ftp": settings.ftp,
                "max_hr": settings.max_hr,
                "lthr": settings.lthr,
                "training_goal": settings.training_goal,
            }
        ).execute()

        return {"message": "Settings updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/settings/api-keys")
async def update_api_keys(
    api_keys: UserApiKeys, user: dict = Depends(get_current_user)
):
    """Update user API keys."""
    supabase = get_supabase_client()

    try:
        # In production, encrypt these keys before storing
        supabase.table("user_api_keys").upsert(
            {
                "user_id": user["id"],
                "intervals_api_key": api_keys.intervals_api_key,
                "athlete_id": api_keys.athlete_id,
                "llm_provider": api_keys.llm_provider,
                "llm_api_key": api_keys.llm_api_key,
            }
        ).execute()

        return {"message": "API keys updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/settings/api-keys/check")
async def check_api_keys(user: dict = Depends(get_current_user)):
    """Check if API keys are configured."""
    supabase = get_supabase_client()

    result = (
        supabase.table("user_api_keys")
        .select("intervals_api_key, athlete_id, llm_provider, llm_api_key")
        .eq("user_id", user["id"])
        .single()
        .execute()
    )

    data = result.data or {}

    return {
        "intervals_configured": bool(
            data.get("intervals_api_key") and data.get("athlete_id")
        ),
        "llm_configured": bool(data.get("llm_api_key")),
        "llm_provider": data.get("llm_provider", "gemini"),
    }
