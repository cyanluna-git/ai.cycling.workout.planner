"""AI Workout Generator.

This module uses LLM to generate cycling workouts based on training metrics
and user profile.
"""

import json
import logging
import re
from dataclasses import dataclass
from datetime import date
from typing import Optional

from ..clients.llm import LLMClient
from ..config import UserProfile
from .data_processor import TrainingMetrics, WellnessMetrics
from .validator import WorkoutValidator, ValidationResult
from .workout_skeleton import WorkoutSkeleton, parse_skeleton_from_dict
from .protocol_builder import ProtocolBuilder, build_intervals_icu_json
from .workout_library import WARMUP_BLOCKS, MAIN_BLOCKS, COOLDOWN_BLOCKS

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
Workout Step Format:
- Time: number + unit (5m = 5 minutes, 30s = 30 seconds, 1h = 1 hour)
- Power: % of FTP (50%, 88%, 100%, 115%)

Step Examples:
- "10m 50%" = 50% FTP for 10 minutes
- "5m 100%" = 100% FTP for 5 minutes
- "30s 120%" = 120% FTP for 30 seconds

Power Zone Guide:
- 50-65%: Z1-Z2 (Recovery/Endurance)
- 75-85%: Z3 (Tempo)
- 88-94%: Z4 (Sweet Spot/Threshold)
- 100-110%: Z5 (VO2max)
- 115%+: Z6 (Anaerobic)
"""

# Legacy system prompt (kept for backward compatibility)
SYSTEM_PROMPT = """You are a world-class cycling coach. Analyze the athlete's condition and prescribe an appropriate workout.

Workout Intensity Guidelines:
- TSB < -20 (Very Fatigued): Recovery only (50-65%, 30-45 mins)
- TSB -20 ~ -10 (Fatigued): Endurance (65-75%, within 60 mins)
- TSB -10 ~ 0 (Neutral): Tempo/Sweet Spot possible
- TSB > 0 (Fresh): Threshold/VO2max possible

{syntax_guide}

**Output Rules (Strictly Adhere):**
You must respond strictly in the JSON format below. Output pure JSON only, without additional explanations or markdown.

```json
{{
  "name": "Workout Name (in English)",
  "type": "One of: Endurance|Threshold|VO2max|Recovery",
  "tss": estimated_tss_number,
  "warmup": ["Step1", "Step2"],
  "main": ["Step1", "Step2", "..."],
  "cooldown": ["Step1"]
}}
```

Example:
```json
{{
  "name": "Sweet Spot Intervals",
  "type": "Threshold",
  "tss": 55,
  "warmup": ["10m 50%"],
  "main": ["5m 88%", "5m 50%", "5m 88%", "5m 50%", "5m 88%", "5m 50%"],
  "cooldown": ["10m 50%"]
}}
```
"""

# Template Refinement Prompt
TEMPLATE_REFINEMENT_PROMPT = """You are an expert cycling coach logic engine.
Your goal is to REFINE a pre-selected workout template to match the athlete's specific condition.

**Input Context:**
1. Athlete Profile & TSB (Training Stress Balance)
2. Selected Base Template (Warmup + Main Set + Cooldown)

**Refinement Rules:**
- **TSB < -20 (Very Fatigued)**: Reduce main set intensity by 5-10%, shorten duration if possible.
- **TSB -10 ~ 0 (Neutral)**: Keep intensity as base or adjust slightly (-2% to +2%).
- **TSB > 10 (Fresh)**: You may increase intensity by 2-5% or add 1-2 reps if duration allows.
- **Warmup/Cooldown**: Generally keep as is, but can shorten if total duration limit is exceeded.
- **Total Duration**: MUST NOT exceed the user's limit ({max_duration} min). Truncate cooldown or remove 1 main set rep if needed.

**Output Format:**
Return the fully constructed JSON with your refinements applied.
The structure MUST match the Skeleton JSON format perfectly.

```json
{{
  "workout_theme": "Refined Name (e.g., 'Ciabatta Adjusted')",
  "workout_type": "...",
  "total_duration_minutes": <int>,
  "estimated_tss": <int>,
  "structure": [ ... refined blocks ... ]
}}
```
"""


USER_PROMPT_TEMPLATE = """Athlete Profile:
- FTP: {ftp}W
- Max HR: {max_hr} bpm
- LTHR: {lthr} bpm
- Training Goal: {training_goal}

Current Training Status:
- CTL (Fitness): {ctl:.1f}
- ATL (Fatigue): {atl:.1f}
- TSB (Form): {tsb:.1f} ({form_status})

