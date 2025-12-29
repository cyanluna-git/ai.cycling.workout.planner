"""Data Processor for training metrics.

This module handles the calculation of training load metrics (CTL, ATL, TSB)
and analysis of wellness data.
"""

import logging
from dataclasses import dataclass
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class TrainingMetrics:
    """Training load metrics."""

    ctl: float  # Chronic Training Load (Fitness)
    atl: float  # Acute Training Load (Fatigue)
    tsb: float  # Training Stress Balance (Form)

    @property
    def form_status(self) -> str:
        """Get human-readable form status."""
        if self.tsb < -20:
            return "Very Fatigued"
        elif self.tsb < -10:
            return "Tired"
        elif self.tsb < 0:
            return "Neutral"
        elif self.tsb < 10:
            return "Fresh"
        else:
            return "Very Fresh"


@dataclass
class WellnessMetrics:
    """Wellness metrics summary from Intervals.icu."""

    # Basic metrics
    hrv: Optional[float]  # Heart Rate Variability (RMSSD)
    hrv_sdnn: Optional[float]  # HRV SDNN
    rhr: Optional[float]  # Resting Heart Rate
    sleep_hours: Optional[float]  # Sleep duration
    sleep_score: Optional[float]  # Sleep score (0-100)
    sleep_quality: Optional[int]  # Sleep quality (1-5)
    readiness: str  # Overall readiness assessment

    # Physical state
    weight: Optional[float]  # Weight (kg)
    body_fat: Optional[float]  # Body fat percentage
    vo2max: Optional[float]  # VO2max estimate

    # Subjective ratings (1-5 scale)
    soreness: Optional[int]  # Muscle soreness
    fatigue: Optional[int]  # Fatigue level
    stress: Optional[int]  # Stress level
    mood: Optional[int]  # Mood
    motivation: Optional[int]  # Motivation

    # Health metrics
    spo2: Optional[float]  # Blood oxygen saturation (%)
    systolic: Optional[int]  # Systolic blood pressure (mmHg)
    diastolic: Optional[int]  # Diastolic blood pressure (mmHg)
    respiration: Optional[float]  # Respiration rate (breaths/min)

    # Computed/derived
    readiness_score: Optional[float]  # Computed readiness score (0-100)


