"""Performance-oriented regression guards for recommendation internals."""

from types import SimpleNamespace
from pathlib import Path
from tempfile import mktemp

from api.services.workout_profile_service import WorkoutProfileService
from src.services.module_usage_tracker import ModuleUsageTracker


class _FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.executed_query = None
        self.executed_params = None

    def execute(self, query, params):
        self.executed_query = query
        self.executed_params = params

    def fetchall(self):
        return self.rows


class _FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor

    def close(self):
        return None


def test_profile_candidates_avoid_order_by_random(monkeypatch):
    rows = [
        {
            "id": idx,
            "name": f"Profile {idx}",
            "category": "threshold",
            "target_zone": "SST",
            "duration_minutes": 60,
            "estimated_tss": 70,
            "difficulty": "intermediate",
            "steps_json": None,
            "coach_notes": None,
            "tags": None,
        }
        for idx in range(1, 9)
    ]
    cursor = _FakeCursor(rows)
    service = WorkoutProfileService(db_path="does-not-matter.db")

    monkeypatch.setattr(service, "db_path", SimpleNamespace(exists=lambda: True))
    monkeypatch.setattr(service, "_get_connection", lambda: _FakeConnection(cursor))
    monkeypatch.setattr(
        service,
        "_sample_candidates",
        lambda profiles, limit: profiles[:limit],
    )

    candidates = service.get_candidates(
        categories=["threshold"],
        duration_range=(45, 75),
        difficulty_max="intermediate",
        limit=3,
    )

    assert len(candidates) == 3
    assert "ORDER BY RANDOM()" not in cursor.executed_query
    assert "ORDER BY id DESC LIMIT ?" in cursor.executed_query
    assert cursor.executed_params[-1] > 3


def test_module_usage_tracking_buffers_disk_writes(monkeypatch):
    tracker = ModuleUsageTracker(
        stats_file=Path(mktemp()),
        flush_every=5,
        flush_interval_seconds=3600,
    )
    writes = []

    monkeypatch.setattr(
        tracker,
        "_write_stats_file",
        lambda data: writes.append(data["total_selections"]),
    )

    tracker.record_selection(["module_a"], categories={"module_a": "main"})
    tracker.record_selection(["module_b"], categories={"module_b": "main"})
    tracker.record_selection(["module_a"], categories={"module_a": "main"})

    # In-memory weights update immediately without forcing disk persistence.
    weights = tracker.calculate_priority_weights(
        ["module_a", "module_b", "module_c"],
        category="main",
    )

    assert tracker.get_module_stats("module_a")["count"] == 2
    assert writes == []
    assert weights["module_c"] > weights["module_b"] > weights["module_a"]

    tracker.flush()

    assert writes == [3]
