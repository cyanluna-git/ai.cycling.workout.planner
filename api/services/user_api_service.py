"""User API Service.

This module handles retrieval of user-specific API keys and creates
configured clients for LLM and Intervals.icu integration.
"""

import os
import json
import logging
from typing import Optional
from dataclasses import dataclass
from datetime import date

from src.clients.supabase_client import get_supabase_admin_client
from src.clients.intervals import IntervalsClient
from src.clients.llm import LLMClient
from src.config import IntervalsConfig, LLMConfig, UserProfile
from src.services.data_processor import DataProcessor
from api.schemas import GeneratedWorkout

logger = logging.getLogger(__name__)


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
    exclude_barcode_workouts: bool = False


class UserApiServiceError(Exception):
    """Exception for user API service errors."""

    pass


class RateLimitExceededError(UserApiServiceError):
    """Exception raised when user exceeds daily rate limit."""

    pass


async def check_rate_limit(user_id: str, limit: int = 5) -> bool:
    """Check if user has exceeded daily workout generation limit.

    Args:
        user_id: The user's unique ID.
        limit: Max workouts per day (default 5).

    Raises:
        RateLimitExceededError: If limit exceeded.
    """
    try:
        supabase = get_supabase_admin_client()
        today = date.today().isoformat()

        result = (
            supabase.table("workout_usage")
            .select("generation_count")
            .eq("user_id", user_id)
            .eq("usage_date", today)
            .maybe_single()
            .execute()
        )

        data = result.data

        if data and data.get("generation_count", 0) >= limit:
            raise RateLimitExceededError(
                f"일일 워크아웃 생성 한도({limit}회)를 초과했습니다. 내일 다시 시도해주세요."
            )
    except RateLimitExceededError:
        raise
    except Exception as e:
        # If workout_usage table doesn't exist or query fails, skip rate limiting
        logger.warning(f"Rate limit check failed for user {user_id}, skipping: {e}")
        logger.info("Continuing without rate limit check (table may not exist)")

    return True


async def increment_usage(user_id: str) -> None:
    """Increment user's daily workout generation count.

    Args:
        user_id: The user's unique ID.
    """
    try:
        supabase = get_supabase_admin_client()
        today = date.today().isoformat()

        # Use RPC for atomic upsert/increment
        supabase.rpc(
            "increment_workout_usage", {"p_user_id": user_id, "p_date": today}
        ).execute()
    except Exception as e:
        # If workout_usage table or RPC function doesn't exist, skip
        logger.warning(f"Failed to increment usage for user {user_id}: {e}")
        logger.info("Continuing without usage tracking")


