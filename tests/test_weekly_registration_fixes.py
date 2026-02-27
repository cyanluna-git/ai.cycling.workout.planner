"""Tests for weekly workout registration fixes.

Covers:
1. resolve_workout_steps() — shared steps resolution helper
2. ZWO format compatibility (DB format → frontend format → ZWO XML)
3. _calculate_daily_duration_targets() — per-day duration calculation
4. _post_validate_weekly_tss() — profile-based workouts skip duration scaling
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---------------------------------------------------------------------------
# resolve_workout_steps tests
# ---------------------------------------------------------------------------
class TestResolveWorkoutSteps:
    """Tests for the shared steps resolution helper in plans.py."""

    def _fn(self):
        from api.routers.plans import resolve_workout_steps
        return resolve_workout_steps

    def test_returns_planned_steps_directly(self):
        """Case 1: planned_steps already present — use as-is."""
        resolve = self._fn()
        steps = [{"duration": 300, "power": {"value": 75, "units": "%ftp"}}]
        workout = {"planned_steps": steps, "profile_id": None, "planned_modules": []}
        result = resolve(workout, ftp=250)
        assert result == steps

    def test_returns_none_when_no_source(self):
        """Case: no steps, no profile_id, no modules → None."""
        resolve = self._fn()
        workout = {"planned_steps": None, "profile_id": None, "planned_modules": []}
        result = resolve(workout, ftp=250)
        assert result is None

    def test_returns_none_for_empty_planned_steps(self):
        """Empty list is falsy → falls through to next source."""
        resolve = self._fn()
        workout = {"planned_steps": [], "profile_id": None, "planned_modules": []}
        result = resolve(workout, ftp=250)
        assert result is None

    def test_priority_planned_steps_over_profile_id(self):
        """planned_steps has highest priority."""
        resolve = self._fn()
        steps = [{"duration": 600, "power": {"value": 80, "units": "%ftp"}}]
        workout = {
            "planned_steps": steps,
            "profile_id": 999,  # Would fail if used (fake ID)
            "planned_modules": [],
        }
        result = resolve(workout, ftp=250)
        assert result == steps


# ---------------------------------------------------------------------------
# ZWO format compatibility tests
# ---------------------------------------------------------------------------
class TestZWOFormatCompatibility:
    """Verify that the ZWO converter works correctly with frontend-format steps."""

    def _make_frontend_steps(self):
        """Frontend format steps (output of profile_to_frontend_steps)."""
        return [
            {
                "duration": 600,
                "warmup": True,
                "ramp": True,
                "power": {"start": 48, "end": 68, "units": "%ftp"},
            },
            {
                "duration": 900,
                "power": {"value": 88, "units": "%ftp"},
            },
            {
                "repeat": 3,
                "steps": [
                    {"duration": 180, "power": {"value": 105, "units": "%ftp"}},
                    {"duration": 120, "power": {"value": 55, "units": "%ftp"}},
                ],
            },
            {
                "duration": 300,
                "cooldown": True,
                "ramp": True,
                "power": {"start": 65, "end": 48, "units": "%ftp"},
            },
        ]

    def _make_raw_db_steps(self):
        """Raw DB format steps (what profile.steps_json.steps looks like)."""
        return [
            {"type": "warmup", "duration_sec": 600, "start_power": 48, "end_power": 68},
            {"type": "steady", "duration_sec": 900, "power": 88},
            {"type": "intervals", "repeat": 3, "on_sec": 180, "off_sec": 120,
             "on_power": 105, "off_power": 55},
            {"type": "cooldown", "duration_sec": 300, "start_power": 65, "end_power": 48},
        ]

    def test_frontend_steps_convert_to_valid_zwo(self):
        """Frontend-format steps → ZWO XML without errors."""
        from src.services.zwo_converter import ZWOConverter
        converter = ZWOConverter(workout_name="Test Workout")
        xml = converter.convert(self._make_frontend_steps())
        assert "<workout_file>" in xml
        assert "<Warmup" in xml
        assert "<SteadyState" in xml
        assert "<IntervalsT" in xml
        assert "<Cooldown" in xml

    def test_frontend_steps_base64_encoding(self):
        """convert_to_base64 returns non-empty string."""
        from src.services.zwo_converter import ZWOConverter
        import base64
        converter = ZWOConverter(workout_name="Test")
        b64 = converter.convert_to_base64(self._make_frontend_steps())
        assert b64
        # Verify it's valid base64
        decoded = base64.b64decode(b64).decode("utf-8")
        assert "<workout_file>" in decoded

    def test_raw_db_steps_crash_zwo_converter(self):
        """Raw DB steps cause AttributeError in ZWO converter (confirms the bug).

        DB format: {"type": "steady", "power": 88}   ← power is int
        ZWO converter: power.get("value", 75)         ← expects dict

        This is exactly why register-all was failing before the fix.
        """
        from src.services.zwo_converter import ZWOConverter
        converter = ZWOConverter(workout_name="Test")
        with pytest.raises((AttributeError, TypeError)):
            converter.convert(self._make_raw_db_steps())

    def test_profile_to_frontend_steps_fixes_format(self):
        """profile_to_frontend_steps converts DB format to ZWO-compatible format."""
        from api.services.workout_profile_service import WorkoutProfileService
        from src.services.zwo_converter import ZWOConverter

        service = WorkoutProfileService()

        # Construct a minimal profile dict with DB-format steps
        profile = {
            "id": 999,
            "steps_json": {"steps": self._make_raw_db_steps()},
        }
        frontend_steps = service.profile_to_frontend_steps(profile, ftp=250)

        # Frontend steps should have 'duration' key (not 'duration_sec')
        for step in frontend_steps:
            if "repeat" not in step:
                assert "duration" in step, f"Missing 'duration' in step: {step}"
            assert "duration_sec" not in step, f"'duration_sec' leaked into frontend step: {step}"

        # These steps should convert to valid ZWO without Duration=0
        converter = ZWOConverter(workout_name="Test")
        xml = converter.convert(frontend_steps)
        assert 'Duration="0"' not in xml, (
            "After profile_to_frontend_steps, no Duration=0 should appear"
        )
        assert "<Warmup" in xml
        assert "<Cooldown" in xml


# ---------------------------------------------------------------------------
# _calculate_daily_duration_targets tests
# ---------------------------------------------------------------------------
class TestCalculateDailyDurationTargets:
    """Tests for the new per-day duration target calculation."""

    def _gen(self):
        from api.services.weekly_plan_service import WeeklyPlanGenerator
        class FakeLLM:
            def generate(self, **kw): return "[]"
        return WeeklyPlanGenerator(llm_client=FakeLLM(), user_profile={})

    def test_rest_days_get_zero_duration(self):
        gen = self._gen()
        daily_tss = {0: 0, 1: 32, 2: 0, 3: 32, 4: 0, 5: 56, 6: 56}
        result = gen._calculate_daily_duration_targets(daily_tss, "sweetspot")
        assert result[0] == 0
        assert result[2] == 0
        assert result[4] == 0

    def test_weekend_min_duration_45(self):
        """Weekend days enforce ≥ 45 min floor."""
        gen = self._gen()
        # TSS 10 on Saturday → mathematically ~8 min but should clamp to 45
        daily_tss = {5: 10, 6: 10}
        result = gen._calculate_daily_duration_targets(daily_tss, "sweetspot")
        assert result[5] >= 45
        assert result[6] >= 45

    def test_weekday_min_duration_30(self):
        """Weekday days enforce ≥ 30 min floor."""
        gen = self._gen()
        daily_tss = {1: 5}  # Very low TSS
        result = gen._calculate_daily_duration_targets(daily_tss, "sweetspot")
        assert result[1] >= 30

    def test_weekend_longer_than_weekday_for_same_style(self):
        """Weekend should produce longer durations due to lower IF assumption."""
        gen = self._gen()
        daily_tss = {1: 50, 5: 50}  # Same TSS, different days
        result = gen._calculate_daily_duration_targets(daily_tss, "sweetspot")
        # Weekend uses lower IF → longer duration for same TSS
        assert result[5] >= result[1], (
            f"Weekend dur={result[5]} should be >= weekday dur={result[1]}"
        )

    def test_polarized_400tss_weekend_is_long(self):
        """Polarized style with high TSS weekend should produce 90+ min."""
        gen = self._gen()
        daily_tss = {5: 140, 6: 100}
        result = gen._calculate_daily_duration_targets(daily_tss, "polarized")
        assert result[5] >= 90
        assert result[6] >= 60

    def test_returns_dict_for_all_days(self):
        gen = self._gen()
        daily_tss = {i: 0 for i in range(7)}
        daily_tss[1] = 30
        daily_tss[5] = 60
        result = gen._calculate_daily_duration_targets(daily_tss, "sweetspot")
        assert len(result) == 7


# ---------------------------------------------------------------------------
# _post_validate_weekly_tss: profile_id duration protection tests
# ---------------------------------------------------------------------------
class TestPostValidateWeeklyTss:
    """Tests for the profile_id duration protection fix."""

    def _gen(self):
        from api.services.weekly_plan_service import WeeklyPlanGenerator, DailyPlan
        from datetime import date

        class FakeLLM:
            def generate(self, **kw): return "[]"

        gen = WeeklyPlanGenerator(llm_client=FakeLLM(), user_profile={})

        def make_plan(profile_id, duration, tss, workout_type="SweetSpot"):
            return DailyPlan(
                day_index=1,
                day_name="Tuesday",
                workout_date=date(2026, 2, 24),
                workout_type=workout_type,
                workout_name="Test Workout",
                duration_minutes=duration,
                estimated_tss=tss,
                intensity="moderate",
                selected_modules=[],
                rationale="",
                profile_id=profile_id,
            )

        return gen, make_plan

    def test_profile_based_duration_NOT_scaled(self):
        """Profile workouts (profile_id set) should keep original duration after TSS scaling."""
        gen, make_plan = self._gen()
        # Profile workout: 30 min, 43 TSS
        plan = make_plan(profile_id=42, duration=30, tss=43)
        plans = [plan]
        # Weekly target = 100 TSS → scale factor = 100/43 ≈ 2.3 (big scale)
        result = gen._post_validate_weekly_tss(plans, weekly_tss_target=100)
        # Duration should NOT be scaled (profile is a fixed ZWO file)
        assert result[0].duration_minutes == 30, (
            f"Profile workout duration should stay 30, got {result[0].duration_minutes}"
        )

    def test_legacy_module_duration_IS_scaled(self):
        """Legacy module workouts (profile_id=None) SHOULD scale duration."""
        gen, make_plan = self._gen()
        # Module workout: 30 min, 20 TSS → scale to target 60 TSS = 3x
        plan = make_plan(profile_id=None, duration=30, tss=20)
        plans = [plan]
        result = gen._post_validate_weekly_tss(plans, weekly_tss_target=60)
        # Duration should be scaled up (capped at 180)
        assert result[0].duration_minutes > 30, (
            f"Module workout duration should be scaled, got {result[0].duration_minutes}"
        )

    def test_rest_days_not_affected(self):
        """Rest days always keep duration 0."""
        gen, make_plan = self._gen()
        rest = make_plan(profile_id=None, duration=0, tss=0, workout_type="Rest")
        plans = [rest]
        result = gen._post_validate_weekly_tss(plans, weekly_tss_target=200)
        assert result[0].duration_minutes == 0

    def test_within_tolerance_no_scaling(self):
        """If total TSS within ±15% of target, no scaling applied."""
        gen, make_plan = self._gen()
        plan = make_plan(profile_id=42, duration=45, tss=50)
        plans = [plan]
        # Target 50 → ratio 1.0 (within 15%)
        result = gen._post_validate_weekly_tss(plans, weekly_tss_target=50)
        assert result[0].duration_minutes == 45
        assert result[0].estimated_tss == 50
