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

    Uses multiple LLM providers with automatic fallback on quota errors.
    Priority: Groq > Gemini > HuggingFace > OpenAI

    Returns:
        Configured LLMClient instance (with fallback support).

    Raises:
        UserApiServiceError: If no LLM API keys are configured.
    """
    from src.clients.llm import FallbackLLMClient

    # Collect all available API keys
    groq_api_key = os.getenv("GROQ_API_KEY")
    gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY")
    hf_api_key = os.getenv("HF_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    # Collect model settings (optional, will use defaults if not set)
    groq_model = os.getenv("GROQ_MODEL")
    gemini_model = os.getenv("GEMINI_MODEL")
    hf_model = os.getenv("HF_MODEL")
    openai_model = os.getenv("OPENAI_MODEL")

    # Check if at least one key is available
    if not any([groq_api_key, gemini_api_key, hf_api_key, openai_api_key]):
        raise UserApiServiceError(
            "서버 LLM API 키가 설정되지 않았습니다. 관리자에게 문의하세요."
        )

    # Create fallback client with all available providers
    fallback_client = FallbackLLMClient.from_api_keys(
        groq_api_key=groq_api_key,
        gemini_api_key=gemini_api_key,
        hf_api_key=hf_api_key,
        openai_api_key=openai_api_key,
        groq_model=groq_model,
        gemini_model=gemini_model,
        hf_model=hf_model,
        openai_model=openai_model,
    )

    # Wrap in LLMClient for compatibility
    return LLMClient(fallback_client)


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
