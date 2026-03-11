"""Tests for shared fitness snapshot orchestration."""

import asyncio
import sys
import types
from types import SimpleNamespace
from unittest.mock import AsyncMock

from api.schemas import WorkoutGenerateRequest
from api.services.fitness_snapshot_service import (
    FitnessSnapshot,
    get_fitness_snapshot,
)
from src.config import UserProfile
from src.services.data_processor import TrainingMetrics, WellnessMetrics

fake_supabase = types.ModuleType("supabase")
fake_supabase.create_client = lambda *args, **kwargs: None
fake_supabase.Client = object
sys.modules.setdefault("supabase", fake_supabase)


def test_get_fitness_snapshot_reuses_cache(monkeypatch):
    cache = {}
    fetch_calls = []

    monkeypatch.setattr(
        "api.services.fitness_snapshot_service.get_cached",
        lambda user_id, key: cache.get((user_id, key)),
    )
    monkeypatch.setattr(
        "api.services.fitness_snapshot_service.set_cached",
        lambda user_id, key, value: cache.__setitem__((user_id, key), value),
    )
    monkeypatch.setattr(
        "api.services.fitness_snapshot_service._fetch_recent_activities",
        lambda config, days: fetch_calls.append(("activities", days))
        or [
            {
                "start_date_local": "2026-03-07T06:00:00",
                "training_load": 65,
                "icu_ctl": 72,
                "icu_atl": 80,
            }
        ],
    )
    monkeypatch.setattr(
        "api.services.fitness_snapshot_service._fetch_recent_wellness",
        lambda config, days: fetch_calls.append(("wellness", days))
        or [{"id": "2026-03-07", "readiness": "Ready"}],
    )

    class StubProcessor:
        def __init__(self):
            self.training_calls = 0
            self.wellness_calls = 0
            self.history_calls = 0

        def calculate_training_metrics(self, activities):
            self.training_calls += 1
            return TrainingMetrics(ctl=72, atl=80, tsb=-8)

        def analyze_wellness(self, wellness_entries, activities=None):
            self.wellness_calls += 1
            assert activities is not None
            return WellnessMetrics(
                hrv=None,
                hrv_sdnn=None,
                rhr=None,
                sleep_hours=None,
                sleep_score=None,
                sleep_quality=None,
                readiness="Ready",
                weight=None,
                body_fat=None,
                vo2max=None,
                soreness=None,
                fatigue=None,
                stress=None,
                mood=None,
                motivation=None,
                spo2=None,
                systolic=None,
                diastolic=None,
                respiration=None,
                readiness_score=None,
                active_calories_load=512.4,
                active_calories_history=[
                    {
                        "date": "2026-03-01",
                        "active_calories_load": 480.0,
                    },
                    {
                        "date": "2026-03-07",
                        "active_calories_load": 512.4,
                    },
                ],
            )

        def calculate_ctl_history(self, activities, days=7):
            self.history_calls += 1
            return [{"date": "2026-03-07", "ctl": 72.0, "atl": 80.0, "tsb": -8.0}]

    processor = StubProcessor()
    client = SimpleNamespace(config=object())

    first = asyncio.run(
        get_fitness_snapshot("user-1", client, processor=processor)
    )
    second = asyncio.run(
        get_fitness_snapshot("user-1", client, processor=processor)
    )

    assert first is second
    assert fetch_calls == [("activities", 42), ("wellness", 28)]
    assert processor.training_calls == 1
    assert processor.wellness_calls == 1
    assert processor.history_calls == 1


def test_generate_workout_uses_shared_snapshot_instead_of_raw_fetch(monkeypatch):
    import api.routers.workout as workout_mod

    class DummyIntervalsClient:
        def get_recent_activities(self, days=42):
            raise AssertionError("route should use shared fitness snapshot")

        def get_recent_wellness(self, days=28):
            raise AssertionError("route should use shared fitness snapshot")

    async def fake_snapshot(user_id, intervals, processor=None, refresh=False):
        return FitnessSnapshot(
            activities=[
                {
                    "start_date_local": "2026-03-07T06:00:00",
                    "training_load": 55,
                    "icu_ctl": 70,
                    "icu_atl": 76,
                }
            ],
            wellness_entries=[{"id": "2026-03-07", "readiness": "Ready"}],
            training_metrics=TrainingMetrics(ctl=70, atl=76, tsb=-6),
            wellness_metrics=WellnessMetrics(
                hrv=None,
                hrv_sdnn=None,
                rhr=None,
                sleep_hours=None,
                sleep_score=None,
                sleep_quality=None,
                readiness="Ready",
                weight=None,
                body_fat=None,
                vo2max=None,
                soreness=None,
                fatigue=None,
                stress=None,
                mood=None,
                motivation=None,
                spo2=None,
                systolic=None,
                diastolic=None,
                respiration=None,
                readiness_score=None,
                active_calories_load=480.0,
                active_calories_history=[
                    {
                        "date": "2026-03-07",
                        "active_calories_load": 480.0,
                    }
                ],
            ),
            ctl_history=[{"date": "2026-03-07", "ctl": 70.0, "atl": 76.0, "tsb": -6.0}],
        )

    class FakeGenerator:
        def __init__(self, llm, user_profile, max_duration_minutes):
            self.max_duration_minutes = max_duration_minutes

        def generate_enhanced(
            self,
            training_metrics,
            wellness_metrics,
            target_date,
            **kwargs,
        ):
            return SimpleNamespace(
                name="Snapshot Workout",
                workout_type="endurance",
                design_goal="Reuse cached fitness snapshot",
                coaching=None,
                estimated_tss=58,
                estimated_duration_minutes=self.max_duration_minutes,
                workout_text="Warmup\n- 10m 50%\n\nMain\n- 20m 75%\n\nCooldown\n- 10m 50%",
                steps=None,
            )

    monkeypatch.setattr(workout_mod, "check_rate_limit", AsyncMock())
    monkeypatch.setattr(
        workout_mod,
        "get_user_intervals_client",
        AsyncMock(return_value=DummyIntervalsClient()),
    )
    monkeypatch.setattr(workout_mod, "get_server_llm_client", lambda: object())
    monkeypatch.setattr(
        workout_mod,
        "get_user_profile",
        AsyncMock(
            return_value=UserProfile(
                ftp=250,
                max_hr=190,
                lthr=170,
                training_goal="Build fitness",
            )
        ),
    )
    monkeypatch.setattr(workout_mod, "get_data_processor", lambda: object())
    monkeypatch.setattr(workout_mod, "get_fitness_snapshot", fake_snapshot)
    monkeypatch.setattr(workout_mod, "get_recent_profile_ids", lambda *args: [])
    monkeypatch.setattr(
        "src.clients.supabase_client.get_supabase_admin_client",
        lambda: object(),
    )
    monkeypatch.setattr(workout_mod, "increment_usage", AsyncMock())
    monkeypatch.setattr(workout_mod, "log_audit_event", AsyncMock())
    monkeypatch.setattr(workout_mod, "WorkoutGenerator", FakeGenerator)

    response = asyncio.run(
        workout_mod.generate_workout(
            WorkoutGenerateRequest(duration=40),
            user={"id": "user-1", "email": "u@example.com"},
        )
    )

    assert response.success is True
    assert response.workout.name == "Snapshot Workout"
    assert response.workout.estimated_tss == 58
