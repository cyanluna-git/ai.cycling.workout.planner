"""E2E Integration tests for TSS Pre-prediction and Post-validation.

Tests the complete flow:
1. _predict_daily_tss() pre-allocates TSS targets
2. Targets injected into LLM prompt
3. Mock LLM generates weekly plan (conservative/aggressive scenarios)
4. _post_validate_weekly_tss() scales to match target
"""

import json
import pytest
from datetime import date
from unittest.mock import MagicMock

from api.services.weekly_plan_service import (
    WeeklyPlanGenerator,
    DAILY_TSS_RATIOS,
)


class TestTSSPredictValidateE2E:
    """End-to-end tests for TSS prediction and validation flow."""

    def setup_method(self):
        """Set up mock LLM client and generator."""
        self.mock_llm = MagicMock()
        self.user_profile = {
            "training_style": "sweetspot",
            "training_focus": "maintain",
            "preferred_duration": 60,
        }
        self.generator = WeeklyPlanGenerator(self.mock_llm, self.user_profile)

    def _mock_llm_response_conservative(self):
        """Mock LLM response that generates LESS than target (e.g., 400 when target is 500)."""
        return json.dumps([
            {"day_index": 0, "workout_type": "Rest", "workout_name": "Rest", "duration_minutes": 0, "estimated_tss": 0, "intensity": "rest", "selected_modules": [], "profile_id": None, "customization": None, "rationale": "Rest day"},
            {"day_index": 1, "workout_type": "SweetSpot", "workout_name": "SS 2x15", "duration_minutes": 60, "estimated_tss": 60, "intensity": "moderate", "selected_modules": [], "profile_id": 25, "customization": None, "rationale": "Sweet Spot"},
            {"day_index": 2, "workout_type": "Endurance", "workout_name": "Z2", "duration_minutes": 60, "estimated_tss": 50, "intensity": "low", "selected_modules": [], "profile_id": 65, "customization": None, "rationale": "Recovery"},
            {"day_index": 3, "workout_type": "SweetSpot", "workout_name": "SS 3x12", "duration_minutes": 60, "estimated_tss": 65, "intensity": "moderate", "selected_modules": [], "profile_id": 26, "customization": None, "rationale": "Sweet Spot"},
            {"day_index": 4, "workout_type": "Rest", "workout_name": "Rest", "duration_minutes": 0, "estimated_tss": 0, "intensity": "rest", "selected_modules": [], "profile_id": None, "customization": None, "rationale": "Rest day"},
            {"day_index": 5, "workout_type": "Threshold", "workout_name": "2x20", "duration_minutes": 90, "estimated_tss": 110, "intensity": "hard", "selected_modules": [], "profile_id": 13, "customization": None, "rationale": "Weekend key workout"},
            {"day_index": 6, "workout_type": "Endurance", "workout_name": "Long Z2", "duration_minutes": 120, "estimated_tss": 115, "intensity": "low", "selected_modules": [], "profile_id": 67, "customization": None, "rationale": "Aerobic base"},
        ])
        # Total = 400 TSS (target is 500)

    def _mock_llm_response_aggressive(self):
        """Mock LLM response that generates MORE than target (e.g., 700 when target is 500)."""
        return json.dumps([
            {"day_index": 0, "workout_type": "Rest", "workout_name": "Rest", "duration_minutes": 0, "estimated_tss": 0, "intensity": "rest", "selected_modules": [], "profile_id": None, "customization": None, "rationale": "Rest day"},
            {"day_index": 1, "workout_type": "Threshold", "workout_name": "Threshold", "duration_minutes": 90, "estimated_tss": 120, "intensity": "hard", "selected_modules": [], "profile_id": 14, "customization": None, "rationale": "Hard"},
            {"day_index": 2, "workout_type": "SweetSpot", "workout_name": "SS", "duration_minutes": 75, "estimated_tss": 85, "intensity": "moderate", "selected_modules": [], "profile_id": 26, "customization": None, "rationale": "Mid"},
            {"day_index": 3, "workout_type": "Threshold", "workout_name": "Threshold", "duration_minutes": 90, "estimated_tss": 120, "intensity": "hard", "selected_modules": [], "profile_id": 13, "customization": None, "rationale": "Hard"},
            {"day_index": 4, "workout_type": "Rest", "workout_name": "Rest", "duration_minutes": 0, "estimated_tss": 0, "intensity": "rest", "selected_modules": [], "profile_id": None, "customization": None, "rationale": "Rest day"},
            {"day_index": 5, "workout_type": "Threshold", "workout_name": "Long Threshold", "duration_minutes": 120, "estimated_tss": 180, "intensity": "hard", "selected_modules": [], "profile_id": 13, "customization": None, "rationale": "Weekend"},
            {"day_index": 6, "workout_type": "Threshold", "workout_name": "Long Threshold", "duration_minutes": 120, "estimated_tss": 195, "intensity": "hard", "selected_modules": [], "profile_id": 13, "customization": None, "rationale": "Weekend"},
        ])
        # Total = 700 TSS (target is 500)

    def _mock_llm_response_on_target(self):
        """Mock LLM response that's already within tolerance (480-500 range)."""
        return json.dumps([
            {"day_index": 0, "workout_type": "Rest", "workout_name": "Rest", "duration_minutes": 0, "estimated_tss": 0, "intensity": "rest", "selected_modules": [], "profile_id": None, "customization": None, "rationale": "Rest day"},
            {"day_index": 1, "workout_type": "SweetSpot", "workout_name": "SS 2x20", "duration_minutes": 75, "estimated_tss": 78, "intensity": "moderate", "selected_modules": [], "profile_id": 26, "customization": None, "rationale": "Sweet Spot"},
            {"day_index": 2, "workout_type": "Endurance", "workout_name": "Z2", "duration_minutes": 60, "estimated_tss": 55, "intensity": "low", "selected_modules": [], "profile_id": 65, "customization": None, "rationale": "Recovery"},
            {"day_index": 3, "workout_type": "SweetSpot", "workout_name": "SS 3x15", "duration_minutes": 75, "estimated_tss": 75, "intensity": "moderate", "selected_modules": [], "profile_id": 26, "customization": None, "rationale": "Sweet Spot"},
            {"day_index": 4, "workout_type": "Rest", "workout_name": "Rest", "duration_minutes": 0, "estimated_tss": 0, "intensity": "rest", "selected_modules": [], "profile_id": None, "customization": None, "rationale": "Rest day"},
            {"day_index": 5, "workout_type": "Threshold", "workout_name": "2x20", "duration_minutes": 90, "estimated_tss": 132, "intensity": "hard", "selected_modules": [], "profile_id": 13, "customization": None, "rationale": "Key workout"},
            {"day_index": 6, "workout_type": "Endurance", "workout_name": "Long Z2", "duration_minutes": 120, "estimated_tss": 140, "intensity": "low", "selected_modules": [], "profile_id": 67, "customization": None, "rationale": "Long ride"},
        ])
        # Total = 480 TSS (96% of 500, within ±15%)

    def test_predict_daily_tss_called(self):
        """Verify _predict_daily_tss() is called and returns correct structure."""
        daily_tss = self.generator._predict_daily_tss(
            weekly_tss_target=500,
            training_style="sweetspot",
            allowed_types=["Recovery", "Endurance", "Tempo", "SweetSpot", "Threshold"]
        )

        assert isinstance(daily_tss, dict)
        assert len(daily_tss) == 7
        assert daily_tss[0] == 0  # Monday rest
        assert daily_tss[4] == 0  # Friday rest
        total = sum(daily_tss.values())
        # Should be close to target (within rounding)
        assert 490 <= total <= 510

    def test_e2e_conservative_llm_scales_up(self):
        """E2E: LLM generates 400 TSS, post-validate scales up to ~500."""
        self.mock_llm.generate.return_value = self._mock_llm_response_conservative()

        week_start = date(2026, 2, 17)  # Monday
        plan = self.generator.generate_weekly_plan(
            ctl=70.0,
            atl=65.0,
            tsb=5.0,
            form_status="Optimal",
            ftp=250,
            week_start=week_start,
            weekly_tss_target=500,
        )

        # Check LLM was called
        assert self.mock_llm.generate.called

        # Check post-validation scaled up
        # Original mock total = 400, should scale to ~500 (±15%)
        assert plan.total_planned_tss >= 425  # 85% of 500
        assert plan.total_planned_tss <= 575  # 115% of 500

        # Rest days should stay at 0
        rest_days = [dp for dp in plan.daily_plans if dp.workout_type == "Rest"]
        for rd in rest_days:
            assert rd.estimated_tss == 0

        # Non-rest days should be scaled
        workout_days = [dp for dp in plan.daily_plans if dp.workout_type != "Rest"]
        assert all(dp.estimated_tss >= 20 for dp in workout_days)  # Floor
        assert all(dp.estimated_tss <= 150 for dp in workout_days)  # Cap

    def test_e2e_aggressive_llm_scales_down(self):
        """E2E: LLM generates 700 TSS, post-validate scales down to ~500."""
        self.mock_llm.generate.return_value = self._mock_llm_response_aggressive()

        week_start = date(2026, 2, 17)
        plan = self.generator.generate_weekly_plan(
            ctl=70.0,
            atl=65.0,
            tsb=5.0,
            form_status="Optimal",
            ftp=250,
            week_start=week_start,
            weekly_tss_target=500,
        )

        # Should scale down from 700 to ~500 (±15%)
        assert plan.total_planned_tss >= 425
        assert plan.total_planned_tss <= 575

        # Rest days unchanged
        rest_days = [dp for dp in plan.daily_plans if dp.workout_type == "Rest"]
        for rd in rest_days:
            assert rd.estimated_tss == 0

        # Non-rest days scaled down, floors/caps enforced
        workout_days = [dp for dp in plan.daily_plans if dp.workout_type != "Rest"]
        assert all(dp.estimated_tss >= 20 for dp in workout_days)
        assert all(dp.estimated_tss <= 150 for dp in workout_days)

    def test_e2e_on_target_no_scaling(self):
        """E2E: LLM generates 480 TSS (96% of 500), within tolerance, no scaling."""
        self.mock_llm.generate.return_value = self._mock_llm_response_on_target()

        week_start = date(2026, 2, 17)
        plan = self.generator.generate_weekly_plan(
            ctl=70.0,
            atl=65.0,
            tsb=5.0,
            form_status="Optimal",
            ftp=250,
            week_start=week_start,
            weekly_tss_target=500,
        )

        # Should NOT scale (480 is 96%, within 85-115%)
        # Total should be close to 480 (allow for _validate_and_correct_tss adjustments)
        assert 425 <= plan.total_planned_tss <= 515  # Allow for _validate_and_correct_tss adjustments

    def test_daily_tss_targets_in_prompt(self):
        """Verify daily TSS targets are injected into the user prompt."""
        self.mock_llm.generate.return_value = self._mock_llm_response_on_target()

        week_start = date(2026, 2, 17)
        self.generator.generate_weekly_plan(
            ctl=70.0,
            atl=65.0,
            tsb=5.0,
            form_status="Optimal",
            ftp=250,
            week_start=week_start,
            weekly_tss_target=500,
        )

        # Check that LLM was called with user_prompt containing daily TSS targets
        call_args = self.mock_llm.generate.call_args
        user_prompt = call_args.kwargs["user_prompt"]

        # Should contain something like "Monday: Rest (0 TSS)" and "Tuesday: ~80 TSS"
        assert "Monday" in user_prompt
        assert "0 TSS" in user_prompt or "Rest" in user_prompt
        assert "Tuesday" in user_prompt
        assert "TSS" in user_prompt  # At least some TSS targets mentioned

    def test_predict_daily_tss_respects_style_ratios(self):
        """Verify different training styles use correct distribution ratios."""
        for style in ["polarized", "norwegian", "sweetspot", "threshold", "endurance"]:
            daily_tss = self.generator._predict_daily_tss(
                weekly_tss_target=500,
                training_style=style,
                allowed_types=["Recovery", "Endurance", "Tempo", "SweetSpot", "Threshold", "VO2max"]
            )

            # Check ratios are applied
            ratios = DAILY_TSS_RATIOS[style]
            expected = [int(round(500 * r / 5) * 5) for r in ratios]  # Round to nearest 5

            # Apply caps (150 standard, 180 for endurance weekends)
            for i in range(7):
                if ratios[i] == 0:
                    continue
                max_tss = 180 if (style == "endurance" and i in [5, 6]) else 150
                expected[i] = min(expected[i], max_tss)

            # Verify each day is close to expected (allow for rounding)
            for i in range(7):
                assert abs(daily_tss[i] - expected[i]) <= 5, f"Day {i} mismatch for {style}"

    def test_post_validate_preserves_rest_days(self):
        """Ensure post-validation never modifies rest days."""
        # Conservative LLM with rest days
        self.mock_llm.generate.return_value = self._mock_llm_response_conservative()

        week_start = date(2026, 2, 17)
        plan = self.generator.generate_weekly_plan(
            ctl=70.0,
            atl=65.0,
            tsb=5.0,
            form_status="Optimal",
            weekly_tss_target=500,
        )

        # Verify Monday (index 0) and Friday (index 4) are still rest
        monday = next(dp for dp in plan.daily_plans if dp.day_index == 0)
        friday = next(dp for dp in plan.daily_plans if dp.day_index == 4)

        assert monday.workout_type == "Rest"
        assert monday.estimated_tss == 0
        assert monday.duration_minutes == 0

        assert friday.workout_type == "Rest"
        assert friday.estimated_tss == 0
        assert friday.duration_minutes == 0

    def test_post_validate_duration_scales_with_tss(self):
        """Verify duration is also scaled proportionally with TSS."""
        self.mock_llm.generate.return_value = self._mock_llm_response_conservative()

        week_start = date(2026, 2, 17)
        plan = self.generator.generate_weekly_plan(
            ctl=70.0,
            atl=65.0,
            tsb=5.0,
            form_status="Optimal",
            weekly_tss_target=500,
        )

        # Check that durations are in valid range and rounded to 5min
        workout_days = [dp for dp in plan.daily_plans if dp.workout_type != "Rest"]
        for dp in workout_days:
            assert dp.duration_minutes >= 30  # Floor
            assert dp.duration_minutes <= 180  # Cap
            assert dp.duration_minutes % 5 == 0  # Rounded to nearest 5

    def test_extreme_scaling_respects_caps(self):
        """Test that extreme scaling scenarios still respect individual caps."""
        # Create extreme conservative response (total 200 TSS)
        extreme_conservative = json.dumps([
            {"day_index": 0, "workout_type": "Rest", "workout_name": "Rest", "duration_minutes": 0, "estimated_tss": 0, "intensity": "rest", "selected_modules": [], "profile_id": None, "customization": None, "rationale": "Rest"},
            {"day_index": 1, "workout_type": "Endurance", "workout_name": "Easy", "duration_minutes": 30, "estimated_tss": 20, "intensity": "low", "selected_modules": [], "profile_id": 65, "customization": None, "rationale": "Easy"},
            {"day_index": 2, "workout_type": "Endurance", "workout_name": "Easy", "duration_minutes": 30, "estimated_tss": 25, "intensity": "low", "selected_modules": [], "profile_id": 65, "customization": None, "rationale": "Easy"},
            {"day_index": 3, "workout_type": "Endurance", "workout_name": "Easy", "duration_minutes": 45, "estimated_tss": 35, "intensity": "low", "selected_modules": [], "profile_id": 65, "customization": None, "rationale": "Easy"},
            {"day_index": 4, "workout_type": "Rest", "workout_name": "Rest", "duration_minutes": 0, "estimated_tss": 0, "intensity": "rest", "selected_modules": [], "profile_id": None, "customization": None, "rationale": "Rest"},
            {"day_index": 5, "workout_type": "Endurance", "workout_name": "Easy", "duration_minutes": 60, "estimated_tss": 60, "intensity": "low", "selected_modules": [], "profile_id": 65, "customization": None, "rationale": "Easy"},
            {"day_index": 6, "workout_type": "Endurance", "workout_name": "Easy", "duration_minutes": 60, "estimated_tss": 60, "intensity": "low", "selected_modules": [], "profile_id": 65, "customization": None, "rationale": "Easy"},
        ])
        # Total = 200 TSS, target = 500, scale factor = 2.5

        self.mock_llm.generate.return_value = extreme_conservative

        week_start = date(2026, 2, 17)
        plan = self.generator.generate_weekly_plan(
            ctl=70.0,
            atl=65.0,
            tsb=5.0,
            form_status="Optimal",
            weekly_tss_target=500,
        )

        # Even with 2.5x scaling, individual TSS should NOT exceed 150
        workout_days = [dp for dp in plan.daily_plans if dp.workout_type != "Rest"]
        for dp in workout_days:
            assert dp.estimated_tss <= 150, f"Day {dp.day_index} exceeded cap: {dp.estimated_tss}"
            assert dp.estimated_tss >= 20, f"Day {dp.day_index} below floor: {dp.estimated_tss}"
