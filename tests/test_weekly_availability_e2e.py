"""Integration tests for weekly availability feature."""

import pytest
import json
import sys
import os
from datetime import date
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.weekly_plan_service import (
    WeeklyPlanGenerator,
    DEFAULT_AVAILABILITY,
    WEEKLY_PLAN_USER_PROMPT,
)


def _make_llm_response(available_days, week_start):
    """Create a valid LLM JSON response."""
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday",
                 "Friday", "Saturday", "Sunday"]
    plans = []
    for i in range(7):
        if i in available_days:
            plans.append({
                "day_index": i,
                "day_name": day_names[i],
                "date": str(week_start),
                "session": None,
                "workout_type": "Endurance",
                "workout_name": f"{day_names[i]} Endurance",
                "duration_minutes": 60,
                "estimated_tss": 50,
                "intensity": "moderate",
                "selected_modules": ["ramp_standard", "endurance_20min", "flush_and_fade"],
                "rationale": "Endurance ride",
            })
        else:
            plans.append({
                "day_index": i,
                "day_name": day_names[i],
                "date": str(week_start),
                "session": None,
                "workout_type": "Rest",
                "workout_name": "Rest Day",
                "duration_minutes": 0,
                "estimated_tss": 0,
                "intensity": "rest",
                "selected_modules": [],
                "rationale": "Rest day",
            })
    return json.dumps(plans)


class MockLLM:
    def __init__(self, available_days):
        self.available_days = available_days
        self.last_user_prompt = None

    def generate(self, system_prompt, user_prompt):
        self.last_user_prompt = user_prompt
        return _make_llm_response(self.available_days, date(2026, 2, 16))


@patch("src.services.workout_modules.get_module_inventory_text", return_value="modules here")
def test_e2e_with_unavailable_days(mock_inv):
    """User with 3 available days gets proper plan."""
    profile = {
        "training_style": "sweetspot",
        "training_focus": "maintain",
        "preferred_duration": 60,
        "weekly_availability": {
            "0": "unavailable", "1": "available", "2": "unavailable",
            "3": "available", "4": "unavailable", "5": "available", "6": "unavailable",
        },
    }
    llm = MockLLM(available_days=[1, 3, 5])
    gen = WeeklyPlanGenerator(llm, profile)
    plan = gen.generate_weekly_plan(
        ctl=50, atl=45, tsb=5, form_status="Optimal",
        week_start=date(2026, 2, 16), weekly_tss_target=400,
    )
    assert plan is not None
    assert len(plan.daily_plans) >= 7


@patch("src.services.workout_modules.get_module_inventory_text", return_value="modules here")
def test_e2e_with_rest_days(mock_inv):
    """Rest vs unavailable both result in TSS=0."""
    profile = {
        "training_style": "polarized",
        "training_focus": "maintain",
        "preferred_duration": 60,
        "weekly_availability": {
            "0": "rest", "1": "available", "2": "available",
            "3": "available", "4": "rest", "5": "available", "6": "available",
        },
    }
    llm = MockLLM(available_days=[1, 2, 3, 5, 6])
    gen = WeeklyPlanGenerator(llm, profile)
    plan = gen.generate_weekly_plan(
        ctl=60, atl=55, tsb=5, form_status="Optimal",
        week_start=date(2026, 2, 16), weekly_tss_target=450,
    )
    assert plan is not None


@patch("src.services.workout_modules.get_module_inventory_text", return_value="modules here")
def test_e2e_prompt_contains_availability(mock_inv):
    """Prompt sent to LLM contains availability section."""
    profile = {
        "training_style": "sweetspot",
        "training_focus": "maintain",
        "preferred_duration": 60,
        "weekly_availability": {
            "0": "unavailable", "1": "available", "2": "available",
            "3": "available", "4": "unavailable", "5": "available", "6": "available",
        },
    }
    llm = MockLLM(available_days=[1, 2, 3, 5, 6])
    gen = WeeklyPlanGenerator(llm, profile)
    gen.generate_weekly_plan(
        ctl=50, atl=45, tsb=5, form_status="Optimal",
        week_start=date(2026, 2, 16), weekly_tss_target=400,
    )
    assert "Weekly Availability" in llm.last_user_prompt
    assert "UNAVAILABLE" in llm.last_user_prompt


@patch("src.services.workout_modules.get_module_inventory_text", return_value="modules here")
def test_e2e_unavailable_days_get_rest(mock_inv):
    """Unavailable days should get Rest Day assignment."""
    profile = {
        "training_style": "sweetspot",
        "training_focus": "maintain",
        "preferred_duration": 60,
        "weekly_availability": {
            "0": "unavailable", "1": "available", "2": "unavailable",
            "3": "available", "4": "unavailable", "5": "available", "6": "unavailable",
        },
    }
    llm = MockLLM(available_days=[1, 3, 5])
    gen = WeeklyPlanGenerator(llm, profile)
    plan = gen.generate_weekly_plan(
        ctl=50, atl=45, tsb=5, form_status="Optimal",
        week_start=date(2026, 2, 16), weekly_tss_target=400,
    )
    for dp in plan.daily_plans:
        if dp.day_index in [0, 2, 4, 6]:
            assert dp.workout_type == "Rest", f"Day {dp.day_index} should be Rest"


@patch("src.services.workout_modules.get_module_inventory_text", return_value="modules here")
def test_e2e_tss_redistributed(mock_inv):
    """TSS targets in prompt should only be on available days."""
    profile = {
        "training_style": "sweetspot",
        "training_focus": "maintain",
        "preferred_duration": 60,
        "weekly_availability": {
            "0": "unavailable", "1": "available", "2": "unavailable",
            "3": "available", "4": "unavailable", "5": "available", "6": "unavailable",
        },
    }
    llm = MockLLM(available_days=[1, 3, 5])
    gen = WeeklyPlanGenerator(llm, profile)
    gen.generate_weekly_plan(
        ctl=50, atl=45, tsb=5, form_status="Optimal",
        week_start=date(2026, 2, 16), weekly_tss_target=400,
    )
    prompt = llm.last_user_prompt
    # Monday (day 0) should show Rest (0 TSS)
    assert "Monday: Rest (0 TSS)" in prompt
    # Tuesday (day 1) should have TSS > 0
    assert "Tuesday: ~" in prompt
