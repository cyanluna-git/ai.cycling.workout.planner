"""Tests for module usage tracker balance features.

Tests the get_balance_hints() and calculate_priority_weights() methods
that ensure even distribution of module selection.
"""

import pytest
import json
import tempfile
from pathlib import Path

from src.services.module_usage_tracker import ModuleUsageTracker


@pytest.fixture
def tracker_with_data():
    """Create a tracker with pre-populated usage data."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        # Pre-populate with sample usage data
        data = {
            "total_selections": 10,
            "modules": {
                "sst_10min": {"count": 5, "last_used": "2026-01-09T10:00:00"},
                "vo2_3x3": {"count": 3, "last_used": "2026-01-09T11:00:00"},
                "threshold_2x8": {"count": 1, "last_used": "2026-01-08T10:00:00"},
                "endurance_20min": {"count": 0, "last_used": None},
                "ramp_standard": {"count": 8, "last_used": "2026-01-09T12:00:00"},
                "flush_and_fade": {"count": 8, "last_used": "2026-01-09T12:00:00"},
            },
            "by_category": {
                "warmup": {"ramp_standard": 8},
                "main": {"sst_10min": 5, "vo2_3x3": 3, "threshold_2x8": 1},
                "rest": {},
                "cooldown": {"flush_and_fade": 8},
            },
        }
        json.dump(data, f)
        stats_path = Path(f.name)

    tracker = ModuleUsageTracker(stats_file=stats_path)
    yield tracker

    # Cleanup
    if stats_path.exists():
        stats_path.unlink()


@pytest.fixture
def empty_tracker():
    """Create a tracker with no usage data."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        stats_path = Path(f.name)
        # Don't write anything - tracker will create default empty stats

    # Remove the file so tracker starts fresh
    stats_path.unlink()

    tracker = ModuleUsageTracker(stats_file=stats_path)
    yield tracker

    # Cleanup (file may not exist if tracker didn't save)
    if stats_path.exists():
        stats_path.unlink()


class TestGetBalanceHints:
    """Tests for get_balance_hints method."""

    def test_returns_hints_for_underused_modules(self, tracker_with_data):
        """Should identify least-used modules in each category."""
        available = {
            "main": ["sst_10min", "vo2_3x3", "threshold_2x8", "endurance_20min"],
            "warmup": ["ramp_standard", "ramp_short"],
            "cooldown": ["flush_and_fade", "fade_out_5min"],
        }

        hints = tracker_with_data.get_balance_hints(available, top_n=2)

        # Should contain suggestions for underused modules
        assert "MAIN" in hints
        # endurance_20min (0 uses) and threshold_2x8 (1 use) should be recommended
        assert "endurance_20min" in hints or "threshold_2x8" in hints

    def test_returns_hints_for_zero_usage_modules(self, empty_tracker):
        """When no usage data exists, all modules have 0 uses and are recommended."""
        available = {
            "main": ["sst_10min", "vo2_3x3"],
        }

        hints = empty_tracker.get_balance_hints(available, top_n=2)

        # All modules are equally "underused" (0 uses) so they get recommended
        assert "MAIN" in hints
        assert "sst_10min" in hints or "vo2_3x3" in hints

    def test_handles_empty_category(self, tracker_with_data):
        """Should handle categories with no modules gracefully."""
        available = {
            "main": [],
            "rest": ["rest_short"],
        }

        hints = tracker_with_data.get_balance_hints(available, top_n=2)

        # Should not crash and should handle empty main category
        assert isinstance(hints, str)


class TestCalculatePriorityWeights:
    """Tests for calculate_priority_weights method."""

    def test_higher_weight_for_less_used(self, tracker_with_data):
        """Less frequently used modules should have higher weights."""
        modules = ["sst_10min", "threshold_2x8", "endurance_20min"]

        weights = tracker_with_data.calculate_priority_weights(modules, category="main")

        # endurance_20min (0 uses) should have highest weight
        # sst_10min (5 uses) should have lowest weight
        assert weights["endurance_20min"] > weights["threshold_2x8"]
        assert weights["threshold_2x8"] > weights["sst_10min"]

    def test_equal_weights_for_no_usage(self, empty_tracker):
        """All modules should have equal weight when no usage data exists."""
        modules = ["sst_10min", "vo2_3x3", "threshold_2x8"]

        weights = empty_tracker.calculate_priority_weights(modules, category="main")

        # All should be 1.0 (equal)
        assert all(w == 1.0 for w in weights.values())

    def test_weight_range(self, tracker_with_data):
        """Weights should be within expected range (0.5 to 2.0)."""
        modules = ["sst_10min", "threshold_2x8", "endurance_20min"]

        weights = tracker_with_data.calculate_priority_weights(modules, category="main")

        for weight in weights.values():
            assert 0.5 <= weight <= 2.0

    def test_empty_module_list(self, tracker_with_data):
        """Should return empty dict for empty module list."""
        weights = tracker_with_data.calculate_priority_weights([])

        assert weights == {}