async def get_user_api_keys(user_id: str) -> UserApiKeysData:
    """Retrieve user's API keys from database.

    Args:
        user_id: The user's unique ID.

    Returns:
        UserApiKeysData with the user's stored API keys.

    Raises:
        UserApiServiceError: If API keys are not configured.
    """
    logger.info(f"Fetching API keys for user_id: {user_id}")
    supabase = get_supabase_admin_client()

    try:
        result = (
            supabase.table("user_api_keys")
            .select("intervals_api_key, athlete_id")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )

        logger.debug(f"Supabase query result: {result}")
        data = result.data if result else None
        logger.debug(f"Extracted data: {data}")

        if not data:
            logger.warning(f"No API keys found for user {user_id}")
            raise UserApiServiceError(
                "⚠️ Intervals.icu API 키가 설정되지 않았습니다.\n"
                "설정 페이지에서 Athlete ID와 API Key를 입력해주세요.\n"
                "온보딩을 완료하지 않으셨다면 새로고침 후 다시 진행해주세요."
            )

        logger.info(f"Successfully retrieved API keys for user {user_id}")
        return UserApiKeysData(
            intervals_api_key=data.get("intervals_api_key"),
            athlete_id=data.get("athlete_id"),
        )
    except UserApiServiceError:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error fetching API keys for user {user_id}")
        raise UserApiServiceError(f"API 키 조회 중 오류가 발생했습니다: {str(e)}")


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
        .select("ftp, max_hr, lthr, training_goal, exclude_barcode_workouts")
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
        exclude_barcode_workouts=data.get("exclude_barcode_workouts", False),
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

    Prioritizes Vercel AI Gateway if configured, otherwise falls back to
    direct API calls with automatic fallback on quota errors.
    Models are loaded from database (llm_models table).

    Returns:
        Configured LLMClient instance (with fallback support).

    Raises:
        UserApiServiceError: If no LLM API keys are configured.
    """
    from src.clients.llm import FallbackLLMClient, VercelGatewayClient
    from api.services.model_service import get_active_models

    # Check for Vercel AI Gateway first (recommended)
    vercel_gateway_key = os.getenv("VERCEL_AI_GATEWAY_API_KEY")
    if vercel_gateway_key:
        # Use Groq as primary for faster inference speed
        logger.info("Using Vercel AI Gateway for LLM calls (Groq primary, Gemini fallback)")
        gateway_client = VercelGatewayClient(
            api_key=vercel_gateway_key,
            model="groq/llama-3.3-70b-versatile",  # Groq as primary
            fallback_models=[
                "google/gemini-2.0-flash",  # Gemini as fallback
                "google/gemini-1.5-flash",
            ],
        )
        return LLMClient(gateway_client)

    # Fallback to direct API calls if Vercel Gateway not configured
    logger.info("Vercel AI Gateway not configured, using direct API calls")

    # Collect all available API keys
    groq_api_key = os.getenv("GROQ_API_KEY")
    gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY")
    hf_api_key = os.getenv("HF_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    # Check if at least one key is available
    if not any([groq_api_key, gemini_api_key, hf_api_key, openai_api_key]):
        raise UserApiServiceError(
            "서버 LLM API 키가 설정되지 않았습니다. 관리자에게 문의하세요."
        )

    # Get models from database (sorted by priority)
    db_models = get_active_models()

    # Group models by provider, take highest priority model for each
    provider_models: dict[str, str] = {}
    for model in db_models:
        if model.provider not in provider_models:
            provider_models[model.provider] = model.model_id

    # Create fallback client with all available providers
    fallback_client = FallbackLLMClient.from_api_keys(
        groq_api_key=groq_api_key,
        gemini_api_key=gemini_api_key,
        hf_api_key=hf_api_key,
        openai_api_key=openai_api_key,
        groq_model=provider_models.get("groq") or os.getenv("GROQ_MODEL"),
        gemini_model=provider_models.get("gemini") or os.getenv("GEMINI_MODEL"),
        hf_model=provider_models.get("huggingface") or os.getenv("HF_MODEL"),
        openai_model=provider_models.get("openai") or os.getenv("OPENAI_MODEL"),
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
        exclude_barcode_workouts=settings.exclude_barcode_workouts,
    )


def get_data_processor() -> DataProcessor:
    """Get a DataProcessor instance.

    Returns:
        DataProcessor instance for processing training data.
    """
    return DataProcessor()


async def save_workout(user_id: str, workout_data: dict) -> dict:
    """Save generated workout to Supabase.

    Args:
        user_id: User ID.
        workout_data: Workout data dictionary.

    Returns:
        Saved workout data.
    """
    supabase = get_supabase_admin_client()

    data = {
        "user_id": user_id,
        "name": workout_data.get("name"),
        "workout_date": workout_data.get("target_date"),
        "workout_text": workout_data.get("workout_text"),
        "design_goal": workout_data.get("design_goal"),
        "workout_type": workout_data.get("workout_type"),
        "estimated_tss": workout_data.get("estimated_tss"),
        "duration_minutes": workout_data.get("duration_minutes"),
        "intervals_event_id": workout_data.get("event_id"),
        "updated_at": date.today().isoformat(),
    }

    # Save structured steps as JSON if present
    steps_data = workout_data.get("steps")
    if steps_data:
        data["steps_json"] = json.dumps(steps_data)

    # Save ZWO content if present
    zwo_content = workout_data.get("zwo_content")
    if zwo_content:
        data["zwo_content"] = zwo_content

    # Upsert based on user_id and workout_date to prevent duplicates for the same day
    try:
        result = (
            supabase.table("saved_workouts")
            .upsert(data, on_conflict="user_id, workout_date")
            .execute()
        )
        return result.data[0] if result.data else {}
    except Exception as e:
        # If columns don't exist, try without them
        if "steps_json" in str(e) or "zwo_content" in str(e):
            logger.warning("New columns not found, saving without steps/zwo")
            data.pop("steps_json", None)
            data.pop("zwo_content", None)
            result = (
                supabase.table("saved_workouts")
                .upsert(data, on_conflict="user_id, workout_date")
                .execute()
            )
            return result.data[0] if result.data else {}
        raise


def _select_best_workout(workout_events: list) -> Optional[dict]:
    """Select the best workout from multiple options.

    Priority:
    1. AI Coach generated workouts ([AICoach] or AI Generated in name)
    2. Most recently updated

    Args:
        workout_events: List of WORKOUT category events

    Returns:
        Selected workout event, or None if list is empty
    """
    if not workout_events:
        return None

    # Separate AI Coach workouts from others
    ai_workouts = []
    other_workouts = []

    for event in workout_events:
        name = event.get("name", "")
        # Check if it's from AI Coach
        if "[AICoach]" in name or "AI Generated" in name:
            ai_workouts.append(event)
        else:
            other_workouts.append(event)

    # Prefer AI Coach workouts
    candidates = ai_workouts if ai_workouts else other_workouts

    # Sort by updated timestamp (most recent first)
    candidates.sort(
        key=lambda x: x.get("updated", ""), reverse=True
    )

    selected = candidates[0]

    # Log selection if multiple options
    if len(workout_events) > 1:
        logger.info(
            f"Multiple workouts found ({len(workout_events)}), "
            f"selected: {selected.get('name')} (AI Coach: {selected in ai_workouts})"
        )

    return selected


async def get_todays_workout(
    user_id: str, target_date: str = None
) -> Optional[GeneratedWorkout]:
    """Get workout directly from Intervals.icu (Single Source of Truth).

    Args:
        user_id: User ID.
        target_date: Date string (YYYY-MM-DD), defaults to today.

    Returns:
        GeneratedWorkout object or None.
    """
    if not target_date:
        target_date = date.today().isoformat()

    try:
        # Get Intervals client for this user
        intervals = await get_user_intervals_client(user_id)

        # Fetch events for the target date
        events = intervals.get_events(target_date, target_date)

        # Filter for WORKOUT category only (exclude ACTIVITY, NOTE, etc.)
        workout_events = [e for e in events if e.get("category") == "WORKOUT"]

        if not workout_events:
            logger.info(f"No workout found on Intervals.icu for {target_date}")
            return None

        # Select workout with priority:
        # 1. AI Coach generated workouts ([AICoach] or AI Generated)
        # 2. Most recently updated
        workout_event = _select_best_workout(workout_events)

        if not workout_event:
            logger.info(f"No suitable workout found for {target_date}")
            return None

        # Parse workout_doc from Intervals.icu
        from src.services.intervals_parser import (
            parse_workout_doc_steps,
            extract_workout_sections,
        )

        workout_doc = workout_event.get("workout_doc")
        steps = parse_workout_doc_steps(workout_doc) if workout_doc else []

        # Extract workout sections for display
        warmup_steps, main_steps, cooldown_steps = extract_workout_sections(steps)

        # Create GeneratedWorkout from Intervals data
        return GeneratedWorkout(
            name=workout_event.get("name", "Workout"),
            workout_type=workout_event.get("type", "Ride"),
            estimated_tss=workout_event.get("icu_training_load"),
            estimated_duration_minutes=workout_event.get("moving_time", 0) // 60,
            workout_text=workout_event.get("description", ""),
            design_goal=None,  # Not stored in Intervals
            steps=steps,
            warmup=warmup_steps,
            main=main_steps,
            cooldown=cooldown_steps,
            zwo_content=None,  # Can regenerate if needed
        )

    except Exception as e:
        logger.exception(f"Error fetching workout from Intervals.icu for {target_date}")
        # Don't fall back to local DB - Intervals.icu is single source of truth
        return None


async def sync_workout_from_intervals(user_id: str, event: dict) -> None:
    """Sync a workout event from Intervals.icu to local DB.

    Preserves existing metadata (design_goal) if the workout already exists.
    """
    supabase = get_supabase_admin_client()
    target_date = event["start_date_local"][:10]

    # Check if exists
    existing = (
        supabase.table("saved_workouts")
        .select("design_goal, workout_type")
        .eq("user_id", user_id)
        .eq("workout_date", target_date)
        .maybe_single()
        .execute()
    )

    existing_data = existing.data if existing else None

    # Prepare data
    description = event.get("description", "") or ""
    moving_time = event.get("moving_time", 0)

    data = {
        "user_id": user_id,
        "name": event.get("name"),
        "workout_date": target_date,
        "workout_text": description,
        "estimated_tss": event.get("icu_training_load"),
        "duration_minutes": moving_time // 60 if moving_time else 0,
        "intervals_event_id": event.get("id"),
        "updated_at": date.today().isoformat(),
    }

    # Preserve or set default metadata
    if existing_data:
        data["design_goal"] = existing_data.get("design_goal")
        # Only overwrite type if not set in DB, or update if we want (kept simple here)
        data["workout_type"] = existing_data.get("workout_type") or event.get(
            "type", "Ride"
        )
    else:
        # New sync
        data["design_goal"] = None  # No AI goal for external workouts
        data["workout_type"] = event.get("type", "Ride")

    # Upsert
    try:
        supabase.table("saved_workouts").upsert(
            data, on_conflict="user_id, workout_date"
        ).execute()
    except Exception as e:
        logger.error(f"Failed to sync workout {event.get('id')}: {e}")


async def cleanup_stale_workouts(
    user_id: str, week_start: str, week_end: str, valid_event_ids: list
) -> int:
    """Remove workouts from local DB that no longer exist in Intervals.icu.

    Args:
        user_id: User ID.
        week_start: Start of week (YYYY-MM-DD).
        week_end: End of week (YYYY-MM-DD).
        valid_event_ids: List of event IDs that exist in Intervals.icu.

    Returns:
        Number of deleted workouts.
    """
    supabase = get_supabase_admin_client()

    try:
        # Get all local workouts for this week
        result = (
            supabase.table("saved_workouts")
            .select("id, intervals_event_id, workout_date")
            .eq("user_id", user_id)
            .gte("workout_date", week_start)
            .lte("workout_date", week_end)
            .execute()
        )

        if not result.data:
            return 0

        # Find workouts that are not in the valid event IDs
        deleted_count = 0
        for workout in result.data:
            event_id = workout.get("intervals_event_id")
            # Skip if no event ID (manually created, not synced)
            if not event_id:
                continue

            # Delete if event ID not in valid list
            if str(event_id) not in [str(eid) for eid in valid_event_ids]:
                logger.info(
                    f"Deleting stale workout {workout['id']} (event {event_id}) for user {user_id}"
                )
                supabase.table("saved_workouts").delete().eq(
                    "id", workout["id"]
                ).execute()
                deleted_count += 1

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} stale workouts for user {user_id}")

        return deleted_count

    except Exception as e:
        logger.error(f"Failed to cleanup stale workouts for user {user_id}: {e}")
        return 0
