"""Tests for TSS prediction and post-validation logic."""

import pytest
from datetime import date
from unittest.mock import Mock

from api.services.weekly_plan_service import (
    WeeklyPlanGenerator,
    DailyPlan,
    DAILY_TSS_RATIOS,
)


def _make_generator(user_profile: dict) -> WeeklyPlanGenerator:
    """Helper to create a generator with mocked LLM."""
    mock_llm = Mock()
    return WeeklyPlanGenerator(llm_client=mock_llm, user_profile=user_profile)


class TestPredictDailyTss:
    """Tests for _predict_daily_tss method."""

    def test_predict_daily_tss_sum_matches_target(self):
        """Verify ratios sum approximately matches target."""
        gen = _make_generator({"training_style": "polarized"})
        weekly_target = 500
        
        daily_targets = gen._predict_daily_tss(
            weekly_tss_target=weekly_target,
            training_style="polarized",
            allowed_types=["Recovery", "Endurance", "VO2max"],
        )
        
        # Check we have 7 days
        assert len(daily_targets) == 7
        
        # Sum should be close to target (within rounding)
        total = sum(daily_targets.values())
        assert abs(total - weekly_target) <= 35  # Allow for rounding and caps
        
        # Monday and Friday should be rest (0 TSS) for polarized
        assert daily_targets[0] == 0  # Monday
        assert daily_targets[4] == 0  # Friday

    def test_predict_daily_tss_caps(self):
        """Verify individual day cap of 150 TSS (180 for endurance weekends)."""
        gen = _make_generator({"training_style": "polarized"})
        
        # Very high weekly target to test caps
        daily_targets = gen._predict_daily_tss(
            weekly_tss_target=1200,
            training_style="polarized",
            allowed_types=["Recovery", "Endurance", "VO2max"],
        )
        
        # No non-rest day should exceed 150 for polarized
        for day_idx, tss in daily_targets.items():
            if tss > 0:
                assert tss <= 150, f"Day {day_idx} exceeded 150 TSS cap: {tss}"

    def test_predict_daily_tss_endurance_weekend_cap(self):
        """Verify endurance weekend days can reach 180 TSS."""
        gen = _make_generator({"training_style": "endurance"})
        
        # High weekly target
        daily_targets = gen._predict_daily_tss(
            weekly_tss_target=1000,
            training_style="endurance",
            allowed_types=["Recovery", "Endurance", "Tempo"],
        )
        
        # Weekend days (Sat=5, Sun=6) can be up to 180
        assert daily_targets[5] <= 180
        assert daily_targets[6] <= 180
        
        # Weekday caps still 150
        for day_idx in [1, 2, 3]:  # Tue, Wed, Thu
            if daily_targets[day_idx] > 0:
                assert daily_targets[day_idx] <= 150

    def test_predict_daily_tss_rounding(self):
        """Verify TSS is rounded to nearest 5."""
        gen = _make_generator({"training_style": "sweetspot"})
        
        daily_targets = gen._predict_daily_tss(
            weekly_tss_target=487,  # Odd number to test rounding
            training_style="sweetspot",
            allowed_types=["Recovery", "Endurance", "SweetSpot"],
        )
        
        # All non-zero values should be multiples of 5
        for tss in daily_targets.values():
            if tss > 0:
                assert tss % 5 == 0, f"TSS {tss} not rounded to nearest 5"


