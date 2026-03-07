"""Shared fitness snapshot service for recommendation and fitness routes."""

import asyncio
from dataclasses import dataclass

from api.schemas import AthleteProfile
from api.services.cache_service import get_cached, set_cached
from src.clients.intervals import IntervalsClient
from src.services.data_processor import DataProcessor, TrainingMetrics, WellnessMetrics

FITNESS_SNAPSHOT_CACHE_KEY = "fitness:snapshot"
FITNESS_PROFILE_CACHE_KEY = "fitness:profile"
ACTIVITY_LOOKBACK_DAYS = 42
WELLNESS_LOOKBACK_DAYS = 28
CTL_HISTORY_DAYS = 7


@dataclass
class FitnessSnapshot:
    """Raw and derived fitness data shared by multiple endpoints."""

    activities: list[dict]
    wellness_entries: list[dict]
    training_metrics: TrainingMetrics
    wellness_metrics: WellnessMetrics
    ctl_history: list[dict]


def _fetch_recent_activities(config, days: int) -> list[dict]:
    client = IntervalsClient(config)
    try:
        return client.get_recent_activities(days=days)
    finally:
        client.session.close()


def _fetch_recent_wellness(config, days: int) -> list[dict]:
    client = IntervalsClient(config)
    try:
        return client.get_recent_wellness(days=days)
    finally:
        client.session.close()


def _fetch_athlete_profile(config) -> dict:
    client = IntervalsClient(config)
    try:
        return client.get_athlete_profile()
    finally:
        client.session.close()


def build_athlete_profile(athlete_data: dict) -> AthleteProfile:
    """Convert Intervals athlete payload to the API profile shape."""
    sport_settings = athlete_data.get("sportSettings", [])
    ride_settings = next(
        (s for s in sport_settings if "Ride" in s.get("types", [])),
        sport_settings[0] if sport_settings else {},
    )

    ftp = ride_settings.get("ftp")
    lthr = ride_settings.get("lthr")
    max_hr = ride_settings.get("max_hr")
    weight = athlete_data.get("icu_weight")

    mmp_model = ride_settings.get("mmp_model", {}) or {}
    vo2max_estimate = mmp_model.get("vo2max") if mmp_model else None
    w_per_kg = round(ftp / weight, 2) if ftp and weight else None

    return AthleteProfile(
        ftp=ftp,
        max_hr=max_hr,
        lthr=lthr,
        weight=weight,
        w_per_kg=w_per_kg,
        vo2max=vo2max_estimate,
    )


async def get_fitness_snapshot(
    user_id: str,
    intervals_client: IntervalsClient,
    *,
    refresh: bool = False,
    processor: DataProcessor | None = None,
) -> FitnessSnapshot:
    """Fetch and cache the shared training/wellness snapshot."""
    if not refresh:
        cached = get_cached(user_id, FITNESS_SNAPSHOT_CACHE_KEY)
        if cached:
            return cached

    processor = processor or DataProcessor()

    activities, wellness_entries = await asyncio.gather(
        asyncio.to_thread(
            _fetch_recent_activities,
            intervals_client.config,
            ACTIVITY_LOOKBACK_DAYS,
        ),
        asyncio.to_thread(
            _fetch_recent_wellness,
            intervals_client.config,
            WELLNESS_LOOKBACK_DAYS,
        ),
    )

    snapshot = FitnessSnapshot(
        activities=activities,
        wellness_entries=wellness_entries,
        training_metrics=processor.calculate_training_metrics(activities),
        wellness_metrics=processor.analyze_wellness(wellness_entries),
        ctl_history=processor.calculate_ctl_history(activities, days=CTL_HISTORY_DAYS),
    )
    set_cached(user_id, FITNESS_SNAPSHOT_CACHE_KEY, snapshot)
    return snapshot


async def get_cached_athlete_profile(
    user_id: str,
    intervals_client: IntervalsClient,
    *,
    refresh: bool = False,
) -> AthleteProfile:
    """Fetch and cache the lightweight athlete profile used by `/fitness`."""
    if not refresh:
        cached = get_cached(user_id, FITNESS_PROFILE_CACHE_KEY)
        if cached:
            return cached

    athlete_data = await asyncio.to_thread(
        _fetch_athlete_profile,
        intervals_client.config,
    )
    profile = build_athlete_profile(athlete_data)
    set_cached(user_id, FITNESS_PROFILE_CACHE_KEY, profile)
    return profile
