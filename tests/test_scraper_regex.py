"""
Unit tests for the whatsonzwift scraper: regex parsing, ZWO generation, URL filtering.
"""

import sys
from pathlib import Path

import pytest

# Make scripts/ importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from scrape_whatsonzwift import (
    BLOCKS,
    RAMP_RE,
    STEADY_RE,
    INTERVALS_RE,
    FREE_RIDE_RE,
    SKIP_SLUGS,
    StepPosition,
    calc_duration,
    parse_step_text,
    create_zwo_xml,
)


# -----------------------------------------------------------------------
# calc_duration
# -----------------------------------------------------------------------
class TestCalcDuration:
    def test_seconds_only(self):
        assert calc_duration(None, None, "30") == 30

    def test_minutes_only(self):
        assert calc_duration(None, "5", None) == 300

    def test_hours_only(self):
        assert calc_duration("1", None, None) == 3600

    def test_combined(self):
        assert calc_duration("1", "30", "15") == 5415

    def test_all_none(self):
        assert calc_duration(None, None, None) == 0


# -----------------------------------------------------------------------
# Regex matching — STEADY
# -----------------------------------------------------------------------
class TestSteadyRegex:
    def test_min_and_power(self):
        m = STEADY_RE.match("5min @ 75% FTP")
        assert m is not None
        assert m.group("mins") == "5"
        assert m.group("power") == "75"

    def test_sec_and_power(self):
        m = STEADY_RE.match("30sec @ 120% FTP")
        assert m is not None
        assert m.group("secs") == "30"
        assert m.group("power") == "120"

    def test_min_sec_and_power(self):
        m = STEADY_RE.match("2min 30sec @ 95% FTP")
        assert m is not None
        assert m.group("mins") == "2"
        assert m.group("secs") == "30"
        assert m.group("power") == "95"

    def test_with_cadence(self):
        m = STEADY_RE.match("3min @ 90rpm, 88% FTP")
        assert m is not None
        assert m.group("cadence") == "90"
        assert m.group("power") == "88"

    def test_hour_min_sec(self):
        m = STEADY_RE.match("1hr 15min @ 65% FTP")
        assert m is not None
        assert m.group("hours") == "1"
        assert m.group("mins") == "15"
        assert m.group("power") == "65"

    def test_hour_only(self):
        m = STEADY_RE.match("1hr @ 55% FTP")
        assert m is not None
        assert m.group("hours") == "1"
        assert m.group("power") == "55"


# -----------------------------------------------------------------------
# Regex matching — RAMP
# -----------------------------------------------------------------------
class TestRampRegex:
    def test_basic_ramp(self):
        m = RAMP_RE.match("10min from 25 to 75% FTP")
        assert m is not None
        assert m.group("mins") == "10"
        assert m.group("low") == "25"
        assert m.group("high") == "75"

    def test_ramp_with_cadence(self):
        m = RAMP_RE.match("5min @ 85rpm, from 50 to 100% FTP")
        assert m is not None
        assert m.group("cadence") == "85"
        assert m.group("low") == "50"
        assert m.group("high") == "100"

    def test_ramp_with_sec(self):
        m = RAMP_RE.match("30sec from 80 to 120% FTP")
        assert m is not None
        assert m.group("secs") == "30"

    def test_ramp_with_hours(self):
        m = RAMP_RE.match("1hr from 40 to 70% FTP")
        assert m is not None
        assert m.group("hours") == "1"


# -----------------------------------------------------------------------
# Regex matching — INTERVALS
# -----------------------------------------------------------------------
class TestIntervalsRegex:
    def test_basic_intervals(self):
        m = INTERVALS_RE.match("3x 2min @ 120% FTP, 2min @ 55% FTP")
        assert m is not None
        assert m.group("reps") == "3"
        assert m.group("on_mins") == "2"
        assert m.group("on_power") == "120"
        assert m.group("off_mins") == "2"
        assert m.group("off_power") == "55"

    def test_intervals_sec(self):
        m = INTERVALS_RE.match("8x 30sec @ 150% FTP, 30sec @ 50% FTP")
        assert m is not None
        assert m.group("reps") == "8"
        assert m.group("on_secs") == "30"
        assert m.group("off_secs") == "30"

    def test_intervals_with_cadence(self):
        m = INTERVALS_RE.match("4x 1min @ 100rpm, 110% FTP, 1min @ 80rpm, 55% FTP")
        assert m is not None
        assert m.group("on_cadence") == "100"
        assert m.group("on_power") == "110"
        assert m.group("off_cadence") == "80"
        assert m.group("off_power") == "55"

    def test_intervals_mixed_duration(self):
        m = INTERVALS_RE.match("6x 1min 30sec @ 105% FTP, 2min @ 60% FTP")
        assert m is not None
        assert m.group("on_mins") == "1"
        assert m.group("on_secs") == "30"
        assert m.group("off_mins") == "2"

    def test_intervals_with_hours(self):
        m = INTERVALS_RE.match("2x 1hr @ 80% FTP, 10min @ 50% FTP")
        assert m is not None
        assert m.group("on_hours") == "1"
        assert m.group("off_mins") == "10"


