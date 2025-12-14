"""AI Workout Generator.

This module uses LLM to generate cycling workouts based on training metrics
and user profile.
"""

import logging
from dataclasses import dataclass
from datetime import date
from typing import Optional

from ..clients.llm import LLMClient
from ..config import UserProfile
from .data_processor import TrainingMetrics, WellnessMetrics
from .validator import WorkoutValidator, ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class GeneratedWorkout:
    """Generated workout with metadata."""

    name: str
    description: str
    workout_text: str
    estimated_duration_minutes: int
    estimated_tss: Optional[int]
    workout_type: str  # Endurance, Threshold, VO2max, Recovery


# Intervals.icu workout text syntax reference
WORKOUT_SYNTAX_GUIDE = """
Intervals.icu Workout Text Syntax:
- Duration can be in seconds (s), minutes (m), or hours (h)
- Power is expressed as percentage of FTP: 50%, 100%, 115%
- Zones: Z1, Z2, Z3, Z4, Z5, Z6, Z7

Examples:
- 10m 50%         → 10 minutes at 50% FTP (warmup/cooldown)
- 5m Z2           → 5 minutes in Zone 2
- 3m 115%         → 3 minutes at 115% FTP (VO2max)
- 5x 4m 105% 4m 50%  → 5 intervals of 4min at 105%, 4min recovery at 50%
- ramp 10m 50% to 75% → 10 minute ramp from 50% to 75%
- 30s 150%        → 30 second sprint at 150%
"""


SYSTEM_PROMPT = """당신은 세계적인 수준의 사이클링 코치입니다. 데이터 기반의 과학적 훈련을 전문으로 합니다.

핵심 원칙:
1. 선수의 현재 상태(TSB)에 맞는 워크아웃 강도를 처방합니다
2. Intervals.icu 워크아웃 텍스트 포맷을 엄격하게 준수합니다
3. 안전하고 효과적인 훈련만 제안합니다

워크아웃 강도 가이드라인:
- TSB < -20 (매우 피로): Recovery Ride만 권장 (Z1-Z2, 30-45분)
- TSB -20 ~ -10 (피로): Endurance (Z2-Z3, 60분 이내)
- TSB -10 ~ 0 (중립): Tempo 또는 Sweet Spot 가능
- TSB > 0 (회복됨): Threshold 또는 VO2max 인터벌 가능

Zone별 파워 제한 시간:
- Zone 5 (105-120%): 최대 5분 단일 인터벌
- Zone 6 (>120%): 최대 2분 단일 인터벌
- Zone 7 (>150%): 최대 30초 스프린트

{syntax_guide}

출력 형식:
반드시 아래 형식으로만 응답하세요. 추가 설명 없이 워크아웃 텍스트만 출력합니다.

[WORKOUT_NAME]
(워크아웃 이름)

[WORKOUT_TYPE]
(Endurance/Threshold/VO2max/Recovery 중 하나)

[ESTIMATED_TSS]
(예상 TSS 숫자)

[WORKOUT_TEXT]
(Intervals.icu 포맷의 워크아웃 텍스트)
"""


USER_PROMPT_TEMPLATE = """선수 프로필:
- FTP: {ftp}W
- 최대 심박수: {max_hr} bpm
- 젖산역치 심박수: {lthr} bpm
- 훈련 목표: {training_goal}

현재 훈련 상태:
- CTL (체력): {ctl:.1f}
- ATL (피로): {atl:.1f}
- TSB (컨디션): {tsb:.1f} ({form_status})

웰니스 상태:
- 준비 상태: {readiness}
{wellness_details}

오늘 날짜: {today}
요일: {weekday}

위 정보를 바탕으로 오늘에 적합한 사이클링 워크아웃을 생성해주세요.
총 운동 시간은 {max_duration}분 이내로 제한해주세요.
"""


