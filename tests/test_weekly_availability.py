"""Unit tests for weekly availability feature."""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.weekly_plan_service import (
    WeeklyPlanGenerator,
    DAILY_TSS_RATIOS,
    DEFAULT_AVAILABILITY,
)


class MockLLM:
    def generate(self, system_prompt, user_prompt):
        return "[]"


def make_generator(profile=None):
    return WeeklyPlanGenerator(MockLLM(), profile or {})


# --- TSS prediction tests ---


def test_predict_tss_with_unavailable_days():
    """Unavailable days get TSS=0, rest redistributed."""
    gen = make_generator()
    result = gen._predict_daily_tss_with_availability(
        weekly_tss_target=500,
        training_style="sweetspot",
        available_days=[1, 2, 3, 5, 6],
        unavailable_days=[0, 4],
    )
    assert result[0] == 0
    assert result[4] == 0
    assert all(result[d] > 0 for d in [1, 2, 3, 5, 6])
    assert sum(result.values()) <= 510  # Rough check


def test_predict_tss_all_available():
    """All available matches original behavior."""
    gen = make_generator()
    result = gen._predict_daily_tss_with_availability(
        weekly_tss_target=500,
        training_style="sweetspot",
        available_days=list(range(7)),
        unavailable_days=[],
    )
    assert len(result) == 7
    assert sum(result.values()) > 0


def test_predict_tss_only_3days_available():
    """Only 3 days available - all TSS goes to those days."""
    gen = make_generator()
    result = gen._predict_daily_tss_with_availability(
        weekly_tss_target=400,
        training_style="polarized",
        available_days=[1, 5, 6],
        unavailable_days=[0, 2, 3, 4],
    )
    assert result[0] == 0
    assert result[2] == 0
    assert result[3] == 0
    assert result[4] == 0
    total = result[1] + result[5] + result[6]
    assert total > 0


def test_predict_tss_respects_individual_caps():
    """TSS caps: 150 normal, 180 endurance weekends."""
    gen = make_generator()
    # High TSS with few available days should trigger caps
    result = gen._predict_daily_tss_with_availability(
        weekly_tss_target=700,
        training_style="endurance",
        available_days=[5, 6],
        unavailable_days=[0, 1, 2, 3, 4],
    )
    assert result[5] <= 180
    assert result[6] <= 180

    result2 = gen._predict_daily_tss_with_availability(
        weekly_tss_target=700,
        training_style="sweetspot",
        available_days=[5, 6],
        unavailable_days=[0, 1, 2, 3, 4],
    )
    assert result2[5] <= 150
    assert result2[6] <= 150


def test_all_days_unavailable_raises_error():
    """All days unavailable raises ValueError."""
    gen = make_generator()
    # All ratios are 0 for rest days (day 0 and 4 in sweetspot have 0 ratio)
    # But if available_days is empty, total_ratio will be 0
    with pytest.raises(ValueError, match="At least one day"):
        gen._predict_daily_tss_with_availability(
            weekly_tss_target=500,
            training_style="sweetspot",
            available_days=[],
            unavailable_days=list(range(7)),
        )


# --- Prompt formatting tests ---


def test_format_availability_for_prompt():
    """Basic prompt text generation."""
    gen = make_generator()
    avail = {"0": "available", "1": "unavailable", "2": "rest",
             "3": "available", "4": "available", "5": "available", "6": "available"}
    text = gen._format_availability_for_prompt(avail)
    assert "Monday" in text
    assert "UNAVAILABLE" in text
    assert "REST" in text
    assert "Available for workout" in text
    assert "Constraints" in text


def test_format_availability_icons():
    """Correct icons for each status."""
    gen = make_generator()
    avail = {"0": "available", "1": "unavailable", "2": "rest",
             "3": "available", "4": "available", "5": "available", "6": "available"}
    text = gen._format_availability_for_prompt(avail)
    assert "\u2705" in text  # available
    assert "\U0001f6ab" in text  # unavailable
    assert "\U0001f634" in text  # rest


def test_availability_weekend_only():
    """Weekend-only availability."""
    gen = make_generator()
    result = gen._predict_daily_tss_with_availability(
        weekly_tss_target=300,
        training_style="endurance",
        available_days=[5, 6],
        unavailable_days=[0, 1, 2, 3, 4],
    )
    for d in range(5):
        assert result[d] == 0
    assert result[5] > 0
    assert result[6] > 0


def test_availability_weekday_only():
    """Weekday-only availability."""
    gen = make_generator()
    result = gen._predict_daily_tss_with_availability(
        weekly_tss_target=400,
        training_style="sweetspot",
        available_days=[0, 1, 2, 3, 4],
        unavailable_days=[5, 6],
    )
    assert result[5] == 0
    assert result[6] == 0
    assert sum(result[d] for d in range(5)) > 0


def test_mixed_availability():
    """Mixed available/unavailable/rest."""
    gen = make_generator()
    avail = {"0": "rest", "1": "available", "2": "unavailable",
             "3": "available", "4": "rest", "5": "available", "6": "unavailable"}
    available_days = [1, 3, 5]
    unavailable_days = [0, 2, 4, 6]
    result = gen._predict_daily_tss_with_availability(
        weekly_tss_target=350,
        training_style="threshold",
        available_days=available_days,
        unavailable_days=unavailable_days,
    )
    for d in unavailable_days:
        assert result[d] == 0
    for d in available_days:
        assert result[d] > 0