Wellness Status:
- Readiness: {readiness}
{wellness_details}

Today's Date: {today}
Day of Week: {weekday}

**User Settings:**
- Target Duration: {max_duration} minutes
- Training Style: {style}
- Intensity Preference: {intensity}
- Environment: {environment}
{user_notes}

Based on the information above, please generate a suitable cycling workout for today.
"""


# Training style descriptions for the prompt
STYLE_DESCRIPTIONS = {
    "auto": "Automatically determined based on TSB status",
    "polarized": "Polarized Training - 80% Easy (Z1-Z2) + 20% Very Hard (Z5-Z6), avoid middle intensity",
    "norwegian": "Norwegian Method - 4x8m or 5x5m Z4 (Threshold) intervals",
    "pyramidal": "Pyramidal - Based on Z1-Z2 with added Z3-Z4, minimize Z5",
    "threshold": "Threshold Focused - Intervals near FTP (95-105%)",
    "sweetspot": "Sweet Spot - Long intervals in 88-94% FTP range",
    "endurance": "Endurance - Z2 focused long distance training",
}

INTENSITY_DESCRIPTIONS = {
    "auto": "Automatically determined based on TSB status",
    "easy": "Easy recovery training (Use Z1-Z2 only)",
    "moderate": "Moderate intensity (Tempo/Sweet Spot allowed)",
    "hard": "High intensity (Threshold/VO2max intervals allowed)",
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

    def generate_enhanced(
        self,
        training_metrics: TrainingMetrics,
        wellness_metrics: WellnessMetrics,
        target_date: Optional[date] = None,
        style: str = "auto",
        notes: str = "",
        intensity: str = "auto",
        indoor: bool = False,
        duration: int = 60,
    ) -> GeneratedWorkout:
        """Generate a workout using enhanced skeleton-based approach.

        Uses protocol types (ramp warmup, classic intervals, step-up, etc.)
        for more varied and structured workouts.

        Args:
            training_metrics: Current CTL/ATL/TSB metrics.
            wellness_metrics: Current wellness status.
            target_date: Date for the workout (default: today).
            style: Training style (auto, polarized, norwegian, etc.).
            notes: Additional user notes/requests.
            intensity: Intensity preference (auto, easy, moderate, hard).
            indoor: If True, generate indoor trainer workout.
            duration: Target duration in minutes (default: 60).

        Returns:
            GeneratedWorkout with name, description, and workout text.
        """
        target_date = target_date or date.today()

        # Get TSB for intensity adjustment
        tsb = training_metrics.tsb if training_metrics.tsb is not None else 0.0

        # Determine intensity based on TSB if auto
        if intensity == "auto" or not intensity:
            if tsb < -20:
                intensity = "easy"
            elif tsb < -10:
                intensity = "easy"
            elif tsb < 5:
                intensity = "moderate"
            else:
                intensity = "hard"

        # Use passed duration
        target_duration = duration

        # Use new modular assembler
        from .workout_assembler import WorkoutAssembler

        assembler = WorkoutAssembler(tsb=tsb, training_goal=self.profile.training_goal)
        assembled_skeleton = assembler.assemble(
            target_duration=target_duration,
            intensity=intensity,
        )

        # Log and convert to skeleton
        logger.info(
            f"Assembled: {assembled_skeleton['workout_theme']} ({assembled_skeleton['total_duration_minutes']} min)"
        )
        print(
            f"[ASSEMBLER] {assembled_skeleton['workout_theme']} - {assembled_skeleton['total_duration_minutes']} min"
        )

        skeleton = parse_skeleton_from_dict(assembled_skeleton)

        # Build Intervals.icu format
        builder = ProtocolBuilder()
        workout_text = builder.build_workout_text(skeleton)
        steps = builder.build_steps(skeleton)

        # Estimate duration from blocks
        duration = skeleton.total_duration_minutes

        logger.info(
            f"Generated enhanced: {skeleton.workout_theme} ({skeleton.workout_type}, ~{duration}min)"
        )

        return GeneratedWorkout(
            name=f"AI Generated - {skeleton.workout_theme}",
            description=workout_text,
            workout_text=workout_text,
            estimated_duration_minutes=duration,
            estimated_tss=skeleton.estimated_tss,
            workout_type=skeleton.workout_type,
        )

    def _build_enhanced_user_prompt(
        self,
        metrics: TrainingMetrics,
        wellness: WellnessMetrics,
        target_date: date,
        style: str = "auto",
        notes: str = "",
        intensity: str = "auto",
        indoor: bool = False,
    ) -> str:
        """Build user prompt for enhanced skeleton generation."""
        # Format wellness details
        wellness_details = []
        if wellness.hrv:
            wellness_details.append(f"- HRV: {wellness.hrv}")
        if wellness.rhr:
            wellness_details.append(f"- RHR: {wellness.rhr} bpm")
        if wellness.sleep_hours:
            wellness_details.append(f"- Sleep: {wellness.sleep_hours:.1f} hours")

        # Weekday in English
        weekdays = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        weekday = weekdays[target_date.weekday()]

        # Get style and intensity descriptions
        style_desc = STYLE_DESCRIPTIONS.get(style, style)
        intensity_desc = INTENSITY_DESCRIPTIONS.get(intensity, intensity)
        environment = "Indoor Trainer" if indoor else "Outdoor or General"

        return f"""Athlete Profile:
