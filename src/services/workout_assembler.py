"""
Workout Assembler.

Duration-aware assembly of modular workout segments.
Composes warmup + main segments + cooldown to match target duration.
"""

import random
import logging
from typing import Dict, List, Any, Optional
from .workout_modules import (
    WARMUP_MODULES,
    MAIN_SEGMENTS,
    REST_SEGMENTS,
    COOLDOWN_MODULES,
)

logger = logging.getLogger(__name__)


class WorkoutAssembler:
    """Assembles workouts from modular segments based on target duration."""

    def __init__(self, tsb: float = 0.0, training_goal: str = ""):
        self.tsb = tsb
        self.training_goal = training_goal

    def assemble(
        self,
        target_duration: int,
        intensity: str = "moderate",
    ) -> Dict[str, Any]:
        """Assemble a complete workout skeleton from modules.

        Args:
            target_duration: Target workout duration in minutes.
            intensity: Workout intensity (easy, moderate, hard).

        Returns:
            Complete workout skeleton dict.
        """
        logger.info(f"Assembling workout: {target_duration} min, {intensity} intensity")

        # 1. Select warmup based on duration
        if target_duration <= 30:
            warmup = WARMUP_MODULES["ramp_short"]
        elif target_duration <= 60:
            warmup = WARMUP_MODULES["ramp_standard"]
        else:
            warmup = WARMUP_MODULES["ramp_extended"]

        # 2. Select cooldown based on duration
        if target_duration <= 30:
            cooldown = COOLDOWN_MODULES["ramp_short"]
        elif target_duration <= 60:
            cooldown = COOLDOWN_MODULES["ramp_standard"]
        else:
            cooldown = COOLDOWN_MODULES["flush_and_fade"]

        # 3. Calculate remaining time for main set
        warmup_time = warmup["duration_minutes"]
        cooldown_time = cooldown["duration_minutes"]
        main_time = target_duration - warmup_time - cooldown_time

        if main_time < 5:
            main_time = 5  # Minimum main set duration

        # 4. Select main segments based on intensity and fill time
        main_segments = self._select_main_segments(main_time, intensity)

        # 5. Build combined structure
        structure = []
        structure.extend(warmup["structure"])

        for i, segment in enumerate(main_segments):
            structure.extend(segment["structure"])
            # Add rest between segments (except after last one)
            if i < len(main_segments) - 1:
                rest = REST_SEGMENTS["rest_short"]
                structure.extend(rest["structure"])

        structure.extend(cooldown["structure"])

        # 6. Calculate actual total duration
        actual_duration = self._calculate_duration(structure)

        # 7. Determine workout type from main segments
        workout_type = self._determine_workout_type(main_segments)

        # 8. Build theme name from segments
        theme = self._build_theme_name(main_segments, intensity)

        logger.info(f"Assembled: {theme} ({actual_duration} min, {workout_type})")

        return {
            "workout_theme": theme,
            "workout_type": workout_type,
            "total_duration_minutes": actual_duration,
            "estimated_tss": self._estimate_tss(structure, actual_duration),
            "structure": structure,
        }

    def _select_main_segments(
        self, available_time: int, intensity: str
    ) -> List[Dict[str, Any]]:
        """Select main segments to fill available time.

        Args:
            available_time: Time available for main set in minutes.
            intensity: Workout intensity preference.

        Returns:
            List of selected segment dicts.
        """
        # Filter segments by intensity preference
        if intensity == "easy":
            preferred_types = ["Endurance", "SweetSpot"]
        elif intensity == "hard":
            preferred_types = ["VO2max", "Threshold"]
        else:
            preferred_types = ["SweetSpot", "Threshold", "Mixed"]

        # Get segments matching preference
        matching_segments = [
            (key, seg)
            for key, seg in MAIN_SEGMENTS.items()
            if seg.get("type", "Mixed") in preferred_types
        ]

        # If no matches, use all segments
        if not matching_segments:
            matching_segments = list(MAIN_SEGMENTS.items())

        # Fill time with segments
        selected = []
        remaining_time = available_time
        attempts = 0
        max_attempts = 10

        while remaining_time >= 8 and attempts < max_attempts:
            # Filter segments that fit in remaining time
            fitting = [
                (key, seg)
                for key, seg in matching_segments
                if seg["duration_minutes"] <= remaining_time
            ]

            if not fitting:
                break

            # Random selection for variety
            key, segment = random.choice(fitting)
            selected.append(segment)
            remaining_time -= segment["duration_minutes"]
            remaining_time -= 2  # Account for rest between segments
            attempts += 1

        # Ensure at least one segment
        if not selected:
            selected.append(matching_segments[0][1])

        return selected

    def _calculate_duration(self, structure: List[Dict]) -> int:
        """Calculate total duration from structure blocks."""
        total_seconds = 0

        for block in structure:
            block_type = block.get("type", "")

            if "duration_minutes" in block:
                total_seconds += block["duration_minutes"] * 60
            elif "duration_seconds" in block:
                total_seconds += block["duration_seconds"]
            elif block_type in ("warmup_ramp", "cooldown_ramp"):
                total_seconds += block.get("duration_minutes", 10) * 60
            elif block_type == "barcode":
                reps = block.get("repetitions", 10)
                on_dur = block.get("on_duration_seconds", 30)
                off_dur = block.get("off_duration_seconds", 30)
                total_seconds += reps * (on_dur + off_dur)
            elif block_type == "main_set_classic":
                reps = block.get("repetitions", 4)
                work = block.get("work_duration_seconds", 240)
                rest = block.get("rest_duration_seconds", 180)
                total_seconds += reps * (work + rest)
            elif block_type == "over_under":
                reps = block.get("repetitions", 4)
                over = block.get("over_duration_seconds", 120)
                under = block.get("under_duration_seconds", 120)
                total_seconds += reps * (over + under)

        return total_seconds // 60

    def _determine_workout_type(self, segments: List[Dict]) -> str:
        """Determine overall workout type from segments."""
        types = [seg.get("type", "Mixed") for seg in segments]

        if "VO2max" in types:
            return "VO2max"
        elif "Threshold" in types:
            return "Threshold"
        elif "SweetSpot" in types:
            return "SweetSpot"
        else:
            return "Endurance"

    def _build_theme_name(self, segments: List[Dict], intensity: str) -> str:
        """Build descriptive theme name from segments."""
        if len(segments) == 1:
            return segments[0]["name"]

        segment_names = [seg["name"].split()[0] for seg in segments[:2]]
        return f"{' + '.join(segment_names)} Combo"

    def _estimate_tss(self, structure: List[Dict], duration: int) -> int:
        """Estimate Training Stress Score."""
        # Simplified TSS estimation
        avg_intensity = 0.75  # Default assumption

        # Adjust based on structure
        high_intensity_count = sum(
            1
            for block in structure
            if block.get("power", 0) > 100 or block.get("on_power", 0) > 100
        )

        if high_intensity_count > 3:
            avg_intensity = 0.85
        elif high_intensity_count > 0:
            avg_intensity = 0.78

        return int(duration * avg_intensity)
