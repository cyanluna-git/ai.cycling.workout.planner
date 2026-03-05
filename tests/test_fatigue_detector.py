"""Tests for acute fatigue detection (src/services/fatigue_detector.py).

Covers:
- compute_baseline: sufficient data, insufficient data, missing fields, skip-today
- detect_acute_fatigue: HRV drop, RHR rise, both triggers, neither, missing inputs
- FatigueSignal.context_text formatting
"""

import pytest

from src.services.fatigue_detector import (
    FatigueSignal,
    compute_baseline,
    detect_acute_fatigue,
    MIN_BASELINE_ENTRIES,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_wellness(hrv: float = None, rhr: float = None, day_offset: int = 0) -> dict:
    """Build a minimal wellness dict matching Intervals.icu shape."""
    entry: dict = {"id": f"2026-03-{5 - day_offset:02d}"}
    if hrv is not None:
        entry["hrv"] = hrv
    if rhr is not None:
        entry["restingHR"] = rhr
    return entry


def _build_wellness_series(
    n: int,
    hrv: float = 60.0,
    rhr: float = 50.0,
    today_hrv: float = None,
    today_rhr: float = None,
) -> list[dict]:
    """Build a wellness list (newest-first) with N historical entries + today.

    Index 0 = today, index 1..N = historical.
    """
    today = _make_wellness(hrv=today_hrv, rhr=today_rhr, day_offset=0)
    history = [_make_wellness(hrv=hrv, rhr=rhr, day_offset=i + 1) for i in range(n)]
    return [today] + history


# ===========================================================================
# compute_baseline tests
# ===========================================================================

class TestComputeBaseline:

    def test_sufficient_data_returns_averages(self):
        """With >= 7 valid entries, returns mean HRV and RHR."""
        data = _build_wellness_series(10, hrv=60.0, rhr=50.0, today_hrv=45.0, today_rhr=55.0)
        result = compute_baseline(data)
        assert result["hrv_baseline"] == pytest.approx(60.0)
        assert result["rhr_baseline"] == pytest.approx(50.0)

    def test_skips_today_record(self):
        """Index-0 (today) must not affect the baseline."""
        data = _build_wellness_series(7, hrv=60.0, rhr=50.0, today_hrv=10.0, today_rhr=100.0)
        result = compute_baseline(data)
        # Baseline should be 60/50, not skewed by today's extreme values
        assert result["hrv_baseline"] == pytest.approx(60.0)
        assert result["rhr_baseline"] == pytest.approx(50.0)

    def test_insufficient_hrv_entries(self):
        """Fewer than 7 HRV entries -> hrv_baseline is None."""
        data = _build_wellness_series(5, hrv=60.0, rhr=50.0)
        result = compute_baseline(data)
        assert result["hrv_baseline"] is None
        assert result["rhr_baseline"] is None  # Also only 5

    def test_insufficient_rhr_only(self):
        """HRV has enough entries but RHR does not."""
        today = _make_wellness(hrv=50.0, day_offset=0)
        history = []
        for i in range(8):
            entry = _make_wellness(hrv=60.0, day_offset=i + 1)
            if i < 5:
                entry["restingHR"] = 50.0  # Only 5 RHR entries
            history.append(entry)
        data = [today] + history
        result = compute_baseline(data)
        assert result["hrv_baseline"] is not None
        assert result["rhr_baseline"] is None

    def test_empty_wellness_data(self):
        """No wellness data -> both baselines None."""
        result = compute_baseline([])
        assert result["hrv_baseline"] is None
        assert result["rhr_baseline"] is None

    def test_single_entry_only_today(self):
        """Only today's entry, no history."""
        data = [_make_wellness(hrv=60.0, rhr=50.0, day_offset=0)]
        result = compute_baseline(data)
        assert result["hrv_baseline"] is None
        assert result["rhr_baseline"] is None

    def test_mixed_none_values(self):
        """Some entries missing HRV or RHR — counts only non-None."""
        today = _make_wellness(day_offset=0)
        history = []
        for i in range(10):
            # Alternate: even entries have HRV, odd entries have RHR
            if i % 2 == 0:
                history.append(_make_wellness(hrv=60.0, day_offset=i + 1))
            else:
                history.append(_make_wellness(rhr=50.0, day_offset=i + 1))
        data = [today] + history
        result = compute_baseline(data)
        # 5 HRV entries (even indices) < 7 -> None
        assert result["hrv_baseline"] is None
        # 5 RHR entries (odd indices) < 7 -> None
        assert result["rhr_baseline"] is None

    def test_hrvsdnn_fallback(self):
        """When hrv is None but hrvSDNN is present, uses SDNN."""
        today = {"id": "2026-03-05"}
        history = []
        for i in range(8):
            history.append({"id": f"2026-03-{4 - i:02d}", "hrvSDNN": 55.0})
        data = [today] + history
        result = compute_baseline(data)
        assert result["hrv_baseline"] == pytest.approx(55.0)


# ===========================================================================
# detect_acute_fatigue tests
# ===========================================================================

class TestDetectAcuteFatigue:

    def test_hrv_drop_20pct_triggers(self):
        """HRV exactly 20% below baseline triggers fatigue."""
        signal = detect_acute_fatigue(
            today_hrv=48.0, today_rhr=50.0,
            hrv_baseline=60.0, rhr_baseline=50.0,
        )
        assert signal.is_fatigued is True
        assert signal.hrv_drop_pct == pytest.approx(0.20)
        assert signal.rhr_rise_bpm is None  # RHR is fine

    def test_hrv_drop_25pct_triggers(self):
        """HRV 25% below baseline triggers fatigue."""
        signal = detect_acute_fatigue(
            today_hrv=45.0, today_rhr=50.0,
            hrv_baseline=60.0, rhr_baseline=50.0,
        )
        assert signal.is_fatigued is True
        assert signal.hrv_drop_pct == pytest.approx(0.25)

    def test_hrv_drop_19pct_no_trigger(self):
        """HRV 19% drop does NOT trigger fatigue."""
        signal = detect_acute_fatigue(
            today_hrv=48.6, today_rhr=50.0,
            hrv_baseline=60.0, rhr_baseline=50.0,
        )
        assert signal.is_fatigued is False

    def test_rhr_rise_5bpm_triggers(self):
        """RHR exactly +5 bpm from baseline triggers fatigue."""
        signal = detect_acute_fatigue(
            today_hrv=60.0, today_rhr=55.0,
            hrv_baseline=60.0, rhr_baseline=50.0,
        )
        assert signal.is_fatigued is True
        assert signal.rhr_rise_bpm == pytest.approx(5.0)
        assert signal.hrv_drop_pct is None  # HRV is fine

    def test_rhr_rise_8bpm_triggers(self):
        """RHR +8 bpm triggers."""
        signal = detect_acute_fatigue(
            today_hrv=60.0, today_rhr=58.0,
            hrv_baseline=60.0, rhr_baseline=50.0,
        )
        assert signal.is_fatigued is True
        assert signal.rhr_rise_bpm == pytest.approx(8.0)

    def test_rhr_rise_4bpm_no_trigger(self):
        """RHR +4 bpm does NOT trigger."""
        signal = detect_acute_fatigue(
            today_hrv=60.0, today_rhr=54.0,
            hrv_baseline=60.0, rhr_baseline=50.0,
        )
        assert signal.is_fatigued is False

    def test_both_triggers_at_once(self):
        """Both HRV drop and RHR rise trigger simultaneously."""
        signal = detect_acute_fatigue(
            today_hrv=40.0, today_rhr=58.0,
            hrv_baseline=60.0, rhr_baseline=50.0,
        )
        assert signal.is_fatigued is True
        assert signal.hrv_drop_pct is not None
        assert signal.rhr_rise_bpm is not None

    def test_neither_triggers(self):
        """Normal values — no fatigue."""
        signal = detect_acute_fatigue(
            today_hrv=58.0, today_rhr=51.0,
            hrv_baseline=60.0, rhr_baseline=50.0,
        )
        assert signal.is_fatigued is False
        assert signal.hrv_drop_pct is None
        assert signal.rhr_rise_bpm is None

    def test_all_none_inputs(self):
        """All None inputs -> no fatigue."""
        signal = detect_acute_fatigue(None, None, None, None)
        assert signal.is_fatigued is False

    def test_today_hrv_none(self):
        """Today's HRV missing -> skip HRV check, RHR still checked."""
        signal = detect_acute_fatigue(
            today_hrv=None, today_rhr=58.0,
            hrv_baseline=60.0, rhr_baseline=50.0,
        )
        assert signal.is_fatigued is True  # RHR triggers
        assert signal.hrv_drop_pct is None

    def test_today_rhr_none(self):
        """Today's RHR missing -> skip RHR check, HRV still checked."""
        signal = detect_acute_fatigue(
            today_hrv=40.0, today_rhr=None,
            hrv_baseline=60.0, rhr_baseline=50.0,
        )
        assert signal.is_fatigued is True  # HRV triggers
        assert signal.rhr_rise_bpm is None

    def test_hrv_baseline_none(self):
        """No HRV baseline -> skip HRV check."""
        signal = detect_acute_fatigue(
            today_hrv=40.0, today_rhr=50.0,
            hrv_baseline=None, rhr_baseline=50.0,
        )
        assert signal.is_fatigued is False  # RHR normal, HRV skipped

    def test_rhr_baseline_none(self):
        """No RHR baseline -> skip RHR check."""
        signal = detect_acute_fatigue(
            today_hrv=60.0, today_rhr=70.0,
            hrv_baseline=60.0, rhr_baseline=None,
        )
        assert signal.is_fatigued is False  # HRV normal, RHR skipped

    def test_zero_baseline_hrv(self):
        """HRV baseline of 0 -> skip HRV check (avoid division by zero)."""
        signal = detect_acute_fatigue(
            today_hrv=0.0, today_rhr=50.0,
            hrv_baseline=0.0, rhr_baseline=50.0,
        )
        assert signal.is_fatigued is False

    def test_zero_baseline_rhr(self):
        """RHR baseline of 0 -> skip RHR check (guard rhr_baseline > 0)."""
        signal = detect_acute_fatigue(
            today_hrv=60.0, today_rhr=80.0,
            hrv_baseline=60.0, rhr_baseline=0.0,
        )
        # RHR check skipped, HRV normal -> no fatigue
        assert signal.is_fatigued is False
        assert signal.rhr_rise_bpm is None


# ===========================================================================
# FatigueSignal.context_text tests
# ===========================================================================

class TestFatigueSignalContextText:

    def test_not_fatigued_returns_empty(self):
        signal = FatigueSignal(is_fatigued=False)
        assert signal.context_text == ""

    def test_hrv_only_context(self):
        signal = FatigueSignal(
            is_fatigued=True, hrv_drop_pct=0.25,
        )
        text = signal.context_text
        assert "HRV -25%" in text
        assert "Z1/Z2 recovery" in text

    def test_rhr_only_context(self):
        signal = FatigueSignal(
            is_fatigued=True, rhr_rise_bpm=7.0,
        )
        text = signal.context_text
        assert "RHR +7bpm" in text
        assert "Z1/Z2 recovery" in text

    def test_both_in_context(self):
        signal = FatigueSignal(
            is_fatigued=True, hrv_drop_pct=0.30, rhr_rise_bpm=6.0,
        )
        text = signal.context_text
        assert "HRV -30%" in text
        assert "RHR +6bpm" in text

    def test_fatigued_no_detail_fields_fallback(self):
        """is_fatigued=True with no drop/rise fields -> generic fallback text."""
        # This can occur if FatigueSignal is constructed manually (e.g. future
        # extension that sets is_fatigued via a third signal type).
        signal = FatigueSignal(is_fatigued=True)
        text = signal.context_text
        assert "acute fatigue detected" in text
        assert "Z1/Z2 recovery" in text


# ===========================================================================
# Integration: compute_baseline -> detect_acute_fatigue pipeline
# ===========================================================================

class TestEndToEnd:

    def test_full_pipeline_fatigued(self):
        """28-day data with today's HRV drop triggers fatigue."""
        data = _build_wellness_series(
            20, hrv=60.0, rhr=50.0, today_hrv=45.0, today_rhr=50.0,
        )
        baseline = compute_baseline(data)
        signal = detect_acute_fatigue(
            today_hrv=45.0,
            today_rhr=50.0,
            hrv_baseline=baseline["hrv_baseline"],
            rhr_baseline=baseline["rhr_baseline"],
        )
        assert signal.is_fatigued is True
        assert signal.hrv_drop_pct == pytest.approx(0.25)

    def test_full_pipeline_not_fatigued(self):
        """Normal day — no override."""
        data = _build_wellness_series(
            20, hrv=60.0, rhr=50.0, today_hrv=58.0, today_rhr=51.0,
        )
        baseline = compute_baseline(data)
        signal = detect_acute_fatigue(
            today_hrv=58.0,
            today_rhr=51.0,
            hrv_baseline=baseline["hrv_baseline"],
            rhr_baseline=baseline["rhr_baseline"],
        )
        assert signal.is_fatigued is False

    def test_full_pipeline_insufficient_data(self):
        """Only 3 days of history — baseline is None, no fatigue triggered."""
        data = _build_wellness_series(
            3, hrv=60.0, rhr=50.0, today_hrv=30.0, today_rhr=70.0,
        )
        baseline = compute_baseline(data)
        assert baseline["hrv_baseline"] is None
        assert baseline["rhr_baseline"] is None
        signal = detect_acute_fatigue(
            today_hrv=30.0,
            today_rhr=70.0,
            hrv_baseline=baseline["hrv_baseline"],
            rhr_baseline=baseline["rhr_baseline"],
        )
        assert signal.is_fatigued is False