class TestPostValidateWeeklyTss:
    """Tests for _post_validate_weekly_tss method."""

    def test_post_validate_scales_up(self):
        """Total 400, target 500 → scales up."""
        gen = _make_generator({"training_style": "sweetspot"})
        
        # Create daily plans with total TSS = 400
        daily_plans = [
            DailyPlan(
                day_index=0, day_name="Monday", workout_date=date(2026, 2, 17),
                workout_type="Rest", workout_name="Rest", duration_minutes=0,
                estimated_tss=0, intensity="rest", selected_modules=[], rationale=""
            ),
            DailyPlan(
                day_index=1, day_name="Tuesday", workout_date=date(2026, 2, 18),
                workout_type="Endurance", workout_name="Easy Ride", duration_minutes=60,
                estimated_tss=50, intensity="easy", selected_modules=[], rationale=""
            ),
            DailyPlan(
                day_index=2, day_name="Wednesday", workout_date=date(2026, 2, 19),
                workout_type="SweetSpot", workout_name="SS", duration_minutes=60,
                estimated_tss=80, intensity="hard", selected_modules=[], rationale=""
            ),
            DailyPlan(
                day_index=3, day_name="Thursday", workout_date=date(2026, 2, 20),
                workout_type="Endurance", workout_name="Easy", duration_minutes=60,
                estimated_tss=50, intensity="easy", selected_modules=[], rationale=""
            ),
            DailyPlan(
                day_index=4, day_name="Friday", workout_date=date(2026, 2, 21),
                workout_type="Rest", workout_name="Rest", duration_minutes=0,
                estimated_tss=0, intensity="rest", selected_modules=[], rationale=""
            ),
            DailyPlan(
                day_index=5, day_name="Saturday", workout_date=date(2026, 2, 22),
                workout_type="Threshold", workout_name="FTP", duration_minutes=75,
                estimated_tss=100, intensity="hard", selected_modules=[], rationale=""
            ),
            DailyPlan(
                day_index=6, day_name="Sunday", workout_date=date(2026, 2, 23),
                workout_type="Endurance", workout_name="Long", duration_minutes=120,
                estimated_tss=120, intensity="moderate", selected_modules=[], rationale=""
            ),
        ]
        
        # Total = 400, target = 500
        validated = gen._post_validate_weekly_tss(daily_plans, 500)
        
        # Total should be closer to 500
        new_total = sum(dp.estimated_tss for dp in validated)
        assert new_total > 400  # Scaled up
        assert 475 <= new_total <= 525  # Within reasonable range of target

    def test_post_validate_scales_down(self):
        """Total 700, target 500 → scales down."""
        gen = _make_generator({"training_style": "threshold"})
        
        # Create daily plans with total TSS = 700
        daily_plans = [
            DailyPlan(
                day_index=0, day_name="Monday", workout_date=date(2026, 2, 17),
                workout_type="Rest", workout_name="Rest", duration_minutes=0,
                estimated_tss=0, intensity="rest", selected_modules=[], rationale=""
            ),
            DailyPlan(
                day_index=1, day_name="Tuesday", workout_date=date(2026, 2, 18),
                workout_type="Threshold", workout_name="FTP", duration_minutes=75,
                estimated_tss=100, intensity="hard", selected_modules=[], rationale=""
            ),
            DailyPlan(
                day_index=2, day_name="Wednesday", workout_date=date(2026, 2, 19),
                workout_type="Endurance", workout_name="Easy", duration_minutes=60,
                estimated_tss=50, intensity="easy", selected_modules=[], rationale=""
            ),
            DailyPlan(
                day_index=3, day_name="Thursday", workout_date=date(2026, 2, 20),
                workout_type="Threshold", workout_name="FTP", duration_minutes=90,
                estimated_tss=120, intensity="hard", selected_modules=[], rationale=""
            ),
            DailyPlan(
                day_index=4, day_name="Friday", workout_date=date(2026, 2, 21),
                workout_type="Rest", workout_name="Rest", duration_minutes=0,
                estimated_tss=0, intensity="rest", selected_modules=[], rationale=""
            ),
            DailyPlan(
                day_index=5, day_name="Saturday", workout_date=date(2026, 2, 22),
                workout_type="Threshold", workout_name="FTP Long", duration_minutes=120,
                estimated_tss=150, intensity="hard", selected_modules=[], rationale=""
            ),
            DailyPlan(
                day_index=6, day_name="Sunday", workout_date=date(2026, 2, 23),
                workout_type="Endurance", workout_name="Recovery Long", duration_minutes=180,
                estimated_tss=280, intensity="moderate", selected_modules=[], rationale=""
            ),
        ]
        
        # Total = 700, target = 500
        validated = gen._post_validate_weekly_tss(daily_plans, 500)
        
        # Total should be closer to 500
        new_total = sum(dp.estimated_tss for dp in validated)
        assert new_total < 700  # Scaled down
        # Note: With 150 cap, might not hit exactly 500
        assert 440 <= new_total <= 560

    def test_post_validate_within_tolerance(self):
        """Total 480, target 500 → no change (within ±15%)."""
        gen = _make_generator({"training_style": "polarized"})
        
        # Create daily plans with total TSS = 480
        daily_plans = [
            DailyPlan(
                day_index=0, day_name="Monday", workout_date=date(2026, 2, 17),
                workout_type="Rest", workout_name="Rest", duration_minutes=0,
                estimated_tss=0, intensity="rest", selected_modules=[], rationale=""
            ),
            DailyPlan(
                day_index=1, day_name="Tuesday", workout_date=date(2026, 2, 18),
                workout_type="Endurance", workout_name="Easy", duration_minutes=60,
                estimated_tss=50, intensity="easy", selected_modules=[], rationale=""
            ),
            DailyPlan(
                day_index=2, day_name="Wednesday", workout_date=date(2026, 2, 19),
                workout_type="VO2max", workout_name="Intervals", duration_minutes=60,
                estimated_tss=80, intensity="hard", selected_modules=[], rationale=""
            ),
            DailyPlan(
                day_index=3, day_name="Thursday", workout_date=date(2026, 2, 20),
                workout_type="Endurance", workout_name="Easy", duration_minutes=45,
                estimated_tss=40, intensity="easy", selected_modules=[], rationale=""
            ),
            DailyPlan(
                day_index=4, day_name="Friday", workout_date=date(2026, 2, 21),
                workout_type="Rest", workout_name="Rest", duration_minutes=0,
                estimated_tss=0, intensity="rest", selected_modules=[], rationale=""
            ),
            DailyPlan(
                day_index=5, day_name="Saturday", workout_date=date(2026, 2, 22),
                workout_type="Endurance", workout_name="Long Z2", duration_minutes=150,
                estimated_tss=150, intensity="moderate", selected_modules=[], rationale=""
            ),
            DailyPlan(
                day_index=6, day_name="Sunday", workout_date=date(2026, 2, 23),
                workout_type="Endurance", workout_name="Long Z2", duration_minutes=120,
                estimated_tss=160, intensity="moderate", selected_modules=[], rationale=""
            ),
        ]
        
        # Total = 480, target = 500 (480/500 = 0.96, within 0.85-1.15)
        original_total = sum(dp.estimated_tss for dp in daily_plans)
        validated = gen._post_validate_weekly_tss(daily_plans, 500)
        
        # Should not change
        new_total = sum(dp.estimated_tss for dp in validated)
        assert new_total == original_total

    def test_post_validate_skips_rest_days(self):
        """Rest days stay at 0 TSS when scaling."""
        gen = _make_generator({"training_style": "sweetspot"})
        
        # Create daily plans with rest days
        daily_plans = [
            DailyPlan(
                day_index=0, day_name="Monday", workout_date=date(2026, 2, 17),
                workout_type="Rest", workout_name="Rest", duration_minutes=0,
                estimated_tss=0, intensity="rest", selected_modules=[], rationale=""
            ),
            DailyPlan(
                day_index=1, day_name="Tuesday", workout_date=date(2026, 2, 18),
                workout_type="SweetSpot", workout_name="SS", duration_minutes=60,
                estimated_tss=60, intensity="hard", selected_modules=[], rationale=""
            ),
            DailyPlan(
                day_index=4, day_name="Friday", workout_date=date(2026, 2, 21),
                workout_type="Rest", workout_name="Rest", duration_minutes=0,
                estimated_tss=0, intensity="rest", selected_modules=[], rationale=""
            ),
        ]
        
        # Will trigger scaling (total 60, target 200)
        validated = gen._post_validate_weekly_tss(daily_plans, 200)
        
        # Rest days should remain 0
        rest_days = [dp for dp in validated if dp.workout_type == "Rest"]
        for dp in rest_days:
            assert dp.estimated_tss == 0
            assert dp.duration_minutes == 0

    def test_post_validate_respects_caps(self):
        """Individual TSS capped at 150 even when scaling up."""
        gen = _make_generator({"training_style": "threshold"})
        
        daily_plans = [
            DailyPlan(
                day_index=1, day_name="Tuesday", workout_date=date(2026, 2, 18),
                workout_type="Threshold", workout_name="FTP", duration_minutes=90,
                estimated_tss=140, intensity="hard", selected_modules=[], rationale=""
            ),
        ]
        
        # Target much higher to force aggressive scaling
        validated = gen._post_validate_weekly_tss(daily_plans, 300)
        
        # Should cap at 150
        assert validated[0].estimated_tss <= 150