# -----------------------------------------------------------------------
# Regex matching — FREE RIDE
# -----------------------------------------------------------------------
class TestFreeRideRegex:
    def test_basic_free_ride(self):
        m = FREE_RIDE_RE.match("10min free ride")
        assert m is not None
        assert m.group("mins") == "10"

    def test_free_ride_sec(self):
        m = FREE_RIDE_RE.match("30sec free ride")
        assert m is not None
        assert m.group("secs") == "30"

    def test_free_ride_case_insensitive(self):
        m = FREE_RIDE_RE.match("5min Free Ride")
        assert m is not None

    def test_target_ftp_free_ride(self):
        m = FREE_RIDE_RE.match("10min target 75% FTP free ride")
        assert m is not None
        assert m.group("mins") == "10"


# -----------------------------------------------------------------------
# parse_step_text — ZWO node generation
# -----------------------------------------------------------------------
class TestParseStepText:
    def test_steady_node(self):
        node = parse_step_text("5min @ 88% FTP", StepPosition.MIDDLE)
        assert node is not None
        assert node.tag == "SteadyState"
        assert node.get("Duration") == "300"
        assert node.get("Power") == "0.88"

    def test_ramp_warmup(self):
        node = parse_step_text("10min from 25 to 75% FTP", StepPosition.FIRST)
        assert node is not None
        assert node.tag == "Warmup"
        assert node.get("PowerLow") == "0.25"
        assert node.get("PowerHigh") == "0.75"

    def test_ramp_cooldown(self):
        node = parse_step_text("5min from 65 to 40% FTP", StepPosition.LAST)
        assert node is not None
        assert node.tag == "Cooldown"

    def test_ramp_middle(self):
        node = parse_step_text("3min from 80 to 100% FTP", StepPosition.MIDDLE)
        assert node is not None
        assert node.tag == "Ramp"

    def test_intervals_node(self):
        node = parse_step_text("4x 1min @ 120% FTP, 1min @ 55% FTP", StepPosition.MIDDLE)
        assert node is not None
        assert node.tag == "IntervalsT"
        assert node.get("Repeat") == "4"
        assert node.get("OnDuration") == "60"
        assert node.get("OffDuration") == "60"
        assert node.get("OnPower") == "1.2"
        assert node.get("OffPower") == "0.55"

    def test_free_ride_node(self):
        node = parse_step_text("10min free ride", StepPosition.MIDDLE)
        assert node is not None
        assert node.tag == "FreeRide"
        assert node.get("Duration") == "600"

    def test_unparseable_returns_none(self):
        node = parse_step_text("some random text", StepPosition.MIDDLE)
        assert node is None


# -----------------------------------------------------------------------
# create_zwo_xml
# -----------------------------------------------------------------------
class TestCreateZwoXml:
    def test_basic_workout(self):
        steps = [
            "10min from 25 to 75% FTP",
            "20min @ 88% FTP",
            "5min from 65 to 40% FTP",
        ]
        xml = create_zwo_xml("Test Workout", "A test", steps)
        assert xml is not None
        assert "<name>Test Workout</name>" in xml
        assert "<description>A test</description>" in xml
        assert "Warmup" in xml
        assert "SteadyState" in xml
        assert "Cooldown" in xml

    def test_empty_steps_returns_none(self):
        xml = create_zwo_xml("Empty", "", ["random text no FTP"])
        assert xml is None

    def test_intervals_in_xml(self):
        steps = [
            "5min from 25 to 65% FTP",
            "3x 2min @ 110% FTP, 2min @ 55% FTP",
            "5min from 60 to 40% FTP",
        ]
        xml = create_zwo_xml("Intervals", "", steps)
        assert xml is not None
        assert "IntervalsT" in xml
        assert 'Repeat="3"' in xml

    def test_free_ride_in_xml(self):
        steps = [
            "5min from 30 to 60% FTP",
            "10min free ride",
            "5min from 50 to 30% FTP",
        ]
        xml = create_zwo_xml("Free Ride Workout", "", steps)
        assert xml is not None
        assert "FreeRide" in xml


# -----------------------------------------------------------------------
# Collection URL filtering (SKIP_SLUGS)
# -----------------------------------------------------------------------
class TestCollectionFiltering:
    def test_running_is_skipped(self):
        assert "running" in SKIP_SLUGS

    def test_cycling_not_skipped(self):
        # Typical cycling slugs should not be in skip list
        for slug in ["build-me-up", "ftp-builder", "sweetspot", "vo2max"]:
            assert slug not in SKIP_SLUGS

    def test_triathlon_is_skipped(self):
        assert "triathlon" in SKIP_SLUGS


# -----------------------------------------------------------------------
# Interval ordering: INTERVALS_RE must precede STEADY_RE in BLOCKS
# -----------------------------------------------------------------------
class TestBlockOrdering:
    def test_intervals_before_steady(self):
        """INTERVALS_RE must be tried before STEADY_RE to avoid false matches."""
        regexes = [r for r, _ in BLOCKS]
        assert regexes.index(INTERVALS_RE) < regexes.index(STEADY_RE)
