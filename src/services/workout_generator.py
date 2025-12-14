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


# Intervals.icu workout text syntax reference - UPDATED for proper parsing
WORKOUT_SYNTAX_GUIDE = """
워크아웃 스텝 형식:
- 시간: 숫자 + 단위 (5m = 5분, 30s = 30초, 1h = 1시간)
- 파워: FTP 퍼센트 (50%, 88%, 100%, 115%)

스텝 예시:
- "10m 50%" = 10분간 FTP 50%
- "5m 100%" = 5분간 FTP 100%
- "30s 120%" = 30초간 FTP 120%

파워 존 가이드:
- 50-65%: Z1-Z2 (회복/지구력)
- 75-85%: Z3 (템포)
- 88-94%: Z4 (Sweet Spot/Threshold)
- 100-110%: Z5 (VO2max)
- 115%+: Z6 (무산소)
"""


SYSTEM_PROMPT = """당신은 세계적인 수준의 사이클링 코치입니다. 선수의 상태를 분석하고 적절한 워크아웃을 처방합니다.

워크아웃 강도 가이드라인:
- TSB < -20 (매우 피로): 회복만 (50-65%, 30-45분)
- TSB -20 ~ -10 (피로): 지구력 (65-75%, 60분 이내)
- TSB -10 ~ 0 (중립): 템포/Sweet Spot 가능
- TSB > 0 (회복됨): Threshold/VO2max 가능

{syntax_guide}

**출력 규칙 (엄격히 준수):**
반드시 아래 JSON 형식으로만 응답하세요. 추가 설명이나 마크다운 없이 순수 JSON만 출력합니다.

```json
{{
  "name": "워크아웃 이름 (한국어)",
  "type": "Endurance|Threshold|VO2max|Recovery 중 하나",
  "tss": 예상TSS숫자,
  "warmup": ["스텝1", "스텝2"],
  "main": ["스텝1", "스텝2", "..."],
  "cooldown": ["스텝1"]
}}
```

예시:
```json
{{
  "name": "스윗스팟 인터벌",
  "type": "Threshold",
  "tss": 55,
  "warmup": ["10m 50%"],
  "main": ["5m 88%", "5m 50%", "5m 88%", "5m 50%", "5m 88%", "5m 50%"],
  "cooldown": ["10m 50%"]
}}
```
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

**사용자 설정:**
- 목표 시간: {max_duration}분
- 훈련 스타일: {style}
- 강도 선호: {intensity}
- 환경: {environment}
{user_notes}

위 정보를 바탕으로 오늘에 적합한 사이클링 워크아웃을 생성해주세요.
"""


# Training style descriptions for the prompt
STYLE_DESCRIPTIONS = {
    "auto": "TSB 상태에 맞게 자동 결정",
    "polarized": "양극화 훈련 - 80% 쉬움(Z1-Z2) + 20% 매우 힘듦(Z5-Z6), 중간 강도 회피",
    "norwegian": "노르웨이식 - 4x8분 또는 5x5분 Z4(역치) 인터벌",
    "pyramidal": "피라미드 - Z1-Z2 기반에 Z3-Z4 추가, Z5 최소화",
    "threshold": "역치 중심 - FTP 근처(95-105%) 인터벌",
    "sweetspot": "스윗스팟 - FTP 88-94% 구간에서 긴 인터벌",
    "endurance": "지구력 - Z2 중심 장거리 훈련",
}

