"""Helpers for recent recommendation history."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

logger = logging.getLogger(__name__)


def get_recent_profile_ids(
    supabase: Any,
    user_id: str,
    *,
    recent_days: int = 14,
    limit: int = 6,
) -> list[int]:
    """Return recent unique profile IDs for a user, newest first."""
    if limit <= 0:
        return []

    since = (date.today() - timedelta(days=max(recent_days, 1))).isoformat()
    try:
        result = (
            supabase.table("daily_workouts")
            .select("profile_id, workout_date")
            .eq("user_id", user_id)
            .not_.is_("profile_id", "null")
            .gte("workout_date", since)
            .order("workout_date", desc=True)
            .limit(max(limit * 4, 12))
            .execute()
        )
    except Exception as exc:
        logger.warning("Failed to fetch recent profile history for %s: %s", user_id, exc)
        return []

    rows = result.data if result and result.data else []
    recent_profile_ids: list[int] = []
    seen: set[int] = set()
    for row in rows:
        profile_id = row.get("profile_id")
        if profile_id is None:
            continue
        try:
            normalized = int(profile_id)
        except (TypeError, ValueError):
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        recent_profile_ids.append(normalized)
        if len(recent_profile_ids) >= limit:
            break

    return recent_profile_ids
