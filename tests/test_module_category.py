"""Tests for module category detection accuracy.

Ensures no key collisions between warmup/cooldown modules
and that get_module_category returns correct categories.
"""
import pytest
from src.services.workout_modules import (
    WARMUP_MODULES,
    MAIN_SEGMENTS,
    REST_SEGMENTS,
    COOLDOWN_MODULES,
    ALL_MODULES,
    get_module_category,
)


class TestModuleKeyUniqueness:
    """Ensure no key collisions across module categories."""

    def test_no_warmup_cooldown_key_collision(self):
        overlap = set(WARMUP_MODULES.keys()) & set(COOLDOWN_MODULES.keys())
        assert overlap == set(), f"Warmup/Cooldown key collision: {overlap}"

    def test_no_warmup_main_key_collision(self):
        overlap = set(WARMUP_MODULES.keys()) & set(MAIN_SEGMENTS.keys())
        assert overlap == set(), f"Warmup/Main key collision: {overlap}"

    def test_no_cooldown_main_key_collision(self):
        overlap = set(COOLDOWN_MODULES.keys()) & set(MAIN_SEGMENTS.keys())
        assert overlap == set(), f"Cooldown/Main key collision: {overlap}"

    def test_all_modules_count_matches_sum(self):
        """ALL_MODULES should contain all modules (no overwrites)."""
        total = len(WARMUP_MODULES) + len(MAIN_SEGMENTS) + len(REST_SEGMENTS) + len(COOLDOWN_MODULES)
        assert len(ALL_MODULES) == total, (
            f"ALL_MODULES has {len(ALL_MODULES)} entries but sum is {total}. "
            "Key collision detected!"
        )


class TestGetModuleCategory:
    """Ensure get_module_category returns correct categories."""

    def test_warmup_modules(self):
        for key in WARMUP_MODULES:
            assert get_module_category(key) == "Warmup", f"{key} should be Warmup"

    def test_cooldown_modules(self):
        for key in COOLDOWN_MODULES:
            assert get_module_category(key) == "Cooldown", f"{key} should be Cooldown"

    def test_main_modules(self):
        for key in MAIN_SEGMENTS:
            cat = get_module_category(key)
            assert cat == "Main", f"{key} should be Main, got {cat}"

    def test_rest_modules(self):
        for key in REST_SEGMENTS:
            cat = get_module_category(key)
            assert cat == "Rest", f"{key} should be Rest, got {cat}"

    def test_unknown_module(self):
        assert get_module_category("nonexistent_xyz") == "Unknown"

    def test_ramp_standard_is_warmup(self):
        """Regression test: ramp_standard must be Warmup, not Cooldown."""
        assert get_module_category("ramp_standard") == "Warmup"

    def test_ramp_short_is_warmup(self):
        """Regression test: ramp_short must be Warmup, not Cooldown."""
        assert get_module_category("ramp_short") == "Warmup"

    def test_cooldown_ramp_variants_are_cooldown(self):
        """Cooldown ramp variants should be Cooldown."""
        assert get_module_category("cooldown_ramp_standard") == "Cooldown"
        assert get_module_category("cooldown_ramp_short") == "Cooldown"
