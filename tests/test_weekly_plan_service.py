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
                "selected_modules": [], "rationale": "Rest"
            })
        else:
            plans.append({
                "day_index": i, "day_name": name, "date": f"2026-02-16",
                "session": None, "workout_type": "Endurance",
                "workout_name": "Zone 2 Ride", "duration_minutes": 60,
                "estimated_tss": 50, "intensity": "easy",
                "selected_modules": ["ramp_standard", "endurance_60min", "flush_and_fade"],
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
            "selected_modules": ["ramp_standard", "endurance_60min", "flush_and_fade"],
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
        """WeeklyPlan.used_modules should collect all module keys from daily plans."""
        gen = _make_generator({"training_style": "endurance", "training_focus": "maintain", "preferred_duration": 60})
        gen.llm.generate.return_value = _mock_llm_response()
        plan = gen.generate_weekly_plan(
            ctl=50.0, atl=55.0, tsb=-5.0, form_status="Neutral",
            week_start=date(2026, 2, 16),
        )
        assert isinstance(plan.used_modules, list)
        # 5 workout days x 3 modules each = 15
        assert len(plan.used_modules) == 15
        assert "ramp_standard" in plan.used_modules


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
