"""User API Service.

This module handles retrieval of user-specific API keys and creates
configured clients for LLM and Intervals.icu integration.
"""

import os
from typing import Optional
from dataclasses import dataclass

from src.clients.supabase_client import get_supabase_admin_client
from src.clients.intervals import IntervalsClient
from src.clients.llm import LLMClient
from src.config import IntervalsConfig, LLMConfig, UserProfile
from src.services.data_processor import DataProcessor


@dataclass
class UserApiKeysData:
    """User API keys from database."""

    intervals_api_key: Optional[str] = None
    athlete_id: Optional[str] = None


@dataclass
class UserSettingsData:
    """User training settings."""

    ftp: int = 200
    max_hr: int = 190
    lthr: int = 170
    training_goal: str = "지구력 강화"


class UserApiServiceError(Exception):
    """Exception for user API service errors."""

    pass


async def get_user_api_keys(user_id: str) -> UserApiKeysData:
    """Retrieve user's API keys from database.

    Args:
        user_id: The user's unique ID.

    Returns:
        UserApiKeysData with the user's stored API keys.

    Raises:
        UserApiServiceError: If API keys are not configured.
    """
    supabase = get_supabase_admin_client()

    result = (
        supabase.table("user_api_keys")
        .select("intervals_api_key, athlete_id")
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )

    data = result.data if result else None

    if not data:
        raise UserApiServiceError(
            "API 키가 설정되지 않았습니다. 설정 페이지에서 API 키를 입력해주세요."
        )

    return UserApiKeysData(
        intervals_api_key=data.get("intervals_api_key"),
        athlete_id=data.get("athlete_id"),
    )


async def get_user_settings(user_id: str) -> UserSettingsData:
    """Retrieve user's training settings from database.

    Args:
        user_id: The user's unique ID.

    Returns:
        UserSettingsData with the user's training profile.
    """
    supabase = get_supabase_admin_client()

    result = (
        supabase.table("user_settings")
        .select("ftp, max_hr, lthr, training_goal")
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )

    data = result.data if result else {}
    if data is None:
        data = {}

    return UserSettingsData(
        ftp=data.get("ftp", 200),
        max_hr=data.get("max_hr", 190),
        lthr=data.get("lthr", 170),
        training_goal=data.get("training_goal", "지구력 강화"),
    )


async def get_user_intervals_client(user_id: str) -> IntervalsClient:
    """Create an IntervalsClient configured with user's API keys.

    Args:
        user_id: The user's unique ID.

    Returns:
        Configured IntervalsClient instance.

    Raises:
        UserApiServiceError: If Intervals.icu keys are not configured.
    """
    api_keys = await get_user_api_keys(user_id)

    if not api_keys.intervals_api_key or not api_keys.athlete_id:
        raise UserApiServiceError(
            "Intervals.icu API 키가 설정되지 않았습니다. 설정 페이지에서 입력해주세요."
        )

    config = IntervalsConfig(
        api_key=api_keys.intervals_api_key,
        athlete_id=api_keys.athlete_id,
    )

    return IntervalsClient(config)


def get_server_llm_client() -> LLMClient:
    """Create an LLMClient configured with server's environment variables.

    Uses LLM_PROVIDER and LLM_API_KEY from server environment.
    This centralizes LLM API key management on the server side.

    Returns:
        Configured LLMClient instance.

    Raises:
        UserApiServiceError: If server LLM API key is not configured.
    """
    provider = os.getenv("LLM_PROVIDER", "gemini")
    api_key = os.getenv("LLM_API_KEY")
    model = os.getenv("LLM_MODEL")

    if not api_key:
        raise UserApiServiceError(
            "서버 LLM API 키가 설정되지 않았습니다. 관리자에게 문의하세요."
        )

    # Determine model based on provider if not specified
    if not model:
        model_map = {
            "gemini": "gemini-2.0-flash",
            "openai": "gpt-4o",
            "anthropic": "claude-3-5-sonnet-20241022",
        }
        model = model_map.get(provider, "gpt-4o")

    config = LLMConfig(
        provider=provider,
        api_key=api_key,
        model=model,
    )

    return LLMClient.from_config(config)


async def get_user_profile(user_id: str) -> UserProfile:
    """Get user's training profile for workout generation.

    Args:
        user_id: The user's unique ID.

    Returns:
        UserProfile instance with user's training settings.
    """
    settings = await get_user_settings(user_id)

    return UserProfile(
        ftp=settings.ftp,
        max_hr=settings.max_hr,
        lthr=settings.lthr,
        training_goal=settings.training_goal,
    )


def get_data_processor() -> DataProcessor:
    """Get a DataProcessor instance.

    Returns:
        DataProcessor instance for processing training data.
    """
    return DataProcessor()