class DataProcessor:
    """Process training and wellness data.

    This class calculates training metrics from activity data and
    analyzes wellness data to determine training readiness.

    Example:
        >>> processor = DataProcessor()
        >>> activities = client.get_recent_activities(days=42)
        >>> metrics = processor.calculate_training_metrics(activities)
        >>> print(f"TSB: {metrics.tsb}, Status: {metrics.form_status}")
    """

    def __init__(self, atl_days: int = 7, ctl_days: int = 42):
        """Initialize the data processor.

        Args:
            atl_days: Days for ATL calculation (default: 7).
            ctl_days: Days for CTL calculation (default: 42).
        """
        self.atl_days = atl_days
        self.ctl_days = ctl_days

    def calculate_training_metrics(self, activities: list[dict]) -> TrainingMetrics:
        """Calculate CTL, ATL, and TSB from activity data.

        If activities already contain icu_ctl and icu_atl, uses those.
        Otherwise, calculates from TSS values using exponential moving average.

        Args:
            activities: List of activity objects from Intervals.icu.

        Returns:
            TrainingMetrics with CTL, ATL, and TSB.
        """
        if not activities:
            logger.warning("No activities provided, returning zero metrics")
            return TrainingMetrics(ctl=0, atl=0, tsb=0)

        # Sort activities by date (newest first)
        sorted_activities = sorted(
            activities,
            key=lambda x: x.get("start_date_local", ""),
            reverse=True,
        )

        # Try to use pre-calculated values from latest activity
        latest = sorted_activities[0]
        if "icu_ctl" in latest and "icu_atl" in latest:
            ctl = float(latest.get("icu_ctl") or 0)
            atl = float(latest.get("icu_atl") or 0)
            tsb = ctl - atl
            logger.info(
                f"Using Intervals.icu metrics: CTL={ctl:.1f}, ATL={atl:.1f}, TSB={tsb:.1f}"
            )
            return TrainingMetrics(ctl=ctl, atl=atl, tsb=tsb)

        # Calculate from TSS values
        return self._calculate_from_tss(activities)

    def _calculate_from_tss(self, activities: list[dict]) -> TrainingMetrics:
        """Calculate metrics from TSS values using exponential moving average.

        Args:
            activities: List of activity objects.

        Returns:
            TrainingMetrics calculated from TSS.
        """
        # Extract TSS values (use icu_training_load as TSS)
        tss_values = []
        for activity in activities:
            tss = activity.get("icu_training_load") or activity.get("suffer_score") or 0
            tss_values.append(float(tss))

        # Calculate exponential moving averages
        atl = self._exponential_moving_average(
            tss_values[: self.atl_days], self.atl_days
        )
        ctl = self._exponential_moving_average(
            tss_values[: self.ctl_days], self.ctl_days
        )
        tsb = ctl - atl

        logger.info(f"Calculated metrics: CTL={ctl:.1f}, ATL={atl:.1f}, TSB={tsb:.1f}")
        return TrainingMetrics(ctl=ctl, atl=atl, tsb=tsb)

    def _exponential_moving_average(self, values: list[float], period: int) -> float:
        """Calculate exponential moving average.

        Args:
            values: List of values (newest first).
            period: EMA period in days.

        Returns:
            EMA value.
        """
        if not values:
            return 0.0

        # Pad with zeros if not enough data
        values = values + [0.0] * max(0, period - len(values))

        # Calculate EMA (decay factor = 2 / (period + 1))
        decay = 2 / (period + 1)
        ema = values[0]

        for value in values[1:period]:
            ema = value * decay + ema * (1 - decay)

        return ema

    def analyze_wellness(self, wellness_data: list[dict]) -> WellnessMetrics:
        """Analyze wellness data to determine training readiness.

        Args:
            wellness_data: List of wellness objects from Intervals.icu.

        Returns:
            WellnessMetrics with comprehensive wellness data.
        """
        if not wellness_data:
            logger.warning("No wellness data provided")
            return WellnessMetrics(
                hrv=None,
                hrv_sdnn=None,
                rhr=None,
                sleep_hours=None,
                sleep_score=None,
                sleep_quality=None,
                readiness="Unknown",
                weight=None,
                body_fat=None,
                vo2max=None,
                soreness=None,
                fatigue=None,
                stress=None,
                mood=None,
                motivation=None,
                spo2=None,
                systolic=None,
                diastolic=None,
                respiration=None,
                readiness_score=None,
            )

        # Get latest wellness data
        latest = max(wellness_data, key=lambda x: x.get("id", ""))

        # Basic metrics
        hrv = latest.get("hrv")
        hrv_sdnn = latest.get("hrvSDNN")
        rhr = latest.get("restingHR")
        sleep_secs = latest.get("sleepSecs")
        sleep_hours = sleep_secs / 3600 if sleep_secs else None
        sleep_score = latest.get("sleepScore")
        sleep_quality = latest.get("sleepQuality")

        # Physical state
        weight = latest.get("weight")
        body_fat = latest.get("bodyFat")
        vo2max = latest.get("vo2max")

        # Subjective ratings
        soreness = latest.get("soreness")
        fatigue = latest.get("fatigue")
        stress = latest.get("stress")
        mood = latest.get("mood")
        motivation = latest.get("motivation")

        # Health metrics
        spo2 = latest.get("spO2")
        systolic = latest.get("systolic")
        diastolic = latest.get("diastolic")
        respiration = latest.get("respiration")

        # Readiness score from Intervals.icu (if available)
        readiness_score = latest.get("readiness")

        # Determine readiness text based on available data
        readiness_text = self._assess_readiness(hrv, rhr, sleep_hours, latest)

        # Log summary
        logger.info(
            f"Wellness: HRV={hrv}, RHR={rhr}, Sleep={sleep_hours:.1f}h "
            f"VO2max={vo2max}, Weight={weight}, Readiness={readiness_text}"
            if sleep_hours
            else f"Wellness: HRV={hrv}, RHR={rhr}, Sleep=N/A, "
            f"VO2max={vo2max}, Weight={weight}, Readiness={readiness_text}"
        )

        return WellnessMetrics(
            hrv=hrv,
            hrv_sdnn=hrv_sdnn,
            rhr=rhr,
            sleep_hours=sleep_hours,
            sleep_score=sleep_score,
            sleep_quality=sleep_quality,
            readiness=readiness_text,
            weight=weight,
            body_fat=body_fat,
            vo2max=vo2max,
            soreness=soreness,
            fatigue=fatigue,
            stress=stress,
            mood=mood,
            motivation=motivation,
            spo2=spo2,
            systolic=systolic,
            diastolic=diastolic,
            respiration=respiration,
            readiness_score=readiness_score,
        )

    def _assess_readiness(
        self,
        hrv: Optional[float],
        rhr: Optional[float],
        sleep_hours: Optional[float],
        wellness: dict,
    ) -> str:
        """Assess training readiness from wellness data.

        Args:
            hrv: Heart rate variability.
            rhr: Resting heart rate.
            sleep_hours: Hours of sleep.
            wellness: Full wellness object for additional data.

        Returns:
            Readiness assessment string.
        """
        # Check for soreness/fatigue indicators
        soreness = wellness.get("soreness", 0)
        fatigue = wellness.get("fatigue", 0)

        # Simple heuristic scoring
        score = 0

        # Sleep assessment
        if sleep_hours:
            if sleep_hours >= 7:
                score += 2
            elif sleep_hours >= 6:
                score += 1
            else:
                score -= 1

        # Soreness/fatigue assessment (lower is better in Intervals.icu)
        if soreness and soreness > 3:
            score -= 1
        if fatigue and fatigue > 3:
            score -= 1

        # Map score to readiness
        if score >= 2:
            return "Good - Ready for hard training"
        elif score >= 0:
            return "Moderate - Consider moderate intensity"
        else:
            return "Poor - Recovery recommended"

    def check_existing_workout(
        self,
        events: list[dict],
        target_date: date,
    ) -> Optional[dict]:
        """Check if a workout already exists for the target date.

        Args:
            events: List of calendar events.
            target_date: Date to check.

        Returns:
            Existing workout event if found, None otherwise.
        """
        target_str = target_date.strftime("%Y-%m-%d")

        for event in events:
            event_date = event.get("start_date_local", "")[:10]
            if event_date == target_str and event.get("category") == "WORKOUT":
                logger.info(
                    f"Found existing workout on {target_str}: {event.get('name')}"
                )
                return event

        return None
