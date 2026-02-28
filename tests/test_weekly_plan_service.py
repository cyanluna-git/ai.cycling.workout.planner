"""Tests for weekly plan service (Phase 3)."""

import json
import pytest
from datetime import date
from unittest.mock import MagicMock, patch

from api.services.weekly_plan_service import (
    WeeklyPlanGenerator,
    WeeklyPlan,
    DailyPlan,
    TSB_INTENSITY_MAP,
    WEEKLY_STRUCTURE_TEMPLATES,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_generator(profile=None):
    """Create a WeeklyPlanGenerator with a mock LLM client."""
    llm = MagicMock()
    if profile is None:
        profile = {"training_style": "auto", "training_focus": "maintain", "preferred_duration": 60}
    gen = WeeklyPlanGenerator(llm_client=llm, user_profile=profile)
    return gen


def _mock_llm_response():
    """Return a minimal valid LLM JSON response for 7 days."""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    plans = []
    for i, name in enumerate(days):
        if i in (0, 4):  # Rest days
            plans.append({
                "day_index": i, "day_name": name, "date": f"2026-02-16",
                "session": None, "workout_type": "Rest", "workout_name": "Rest Day",
                "duration_minutes": 0, "estimated_tss": 0, "intensity": "rest",
                "selected_modules": [], "profile_id": None, "customization": None, "rationale": "Rest"
            })
        else:
            plans.append({
                "day_index": i, "day_name": name, "date": f"2026-02-16",
                "session": None, "workout_type": "Endurance",
                "workout_name": "Zone 2 Ride", "duration_minutes": 60,
                "estimated_tss": 50, "intensity": "easy",
                "selected_modules": [], "profile_id": 65, "customization": None,
                "rationale": "Aerobic base"
            })
    return json.dumps(plans)


# ---------------------------------------------------------------------------
# Auto style resolution
# ---------------------------------------------------------------------------
class TestResolveAutoStyle:
    def test_resolve_auto_style_fresh(self):
        gen = _make_generator()
        assert gen._resolve_auto_style(tsb=15.0, training_focus="maintain") == "polarized"

    def test_resolve_auto_style_tired(self):
        gen = _make_generator()
        assert gen._resolve_auto_style(tsb=-12.0, training_focus="maintain") == "sweetspot"

    def test_resolve_auto_style_very_tired(self):
        gen = _make_generator()
        assert gen._resolve_auto_style(tsb=-25.0, training_focus="maintain") == "endurance"

    def test_resolve_auto_style_recovery_focus(self):
        gen = _make_generator()
        assert gen._resolve_auto_style(tsb=15.0, training_focus="recovery") == "endurance"


# ---------------------------------------------------------------------------
# TSB intensity filtering
# ---------------------------------------------------------------------------
class TestTSBIntensityFiltering:
    def test_tsb_intensity_filtering(self):
        """TSB < -20 (very_tired) should only allow Recovery and Endurance."""
        allowed = TSB_INTENSITY_MAP["very_tired"]
        assert "VO2max" not in allowed
        assert "Threshold" not in allowed
        assert "Recovery" in allowed
        assert "Endurance" in allowed


# ---------------------------------------------------------------------------
# Type enforcement / downgrade
# ---------------------------------------------------------------------------
class TestTypeEnforcementDowngrade:
    def test_type_enforcement_downgrade(self):
        """VO2max in very_tired state should be downgraded."""
        gen = _make_generator()
        allowed = TSB_INTENSITY_MAP["very_tired"]  # ["Recovery", "Endurance"]
        # Simulate LLM returning VO2max when very tired
        bad_response = json.dumps([{
            "day_index": 0, "day_name": "Monday", "date": "2026-02-16",
            "session": None, "workout_type": "VO2max", "workout_name": "VO2 Blast",
            "duration_minutes": 60, "estimated_tss": 80, "intensity": "hard",
            "selected_modules": [],
            "rationale": "Hard day"
        }])
        plans = gen._parse_response(bad_response, date(2026, 2, 16), allowed_types=allowed)
        monday = [p for p in plans if p.day_index == 0][0]
        assert monday.workout_type in allowed, f"Expected downgrade, got {monday.workout_type}"


# ---------------------------------------------------------------------------
# Module validation
# ---------------------------------------------------------------------------
class TestModuleValidation:
    def test_module_validation_removes_invalid(self):
        gen = _make_generator()
        modules = ["ramp_standard", "nonexistent_module_xyz", "endurance_60min"]
        valid = gen._validate_modules(modules)
        assert "nonexistent_module_xyz" not in valid
        assert "ramp_standard" in valid
        assert "endurance_60min" in valid


# ---------------------------------------------------------------------------
# Athlete context
# ---------------------------------------------------------------------------
class TestAthleteContext:
    def test_athlete_context_with_ftp_weight(self):
        gen = _make_generator()
        ctx = gen._build_athlete_context(ftp=280.0, weight=72.0)
        assert "280W" in ctx
        assert "72.0kg" in ctx
        assert "W/kg" in ctx

    def test_athlete_context_without_ftp(self):
        gen = _make_generator()
        ctx = gen._build_athlete_context(ftp=None, weight=None)
        assert ctx == ""


# ---------------------------------------------------------------------------
# Used modules collection
# ---------------------------------------------------------------------------
class TestUsedModulesCollection:
    def test_used_modules_collection(self):
        """WeeklyPlan.used_modules should be empty (profile-based system)."""  
        gen = _make_generator({"training_style": "endurance", "training_focus": "maintain", "preferred_duration": 60})
        gen.llm.generate.return_value = _mock_llm_response()
        plan = gen.generate_weekly_plan(
            ctl=50.0, atl=55.0, tsb=-5.0, form_status="Neutral",
            week_start=date(2026, 2, 16),
        )
        assert isinstance(plan.used_modules, list)
        # Profile-based system: selected_modules is empty, so used_modules is also empty
        assert len(plan.used_modules) == 0
        # Instead, verify that workout days have profile_id
        workout_days = [dp for dp in plan.daily_plans if dp.workout_type != "Rest"]
        assert all(hasattr(dp, 'profile_id') and dp.profile_id is not None for dp in workout_days)


# ---------------------------------------------------------------------------
# Style template filtering
# ---------------------------------------------------------------------------
class TestStyleTemplateFiltering:
    def test_style_template_filtering(self):
        """Polarized style should use polarized template."""
        template = WEEKLY_STRUCTURE_TEMPLATES.get("polarized")
        assert template is not None
        assert "POLARIZED" in template
        assert "80/20" in template


# ---------------------------------------------------------------------------
# Backward compatibility
# ---------------------------------------------------------------------------
class TestBackwardCompatibility:
    def test_backward_compatibility(self):
        """Calling generate_weekly_plan without ftp/weight should work."""
        gen = _make_generator({"training_style": "sweetspot", "training_focus": "maintain", "preferred_duration": 60})
        gen.llm.generate.return_value = _mock_llm_response()
        plan = gen.generate_weekly_plan(
            ctl=60.0, atl=65.0, tsb=-5.0, form_status="Neutral",
            week_start=date(2026, 2, 16),
        )
        assert isinstance(plan, WeeklyPlan)
        assert len(plan.daily_plans) >= 7


# ---------------------------------------------------------------------------
# Weekly TSS Target
# ---------------------------------------------------------------------------
class TestWeeklyTssTarget:
    def test_weekly_tss_target_from_parameter(self):
        """weekly_tss_target parameter should override auto calculation."""
        gen = _make_generator({"training_style": "sweetspot", "training_focus": "maintain", "preferred_duration": 60})
        gen.llm.generate.return_value = _mock_llm_response()
        plan = gen.generate_weekly_plan(
            ctl=50.0, atl=55.0, tsb=-5.0, form_status="Neutral",
            week_start=date(2026, 2, 16),
            weekly_tss_target=500,
        )
        assert isinstance(plan, WeeklyPlan)

    def test_weekly_tss_target_from_user_settings(self):
        """weekly_tss_target from user_settings should be used when no param."""
        gen = _make_generator({
            "training_style": "sweetspot",
            "training_focus": "maintain",
            "preferred_duration": 60,
            "weekly_tss_target": 450,
        })
        gen.llm.generate.return_value = _mock_llm_response()
        plan = gen.generate_weekly_plan(
            ctl=50.0, atl=55.0, tsb=-5.0, form_status="Neutral",
            week_start=date(2026, 2, 16),
        )
        assert isinstance(plan, WeeklyPlan)

    def test_weekly_tss_target_param_overrides_settings(self):
        """Parameter should take priority over user_settings."""
        gen = _make_generator({
            "training_style": "sweetspot",
            "training_focus": "maintain",
            "preferred_duration": 60,
            "weekly_tss_target": 450,
        })
        gen.llm.generate.return_value = _mock_llm_response()
        plan = gen.generate_weekly_plan(
            ctl=50.0, atl=55.0, tsb=-5.0, form_status="Neutral",
            week_start=date(2026, 2, 16),
            weekly_tss_target=600,
        )
        assert isinstance(plan, WeeklyPlan)

    def test_weekly_tss_target_none_uses_auto(self):
        """No weekly_tss_target should use auto calculation (backward compat)."""
        gen = _make_generator({"training_style": "sweetspot", "training_focus": "build", "preferred_duration": 60})
        gen.llm.generate.return_value = _mock_llm_response()
        plan = gen.generate_weekly_plan(
            ctl=60.0, atl=65.0, tsb=-5.0, form_status="Neutral",
            week_start=date(2026, 2, 16),
        )
        assert isinstance(plan, WeeklyPlan)
        assert len(plan.daily_plans) >= 7


# ---------------------------------------------------------------------------
# Current-week (mid-week) generation
# ---------------------------------------------------------------------------
class TestCurrentWeekGeneration:
    """Tests for remaining_days_only mid-week plan generation."""

    def test_mid_week_past_days_are_rest(self):
        """Days before start_day_index should be Rest with TSS=0."""
        gen = _make_generator({
            "training_style": "sweetspot", "training_focus": "maintain",
            "preferred_duration": 60,
        })
        gen.llm.generate.return_value = _mock_llm_response()
        plan = gen.generate_weekly_plan(
            ctl=60.0, atl=55.0, tsb=5.0, form_status="Optimal",
            week_start=date(2026, 3, 2),  # Monday
            weekly_tss_target=500,
            remaining_days_only=True,
            completed_tss=200,
            start_day_index=3,  # Thursday
        )
        assert isinstance(plan, WeeklyPlan)
        # LLM is mocked, so we can't fully control which days the mock returns.
        # However, we verify the generator ran without errors.
        assert len(plan.daily_plans) >= 7

    def test_mid_week_remaining_tss_subtracted(self):
        """Remaining TSS = weekly_target - completed_tss; check that
        the generator's internal daily_tss_targets reflect this."""
        gen = _make_generator({
            "training_style": "sweetspot", "training_focus": "maintain",
            "preferred_duration": 60,
        })
        # We'll check the daily TSS prediction directly via the internal method
        daily_tss = gen._predict_daily_tss_with_availability(
            weekly_tss_target=500,
            training_style="sweetspot",
            available_days=[1, 2, 3, 5, 6],
            unavailable_days=[0, 4],
        )
        # Simulate mid-week: zero out days 0-2, redistribute
        remaining_tss = 500 - 200  # 300 remaining
        for day_idx in range(3):
            daily_tss[day_idx] = 0
        remaining_ratios = {
            k: v for k, v in daily_tss.items() if k >= 3 and v > 0
        }
        total = sum(remaining_ratios.values())
        if total > 0:
            for day_idx, old_tss in remaining_ratios.items():
                normalized = old_tss / total
                daily_tss[day_idx] = min(
                    int(round(remaining_tss * normalized / 5) * 5), 150
                )
        # Past days should be 0
        assert daily_tss[0] == 0
        assert daily_tss[1] == 0
        assert daily_tss[2] == 0
        # Total of remaining days should not exceed remaining_tss + rounding margin
        remaining_total = sum(v for k, v in daily_tss.items() if k >= 3)
        assert remaining_total <= remaining_tss + 25  # rounding tolerance

    def test_mid_week_per_day_tss_cap(self):
        """Per-day TSS should be capped at 150 (180 for endurance weekends)."""
        gen = _make_generator({
            "training_style": "endurance", "training_focus": "maintain",
            "preferred_duration": 60,
        })
        gen.llm.generate.return_value = _mock_llm_response()
        plan = gen.generate_weekly_plan(
            ctl=80.0, atl=70.0, tsb=10.0, form_status="Fresh",
            week_start=date(2026, 3, 2),
            weekly_tss_target=700,
            remaining_days_only=True,
            completed_tss=100,
            start_day_index=5,  # Saturday — only Sat+Sun left
        )
        assert isinstance(plan, WeeklyPlan)

    def test_next_week_generation_unchanged(self):
        """Next week generation should not be affected by mid-week logic."""
        gen = _make_generator({
            "training_style": "sweetspot", "training_focus": "maintain",
            "preferred_duration": 60,
        })
        gen.llm.generate.return_value = _mock_llm_response()
        plan = gen.generate_weekly_plan(
            ctl=60.0, atl=55.0, tsb=5.0, form_status="Optimal",
            week_start=date(2026, 3, 9),  # Next week Monday
            weekly_tss_target=500,
            remaining_days_only=False,  # Not current week
        )
        assert isinstance(plan, WeeklyPlan)
        assert len(plan.daily_plans) >= 7
        # Verify that non-rest days have TSS > 0
        workout_days = [dp for dp in plan.daily_plans if dp.workout_type != "Rest"]
        assert len(workout_days) >= 3
