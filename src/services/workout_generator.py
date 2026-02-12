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
from ..constants import WORKOUT_PREFIX, WORKOUT_FALLBACK_NAME
from .data_processor import TrainingMetrics, WellnessMetrics
from .validator import WorkoutValidator, ValidationResult
from .workout_skeleton import WorkoutSkeleton, parse_skeleton_from_dict
from .protocol_builder import ProtocolBuilder, build_intervals_icu_json
from .workout_library import WARMUP_BLOCKS, MAIN_BLOCKS, COOLDOWN_BLOCKS
from .workout_modules import get_module_inventory_text
from .prompts import (
    MODULE_SELECTOR_SYSTEM,
    MODULE_SELECTOR_USER,
    MODULE_SELECTOR_PROMPT,  # backward compat
    STYLE_DESCRIPTIONS,
    INTENSITY_DESCRIPTIONS,
)

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
    design_goal: Optional[str] = None
    steps: Optional[list] = None  # Structured steps for API


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

    def _select_modules_with_llm(
        self,
        tsb: float,
        form: str,
        duration: int,
        goal: str,
        intensity: str = "moderate",
        weekly_tss: int = 0,
        yesterday_load: int = 0,
        exclude_barcode: bool = False,
        ftp: int = 0,
        weight: float = 0,
        indoor: bool = False,
        weekday: str = "",
        wellness_text: str = "",
    ) -> dict:
        """Use LLM to select module keys from inventory."""
        inventory_text = get_module_inventory_text(exclude_barcode=exclude_barcode, intensity=intensity)

        # Get balance hints for variety enforcement
        try:
            from .module_usage_tracker import get_tracker
            from .workout_modules import get_filtered_modules

            tracker = get_tracker()
            warmup, main, rest, cooldown = get_filtered_modules(exclude_barcode)

            available_modules = {
                "warmup": list(warmup.keys()),
                "main": list(main.keys()),
                "rest": list(rest.keys()),
                "cooldown": list(cooldown.keys()),
            }
            balance_hints = tracker.get_balance_hints(available_modules, top_n=3)
            logger.info(f"Generated balance hints for AI:\n{balance_hints}")
        except Exception as e:
            logger.warning(f"Failed to generate balance hints: {e}")
            balance_hints = "  (No usage data available)"

        environment = "Indoor Trainer" if indoor else "Outdoor"
        system_prompt = MODULE_SELECTOR_SYSTEM
        user_prompt = MODULE_SELECTOR_USER.format(
            module_inventory=inventory_text,
            ftp=ftp or "N/A",
            weight=weight or "N/A",
            environment=environment,
            weekday=weekday or "N/A",
            wellness_text=wellness_text or "No data available",
            tsb=tsb,
            form=form,
            weekly_tss=weekly_tss,
            yesterday_load=yesterday_load,
            duration=duration,
            goal=goal,
            intensity=intensity,
            balance_hints=balance_hints,
        )

        response = self.llm.generate(
            system_prompt=system_prompt, user_prompt=user_prompt
        )

        # Simple JSON extraction
        try:
            # Find JSON block
            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                json_str = match.group(0)
                return json.loads(json_str)
            else:
                # Try to parse entire response if no code block
                return json.loads(response)
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {response}")
            raise ValueError(f"LLM JSON parsing failed: {e}")

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
        weekly_tss: int = 0,
        yesterday_load: int = 0,
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

        assembler = WorkoutAssembler(
            tsb=tsb,
            training_goal=self.profile.training_goal,
            exclude_barcode=self.profile.exclude_barcode_workouts,
        )

        # AI-Driven Selection with Fallback
        try:
            # We treat 'intensity' as 'goal' hint if provided, otherwise use profile goal
            goal_desc = self.profile.training_goal or "General Fitness"
            if intensity and intensity != "auto":
                goal_desc += f" (Preference: {intensity})"

            # Collect athlete context for LLM (Step 3)
            weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            weekday_str = weekdays[target_date.weekday()]

            wellness_lines = []
            if wellness_metrics.hrv:
                wellness_lines.append(f"- HRV: {wellness_metrics.hrv}")
            if wellness_metrics.rhr:
                wellness_lines.append(f"- RHR: {wellness_metrics.rhr} bpm")
            if wellness_metrics.sleep_hours:
                wellness_lines.append(f"- Sleep: {wellness_metrics.sleep_hours:.1f} hours")
            if wellness_metrics.readiness:
                wellness_lines.append(f"- Readiness: {wellness_metrics.readiness}")
            wellness_text = "\n".join(wellness_lines) if wellness_lines else "No data available"

            logger.info("Requesting workout plan from AI...")
            selection = self._select_modules_with_llm(
                tsb=tsb,
                form=training_metrics.form_status,
                duration=target_duration,
                goal=goal_desc,
                weekly_tss=weekly_tss,
                yesterday_load=yesterday_load,
                exclude_barcode=self.profile.exclude_barcode_workouts,
                intensity=intensity,
                ftp=self.profile.ftp,
                weight=getattr(self.profile, "weight", 0),
                indoor=indoor,
                weekday=weekday_str,
                wellness_text=wellness_text,
            )

            logger.info(
                f"AI Selection: {selection.get('workout_name')} - {selection.get('selected_modules')}"
            )

            assembled_skeleton = assembler.assemble_from_plan(
                selection["selected_modules"]
            )

            # Override name/theme from AI
            if "workout_name" in selection:
                assembled_skeleton["workout_theme"] = selection["workout_name"]

        except Exception as e:
            logger.error(
                f"AI selection failed ({e}), falling back to algorithmic assembly"
            )
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

        # Extract design goal if available
        design_goal = None
        try:
            # If we have selection from AI
            if "selection" in locals() and isinstance(selection, dict):
                design_goal = selection.get("design_goal")
        except:
            pass

        return GeneratedWorkout(
            name=f"{WORKOUT_PREFIX} {skeleton.workout_theme}",
            description=workout_text,
            workout_text=workout_text,
            estimated_duration_minutes=duration,
            estimated_tss=skeleton.estimated_tss,
            workout_type=skeleton.workout_type,
            design_goal=design_goal,
            steps=steps,
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
