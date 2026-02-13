"""Comprehensive E2E tests for weekly availability with various scenarios."""

import pytest
import json
import sys
import os
from datetime import date
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.weekly_plan_service import WeeklyPlanGenerator


def _make_llm_response(available_days, week_start, target_tss_map=None):
    """Create a smart LLM response."""
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday",
                 "Friday", "Saturday", "Sunday"]
    plans = []
    
    if target_tss_map is None:
        target_tss_map = {day: 70 for day in available_days}
    
    for i in range(7):
        if i in available_days:
            tss = target_tss_map.get(i, 70)
            duration = min(180, max(30, int(tss * 1.2)))
            
            plans.append({
                "day_index": i,
                "day_name": day_names[i],
                "date": str(week_start),
                "session": None,
                "workout_type": "SweetSpot" if tss > 70 else "Endurance",
                "workout_name": f"{day_names[i]} Workout",
                "duration_minutes": duration,
                "estimated_tss": tss,
                "intensity": "hard" if tss > 100 else "moderate",
                "selected_modules": ["ramp_standard", "endurance_20min", "flush_and_fade"],
                "rationale": f"Target {tss} TSS",
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


class SimpleMockLLM:
    """Simple Mock LLM that takes available days."""
    
    def __init__(self, available_days, target_tss_map=None):
        self.available_days = available_days
        self.target_tss_map = target_tss_map or {}
        self.last_user_prompt = None
    
    def generate(self, system_prompt, user_prompt):
        self.last_user_prompt = user_prompt
        return _make_llm_response(
            self.available_days, 
            date(2026, 2, 16),
            self.target_tss_map
        )


@patch("src.services.workout_modules.get_module_inventory_text", return_value="modules here")
def test_weekend_only_availability(mock_inv):
    """User can only work out on weekends (Sat, Sun)."""
    profile = {
        "training_style": "polarized",
        "training_focus": "maintain",
        "preferred_duration": 120,
        "weekly_availability": {
            "0": "unavailable", "1": "unavailable", "2": "unavailable",
            "3": "unavailable", "4": "unavailable",
            "5": "available", "6": "available",
        },
    }
    
    llm = SimpleMockLLM(available_days=[5, 6], target_tss_map={5: 150, 6: 150})
    gen = WeeklyPlanGenerator(llm, profile)
    
    plan = gen.generate_weekly_plan(
        ctl=50, atl=45, tsb=5, form_status="Optimal",
        week_start=date(2026, 2, 16), weekly_tss_target=400,
    )
    
    # Weekdays should all be Rest
    for i in range(5):
        dp = next(d for d in plan.daily_plans if d.day_index == i)
        assert dp.workout_type == "Rest", f"Weekday {i} should be Rest"
        assert dp.estimated_tss == 0
    
    # Weekend should have workouts
    sat = next(d for d in plan.daily_plans if d.day_index == 5)
    sun = next(d for d in plan.daily_plans if d.day_index == 6)
    assert sat.workout_type != "Rest"
    assert sun.workout_type != "Rest"
    assert sat.estimated_tss > 0
    assert sun.estimated_tss > 0


@patch("src.services.workout_modules.get_module_inventory_text", return_value="modules here")
def test_weekday_only_availability(mock_inv):
    """User can only work out on weekdays."""
    profile = {
        "training_style": "sweetspot",
        "training_focus": "build",
        "preferred_duration": 60,
        "weekly_availability": {
            "0": "available", "1": "available", "2": "available",
            "3": "available", "4": "available",
            "5": "unavailable", "6": "unavailable",
        },
    }
    
    llm = SimpleMockLLM(available_days=[0, 1, 2, 3, 4])
    gen = WeeklyPlanGenerator(llm, profile)
    
    plan = gen.generate_weekly_plan(
        ctl=60, atl=55, tsb=5, form_status="Optimal",
        week_start=date(2026, 2, 16), weekly_tss_target=450,
    )
    
    # Weekend should be Rest
    sat = next(d for d in plan.daily_plans if d.day_index == 5)
    sun = next(d for d in plan.daily_plans if d.day_index == 6)
    assert sat.workout_type == "Rest"
    assert sun.workout_type == "Rest"
    assert sat.estimated_tss == 0
    assert sun.estimated_tss == 0


@patch("src.services.workout_modules.get_module_inventory_text", return_value="modules here")
def test_single_day_availability_extreme(mock_inv):
    """Extreme case: only 1 day available."""
    profile = {
        "training_style": "endurance",
        "training_focus": "maintain",
        "preferred_duration": 180,
        "weekly_availability": {
            "0": "unavailable", "1": "unavailable", "2": "unavailable",
            "3": "unavailable", "4": "unavailable",
            "5": "available",
            "6": "unavailable",
        },
    }
    
    llm = SimpleMockLLM(available_days=[5], target_tss_map={5: 150})
    gen = WeeklyPlanGenerator(llm, profile)
    
    plan = gen.generate_weekly_plan(
        ctl=40, atl=35, tsb=5, form_status="Optimal",
        week_start=date(2026, 2, 16), weekly_tss_target=300,
    )
    
    # Only Saturday should have workout
    sat = next(d for d in plan.daily_plans if d.day_index == 5)
    assert sat.workout_type != "Rest"
    assert sat.estimated_tss > 0
    
    # All other days Rest
    for i in [0, 1, 2, 3, 4, 6]:
        dp = next(d for d in plan.daily_plans if d.day_index == i)
        assert dp.workout_type == "Rest"
        assert dp.estimated_tss == 0


@patch("src.services.workout_modules.get_module_inventory_text", return_value="modules here")
def test_tss_redistribution_verification(mock_inv):
    """Verify TSS is properly redistributed to available days."""
    profile = {
        "training_style": "sweetspot",
        "training_focus": "maintain",
        "preferred_duration": 60,
        "weekly_availability": {
            "0": "available", "1": "available", "2": "unavailable",
            "3": "available", "4": "unavailable",
            "5": "available", "6": "unavailable",
        },
    }
    
    llm = SimpleMockLLM(
        available_days=[0, 1, 3, 5],
        target_tss_map={0: 80, 1: 100, 3: 120, 5: 150}
    )
    gen = WeeklyPlanGenerator(llm, profile)
    
    target = 500
    plan = gen.generate_weekly_plan(
        ctl=70, atl=65, tsb=5, form_status="Optimal",
        week_start=date(2026, 2, 16), weekly_tss_target=target,
    )
    
    # Calculate total TSS
    total_tss = sum(dp.estimated_tss for dp in plan.daily_plans)
    
    # Should be within ±15% of target
    assert target * 0.85 <= total_tss <= target * 1.15, \
        f"Total TSS {total_tss} should be ~{target} (±15%)"
    
    # Unavailable days should have 0 TSS
    for i in [2, 4, 6]:
        dp = next(d for d in plan.daily_plans if d.day_index == i)
        assert dp.estimated_tss == 0


@patch("src.services.workout_modules.get_module_inventory_text", return_value="modules here")
def test_rest_vs_unavailable_both_zero_tss(mock_inv):
    """Both 'rest' and 'unavailable' should result in 0 TSS."""
    profile = {
        "training_style": "sweetspot",
        "training_focus": "maintain",
        "preferred_duration": 60,
        "weekly_availability": {
            "0": "rest", "1": "available", "2": "unavailable",
            "3": "available", "4": "rest",
            "5": "available", "6": "unavailable",
        },
    }
    
    llm = SimpleMockLLM(available_days=[1, 3, 5])
    gen = WeeklyPlanGenerator(llm, profile)
    
    plan = gen.generate_weekly_plan(
        ctl=60, atl=55, tsb=5, form_status="Optimal",
        week_start=date(2026, 2, 16), weekly_tss_target=400,
    )
    
    # Both rest and unavailable should be 0 TSS
    for i in [0, 2, 4, 6]:
        dp = next(d for d in plan.daily_plans if d.day_index == i)
        assert dp.estimated_tss == 0, f"Day {i} (rest/unavailable) should have 0 TSS"
        assert dp.workout_type == "Rest"


@patch("src.services.workout_modules.get_module_inventory_text", return_value="modules here")
def test_prompt_formatting_with_mixed_availability(mock_inv):
    """Verify prompt contains proper availability formatting."""
    profile = {
        "training_style": "sweetspot",
        "training_focus": "maintain",
        "preferred_duration": 60,
        "weekly_availability": {
            "0": "available", "1": "unavailable", "2": "rest",
            "3": "available", "4": "available",
            "5": "available", "6": "unavailable",
        },
    }
    
    llm = SimpleMockLLM(available_days=[0, 3, 4, 5])
    gen = WeeklyPlanGenerator(llm, profile)
    
    gen.generate_weekly_plan(
        ctl=60, atl=55, tsb=5, form_status="Optimal",
        week_start=date(2026, 2, 16), weekly_tss_target=400,
    )
    
    prompt = llm.last_user_prompt
    
    # Check availability section exists
    assert "Weekly Availability" in prompt
    
    # Check constraints mentioned
    assert "NO workouts on UNAVAILABLE or REST days" in prompt or "Distribute workouts only across AVAILABLE days" in prompt


@patch("src.services.workout_modules.get_module_inventory_text", return_value="modules here")
def test_all_days_available_baseline(mock_inv):
    """Baseline: all days available should work like before."""
    profile = {
        "training_style": "sweetspot",
        "training_focus": "maintain",
        "preferred_duration": 60,
        "weekly_availability": {
            str(i): "available" for i in range(7)
        },
    }
    
    llm = SimpleMockLLM(available_days=list(range(7)))
    gen = WeeklyPlanGenerator(llm, profile)
    
    plan = gen.generate_weekly_plan(
        ctl=70, atl=65, tsb=5, form_status="Optimal",
        week_start=date(2026, 2, 16), weekly_tss_target=500,
    )
    
    # Should have normal plan
    assert len(plan.daily_plans) == 7
    
    # At least some workout days
    workout_days = [d for d in plan.daily_plans if d.workout_type != "Rest"]
    assert len(workout_days) >= 4, "Should have at least 4 workout days"