- FTP: {self.profile.ftp}W
- Max HR: {self.profile.max_hr} bpm
- Training Goal: {self.profile.training_goal}

Current Training Status:
- CTL (Fitness): {metrics.ctl:.1f}
- ATL (Fatigue): {metrics.atl:.1f}
- TSB (Form): {metrics.tsb:.1f} ({metrics.form_status})

Wellness Status:
- Readiness: {wellness.readiness}
{chr(10).join(wellness_details) if wellness_details else "- No Data"}

Today: {target_date.strftime("%Y-%m-%d")} ({weekday})

Settings:
- Target Duration: {self.max_duration} minutes
- Training Style: {style_desc}
- Intensity: {intensity_desc}
- Environment: {environment}
{f"- Notes: {notes}" if notes else ""}

Generate a structured workout using the appropriate protocol types."""

    def _build_refinement_user_prompt(
        self,
        metrics: TrainingMetrics,
        wellness: WellnessMetrics,
        target_date: date,
        base_template: dict,
        notes: str = "",
    ) -> str:
        """Build user prompt for template refinement."""

        # Format template as clear JSON string
        import json

        template_str = json.dumps(base_template, indent=2)

        return f"""Athlete Profile:
- FTP: {self.profile.ftp}W
- TSB (Form): {metrics.tsb:.1f} ({metrics.form_status})
- Training Goal: {self.profile.training_goal}

Target Date: {target_date}

Selected Base Template:
{template_str}

User Notes: {notes}

Based on the TSB and condition, please REFINE the power/duration values of the above template.
"""

    def _parse_skeleton_response(self, response: str) -> Optional[WorkoutSkeleton]:
        """Parse LLM response into WorkoutSkeleton.

        Args:
            response: Raw LLM response (should be JSON).

        Returns:
            WorkoutSkeleton or None if parsing fails.
        """
        try:
            # Remove markdown code blocks if present
            json_text = response
            if "```json" in json_text:
                match = re.search(r"```json\s*(.*?)\s*```", json_text, re.DOTALL)
                if match:
                    json_text = match.group(1)
            elif "```" in json_text:
                match = re.search(r"```\s*(.*?)\s*```", json_text, re.DOTALL)
                if match:
                    json_text = match.group(1)

            # Parse JSON
            data = json.loads(json_text.strip())

            # Convert to skeleton
            skeleton = parse_skeleton_from_dict(data)

            # Validate
            errors = skeleton.validate()
            if errors:
                logger.warning(f"Skeleton validation issues: {errors}")
                # Still return skeleton, validation is advisory

            logger.info(f"Successfully parsed skeleton: {skeleton.workout_theme}")
            return skeleton

        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Failed to parse skeleton response: {e}")
            logger.debug(f"Response was: {response[:500]}...")
            return None

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
            wellness_details.append(f"- RHR: {wellness.rhr} bpm")
        if wellness.sleep_hours:
            wellness_details.append(f"- Sleep: {wellness.sleep_hours:.1f} hours")

        # Weekday in English
        weekdays = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        weekday = weekdays[target_date.weekday()]

        # Get style and intensity descriptions
        style_desc = STYLE_DESCRIPTIONS.get(style, style)
        intensity_desc = INTENSITY_DESCRIPTIONS.get(intensity, intensity)
        environment = (
            "Indoor Trainer (Structured intervals, short rest)"
            if indoor
            else "Outdoor or General"
        )

        # Format user notes
        user_notes = f"- Additional Requests: {notes}" if notes else ""

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
                "\n".join(wellness_details) if wellness_details else "- No Data"
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
