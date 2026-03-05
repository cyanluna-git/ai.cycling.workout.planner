"""Acute fatigue detection from wellness data.

Detects HRV drops and RHR elevations relative to a rolling baseline,
signaling when workout intensity should be forced to Z1/Z2 recovery.
"""

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# Thresholds
HRV_DROP_THRESHOLD = 0.20  # 20% drop from baseline triggers override
RHR_RISE_THRESHOLD = 5  # +5 bpm from baseline triggers override
MIN_BASELINE_ENTRIES = 7  # Need at least 7 valid entries for a reliable baseline


@dataclass
class FatigueSignal:
    """Result of acute fatigue detection."""

    is_fatigued: bool
    hrv_drop_pct: Optional[float] = None  # e.g. 0.25 means 25% drop
    rhr_rise_bpm: Optional[float] = None  # e.g. 7.0 means +7 bpm
    hrv_baseline: Optional[float] = None
    rhr_baseline: Optional[float] = None
    today_hrv: Optional[float] = None
    today_rhr: Optional[float] = None

    @property
    def context_text(self) -> str:
        """Build human-readable fatigue context for LLM prompt injection."""
        if not self.is_fatigued:
            return ""

        parts = []
        if self.hrv_drop_pct is not None:
            parts.append(f"HRV -{self.hrv_drop_pct:.0%} from baseline")
        if self.rhr_rise_bpm is not None:
            parts.append(f"RHR +{self.rhr_rise_bpm:.0f}bpm from baseline")

        detail = " / ".join(parts) if parts else "acute fatigue detected"
        return (
            f"WARNING: Acute fatigue override: {detail}. "
            f"Forcing Z1/Z2 recovery session."
        )


def compute_baseline(
    wellness_data: list[dict],
) -> dict:
    """Compute 28-day rolling baseline for HRV and RHR.

    Expects wellness_data sorted newest-first (index 0 = today).
    Skips today's record (index 0) so today's values are compared
    against historical averages, not included in them.

    Args:
        wellness_data: List of Intervals.icu wellness dicts, newest first.

    Returns:
        Dict with 'hrv_baseline' and 'rhr_baseline' (float or None).
        Returns None for a metric if fewer than MIN_BASELINE_ENTRIES
        valid entries exist.
    """
    hrv_values: list[float] = []
    rhr_values: list[float] = []

    # Skip index 0 (today) — use indices 1..N for baseline
    for entry in wellness_data[1:]:
        hrv = entry.get("hrv")
        if hrv is None:
            # Fallback to SDNN if RMSSD not available
            hrv = entry.get("hrvSDNN")
        if hrv is not None:
            hrv_values.append(float(hrv))

        rhr = entry.get("restingHR")
        if rhr is not None:
            rhr_values.append(float(rhr))

    hrv_baseline = (
        sum(hrv_values) / len(hrv_values)
        if len(hrv_values) >= MIN_BASELINE_ENTRIES
        else None
    )
    rhr_baseline = (
        sum(rhr_values) / len(rhr_values)
        if len(rhr_values) >= MIN_BASELINE_ENTRIES
        else None
    )

    logger.info(
        f"Fatigue baseline: HRV={hrv_baseline:.1f} ({len(hrv_values)} entries)"
        if hrv_baseline
        else f"Fatigue baseline: HRV=N/A ({len(hrv_values)} entries)"
    )
    logger.info(
        f"Fatigue baseline: RHR={rhr_baseline:.1f} ({len(rhr_values)} entries)"
        if rhr_baseline
        else f"Fatigue baseline: RHR=N/A ({len(rhr_values)} entries)"
    )

    return {
        "hrv_baseline": hrv_baseline,
        "rhr_baseline": rhr_baseline,
    }


def detect_acute_fatigue(
    today_hrv: Optional[float],
    today_rhr: Optional[float],
    hrv_baseline: Optional[float],
    rhr_baseline: Optional[float],
) -> FatigueSignal:
    """Detect acute fatigue by comparing today's metrics against baseline.

    Rules:
    - HRV drop >= 20% from baseline -> fatigued
    - RHR rise >= 5 bpm from baseline -> fatigued
    - Either condition alone is sufficient
    - Missing data (None) for any input -> that check is skipped

    Args:
        today_hrv: Today's HRV value (RMSSD or SDNN).
        today_rhr: Today's resting heart rate (bpm).
        hrv_baseline: 28-day average HRV (excluding today).
        rhr_baseline: 28-day average RHR (excluding today).

    Returns:
        FatigueSignal with detection result and details.
    """
    hrv_drop_pct: Optional[float] = None
    rhr_rise_bpm: Optional[float] = None
    is_fatigued = False

    # HRV check: drop >= 20%
    if hrv_baseline and today_hrv is not None and hrv_baseline > 0:
        hrv_drop_pct = (hrv_baseline - today_hrv) / hrv_baseline
        if hrv_drop_pct >= HRV_DROP_THRESHOLD:
            is_fatigued = True
            logger.warning(
                f"Acute fatigue: HRV drop {hrv_drop_pct:.0%} "
                f"(today={today_hrv}, baseline={hrv_baseline:.1f})"
            )
        else:
            # Not a significant drop — clear the pct so it's not confusing
            hrv_drop_pct = None

    # RHR check: rise >= 5 bpm
    if rhr_baseline and today_rhr is not None and rhr_baseline > 0:
        rhr_rise_bpm = today_rhr - rhr_baseline
        if rhr_rise_bpm >= RHR_RISE_THRESHOLD:
            is_fatigued = True
            logger.warning(
                f"Acute fatigue: RHR rise {rhr_rise_bpm:.0f}bpm "
                f"(today={today_rhr}, baseline={rhr_baseline:.1f})"
            )
        else:
            # Not a significant rise — clear
            rhr_rise_bpm = None

    if not is_fatigued:
        logger.info("No acute fatigue detected")

    return FatigueSignal(
        is_fatigued=is_fatigued,
        hrv_drop_pct=hrv_drop_pct,
        rhr_rise_bpm=rhr_rise_bpm,
        hrv_baseline=hrv_baseline,
        rhr_baseline=rhr_baseline,
        today_hrv=today_hrv,
        today_rhr=today_rhr,
    )