class WorkoutGenerator:
    """Generate AI-powered cycling workouts.

    Uses LLM to create structured workouts based on training metrics,
    wellness data, and user profile.

    Example:
        >>> from src.config import load_config
        >>> from src.clients.llm import LLMClient
        >>>
        >>> config = load_config()
        >>> llm = LLMClient.from_config(config.llm)
        >>> generator = WorkoutGenerator(llm, config.user_profile)
        >>> workout = generator.generate(training_metrics, wellness_metrics)
    """

    def __init__(
        self,
        llm_client: LLMClient,
        user_profile: UserProfile,
        max_duration_minutes: int = 60,
    ):
        """Initialize the workout generator.

        Args:
            llm_client: LLM client for text generation.
            user_profile: User's cycling profile.
            max_duration_minutes: Maximum workout duration (default: 60).
        """
        self.llm = llm_client
        self.profile = user_profile
        self.max_duration = max_duration_minutes
        self.validator = WorkoutValidator(max_duration_minutes=max_duration_minutes * 2)

    def generate(
        self,
        training_metrics: TrainingMetrics,
        wellness_metrics: WellnessMetrics,
        target_date: Optional[date] = None,
    ) -> GeneratedWorkout:
        """Generate a workout based on current training state.

        Args:
            training_metrics: Current CTL/ATL/TSB metrics.
            wellness_metrics: Current wellness status.
            target_date: Date for the workout (default: today).

        Returns:
            GeneratedWorkout with name, description, and workout text.
        """
        target_date = target_date or date.today()

        # Build prompts
        system_prompt = SYSTEM_PROMPT.format(syntax_guide=WORKOUT_SYNTAX_GUIDE)
        user_prompt = self._build_user_prompt(
            training_metrics,
            wellness_metrics,
            target_date,
        )

        logger.info(
            f"Generating workout for {target_date} (TSB: {training_metrics.tsb:.1f})"
        )

        # Generate with LLM
        response = self.llm.generate(system_prompt, user_prompt)

        # Parse response
        workout = self._parse_response(response)

        # Validate workout text
        validation = self.validator.validate(workout.workout_text)

        if not validation.is_valid:
            logger.warning(f"Generated workout has issues: {validation.errors}")
            # Use cleaned text if available
            if validation.cleaned_text:
                workout = GeneratedWorkout(
                    name=workout.name,
                    description=workout.description,
                    workout_text=validation.cleaned_text,
                    estimated_duration_minutes=workout.estimated_duration_minutes,
                    estimated_tss=workout.estimated_tss,
                    workout_type=workout.workout_type,
                )

        if validation.warnings:
            logger.warning(f"Workout warnings: {validation.warnings}")

        logger.info(
            f"Generated: {workout.name} ({workout.workout_type}, ~{workout.estimated_duration_minutes}min)"
        )
        return workout

    def _build_user_prompt(
        self,
        metrics: TrainingMetrics,
        wellness: WellnessMetrics,
        target_date: date,
    ) -> str:
        """Build the user prompt for LLM.

        Args:
            metrics: Training metrics.
            wellness: Wellness metrics.
            target_date: Target date for workout.

        Returns:
            Formatted user prompt.
        """
        # Format wellness details
        wellness_details = []
        if wellness.hrv:
            wellness_details.append(f"- HRV: {wellness.hrv}")
        if wellness.rhr:
            wellness_details.append(f"- 안정시 심박수: {wellness.rhr} bpm")
        if wellness.sleep_hours:
            wellness_details.append(f"- 수면: {wellness.sleep_hours:.1f}시간")

        # Weekday in Korean
        weekdays = [
            "월요일",
            "화요일",
            "수요일",
            "목요일",
            "금요일",
            "토요일",
            "일요일",
        ]
        weekday = weekdays[target_date.weekday()]

        return USER_PROMPT_TEMPLATE.format(
            ftp=self.profile.ftp,
            max_hr=self.profile.max_hr,
            lthr=self.profile.lthr,
            training_goal=self.profile.training_goal,
            ctl=metrics.ctl,
            atl=metrics.atl,
            tsb=metrics.tsb,
            form_status=metrics.form_status,
            readiness=wellness.readiness,
            wellness_details=(
                "\n".join(wellness_details) if wellness_details else "- 데이터 없음"
            ),
            today=target_date.strftime("%Y-%m-%d"),
            weekday=weekday,
            max_duration=self.max_duration,
        )

    def _parse_response(self, response: str) -> GeneratedWorkout:
        """Parse LLM response into GeneratedWorkout.

        Args:
            response: Raw LLM response.

        Returns:
            Parsed GeneratedWorkout.
        """
        # Default values
        name = "AI Generated Workout"
        workout_type = "Endurance"
        estimated_tss = None
        workout_text = ""

        # Parse sections
        sections = {}
        current_section = None
        current_content = []

        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = line[1:-1]
                current_content = []
            elif current_section:
                current_content.append(line)

        # Save last section
        if current_section:
            sections[current_section] = "\n".join(current_content).strip()

        # Extract values
        if "WORKOUT_NAME" in sections:
            name = sections["WORKOUT_NAME"] or name

        if "WORKOUT_TYPE" in sections:
            workout_type = sections["WORKOUT_TYPE"] or workout_type

        if "ESTIMATED_TSS" in sections:
            try:
                estimated_tss = int(sections["ESTIMATED_TSS"])
            except ValueError:
                pass

        if "WORKOUT_TEXT" in sections:
            workout_text = sections["WORKOUT_TEXT"]
        else:
            # Fallback: try to extract workout text directly
            workout_text = response

        # Estimate duration from workout text
        duration = self._estimate_duration(workout_text)

        # Build description
        description = f"AI가 생성한 {workout_type} 워크아웃입니다.\n\n{workout_text}"

        return GeneratedWorkout(
            name=f"AI Generated - {name}",
            description=description,
            workout_text=workout_text,
            estimated_duration_minutes=duration,
            estimated_tss=estimated_tss,
            workout_type=workout_type,
        )

    def _estimate_duration(self, workout_text: str) -> int:
        """Estimate workout duration from text.

        Args:
            workout_text: Workout text to analyze.

        Returns:
            Estimated duration in minutes.
        """
        import re

        total_seconds = 0

        # Find all duration patterns
        duration_pattern = re.compile(r"(\d+)\s*(s|m|h)", re.IGNORECASE)

        for match in duration_pattern.finditer(workout_text):
            value = int(match.group(1))
            unit = match.group(2).lower()

            if unit == "s":
                total_seconds += value
            elif unit == "m":
                total_seconds += value * 60
            elif unit == "h":
                total_seconds += value * 3600

        # Handle intervals (multiplier)
        interval_pattern = re.compile(r"(\d+)\s*x", re.IGNORECASE)
        for match in interval_pattern.finditer(workout_text):
            # Rough estimate: multiply by repetitions
            # This is simplified; actual calculation would need more parsing
            pass

        duration_minutes = max(30, total_seconds // 60)  # Minimum 30 minutes
        return min(duration_minutes, 180)  # Cap at 3 hours