INTENSITY_DESCRIPTIONS = {
    "auto": "TSB 상태에 맞게 자동 결정",
    "easy": "쉬운 회복 훈련 (Z1-Z2만 사용)",
    "moderate": "적당한 강도 (템포/스윗스팟 허용)",
    "hard": "높은 강도 (역치/VO2max 인터벌 허용)",
}


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
        style: str = "auto",
        notes: str = "",
        intensity: str = "auto",
        indoor: bool = False,
    ) -> GeneratedWorkout:
        """Generate a workout based on current training state.

        Args:
            training_metrics: Current CTL/ATL/TSB metrics.
            wellness_metrics: Current wellness status.
            target_date: Date for the workout (default: today).
            style: Training style (auto, polarized, norwegian, etc.).
            notes: Additional user notes/requests.
            intensity: Intensity preference (auto, easy, moderate, hard).
            indoor: If True, generate indoor trainer workout.

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
            style=style,
            notes=notes,
            intensity=intensity,
            indoor=indoor,
        )

        logger.info(
            f"Generating workout for {target_date} (TSB: {training_metrics.tsb:.1f})"
        )

        # Generate with LLM
        response = self.llm.generate(system_prompt, user_prompt)

        # Parse response
        workout = self._parse_response(response)

        # Keep original description (for Intervals.icu parsing)
        original_description = workout.description

        # Validate workout text
        validation = self.validator.validate(workout.workout_text)

        if not validation.is_valid:
            logger.warning(f"Generated workout has issues: {validation.errors}")
            # Note: We keep the original description for Intervals.icu
            # The cleaned_text is used for internal workout_text validation only
            # But we don't replace description as it has proper formatting

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
        style: str = "auto",
        notes: str = "",
        intensity: str = "auto",
        indoor: bool = False,
    ) -> str:
        """Build the user prompt for LLM.

        Args:
            metrics: Training metrics.
            wellness: Wellness metrics.
            target_date: Target date for workout.
            style: Training style preference.
            notes: Additional user notes.
            intensity: Intensity preference.
            indoor: Indoor trainer mode.

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

        # Get style and intensity descriptions
        style_desc = STYLE_DESCRIPTIONS.get(style, style)
        intensity_desc = INTENSITY_DESCRIPTIONS.get(intensity, intensity)
        environment = (
            "실내 트레이너 (구조화된 인터벌, 짧은 휴식)" if indoor else "야외 또는 일반"
        )

        # Format user notes
        user_notes = f"- 추가 요청: {notes}" if notes else ""

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
            style=style_desc,
            intensity=intensity_desc,
            environment=environment,
            user_notes=user_notes,
        )

    def _parse_response(self, response: str) -> GeneratedWorkout:
        """Parse LLM JSON response into GeneratedWorkout.

        Args:
            response: Raw LLM response (should be JSON).

        Returns:
            Parsed GeneratedWorkout.
        """
        import json
        import re

        # Default values
        name = "AI Generated Workout"
        workout_type = "Endurance"
        estimated_tss = None
        warmup_steps = []
        main_steps = []
        cooldown_steps = []

        # Try to extract JSON from response
        try:
            # Remove markdown code blocks if present
            json_text = response
            if "```json" in json_text:
                json_match = re.search(r"```json\s*(.*?)\s*```", json_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(1)
            elif "```" in json_text:
                json_match = re.search(r"```\s*(.*?)\s*```", json_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(1)

            # Parse JSON
            data = json.loads(json_text.strip())

            name = data.get("name", name)
            workout_type = data.get("type", workout_type)
            estimated_tss = data.get("tss")
            warmup_steps = data.get("warmup", [])
            main_steps = data.get("main", [])
            cooldown_steps = data.get("cooldown", [])

            logger.info(f"Successfully parsed JSON workout: {name}")

        except (json.JSONDecodeError, Exception) as e:
            logger.warning(
                f"Failed to parse JSON response: {e}. Falling back to text parsing."
            )
            # Fallback: try to extract workout steps from text
            warmup_steps, main_steps, cooldown_steps = self._extract_steps_from_text(
                response
            )

        # Validate and sanitize steps
        warmup_steps = self._validate_steps(warmup_steps)
        main_steps = self._validate_steps(main_steps)
        cooldown_steps = self._validate_steps(cooldown_steps)

        # Build Intervals.icu formatted workout text
        workout_text = self._build_intervals_text(
            warmup_steps, main_steps, cooldown_steps
        )

        # Estimate duration from workout text
        duration = self._estimate_duration(workout_text)

        return GeneratedWorkout(
            name=f"AI Generated - {name}",
            description=workout_text,  # description is the workout text for Intervals.icu
            workout_text=workout_text,
            estimated_duration_minutes=duration,
            estimated_tss=estimated_tss,
            workout_type=workout_type,
        )

    def _validate_steps(self, steps: list) -> list:
        """Validate and sanitize workout steps.

        Args:
            steps: List of step strings.

        Returns:
            List of validated step strings.
        """
        import re

        valid_steps = []
        step_pattern = re.compile(r"^(\d+[smh])\s+(\d+%?)$", re.IGNORECASE)

        for step in steps:
            if not isinstance(step, str):
                continue
            step = step.strip()
            # Remove leading dash if present
            if step.startswith("-"):
                step = step[1:].strip()

            # Check if step matches expected format
            if step_pattern.match(step):
                valid_steps.append(step)
            elif re.match(r"\d+[smh]\s+\d+%", step):
                valid_steps.append(step)
            else:
                logger.warning(f"Invalid step format, skipping: {step}")

        return valid_steps

    def _build_intervals_text(self, warmup: list, main: list, cooldown: list) -> str:
        """Build Intervals.icu formatted workout text.

        Args:
            warmup: List of warmup steps.
            main: List of main set steps.
            cooldown: List of cooldown steps.

        Returns:
            Formatted workout text for Intervals.icu.
        """
        lines = []

        if warmup:
            lines.append("Warmup")
            for step in warmup:
                lines.append(f"- {step}")
            lines.append("")

        if main:
            lines.append("Main Set")
            for step in main:
                lines.append(f"- {step}")
            lines.append("")

        if cooldown:
            lines.append("Cooldown")
            for step in cooldown:
                lines.append(f"- {step}")

        return "\n".join(lines)

    def _extract_steps_from_text(self, text: str) -> tuple:
        """Extract workout steps from free text (fallback).

        Args:
            text: Raw text containing workout steps.

        Returns:
            Tuple of (warmup_steps, main_steps, cooldown_steps).
        """
        import re

        # Extract all steps matching pattern
        step_pattern = re.compile(r"(\d+[smh]\s+\d+%?)", re.IGNORECASE)
        all_steps = step_pattern.findall(text)

        if not all_steps:
            return [], [], []

        # Simple heuristic: first step is warmup, last is cooldown, rest is main
        if len(all_steps) >= 3:
            return [all_steps[0]], all_steps[1:-1], [all_steps[-1]]
        elif len(all_steps) == 2:
            return [], all_steps, []
        else:
            return [], all_steps, []

    def _format_for_intervals(self, text: str) -> str:
        """Format workout text for Intervals.icu parsing.

        Ensures proper structure with Warmup/Main Set/Cooldown headers
        and dash prefixes for each step.

        Args:
            text: Raw workout text.

        Returns:
            Formatted workout text.
        """
        import re

        lines = text.strip().split("\n")
        formatted = []

        # Extract only valid workout lines (e.g., "10m 50%", "5m 88%")
        workout_pattern = re.compile(r"^\s*[-•]?\s*(\d+[smh]\s+\d+%.*)", re.IGNORECASE)

        valid_steps = []
        for line in lines:
            # Skip section headers and empty lines - they'll be rebuilt
            if line.strip().lower() in ["warmup", "main set", "cooldown", ""]:
                continue
            match = workout_pattern.match(line)
            if match:
                step = match.group(1).strip()
                valid_steps.append(step)
            elif re.match(r"^\d+[smh]\s+\d+%", line.strip()):
                valid_steps.append(line.strip())

        if not valid_steps:
            return text  # Return original if no valid steps found

        # Build structured workout
        # First step is warmup, last step is cooldown, rest is main set
        if len(valid_steps) >= 3:
            formatted.append("Warmup")
            formatted.append(f"- {valid_steps[0]}")
            formatted.append("")
            formatted.append("Main Set")
            for step in valid_steps[1:-1]:
                formatted.append(f"- {step}")
            formatted.append("")
            formatted.append("Cooldown")
            formatted.append(f"- {valid_steps[-1]}")
        elif len(valid_steps) == 2:
            formatted.append("Main Set")
            for step in valid_steps:
                formatted.append(f"- {step}")
        else:
            formatted.append("Main Set")
            formatted.append(f"- {valid_steps[0]}")

        return "\n".join(formatted)

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
