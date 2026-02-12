"""
Workout Assembler.

Duration-aware assembly of modular workout segments.
Composes warmup + main segments + cooldown to match target duration.
"""

import random
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class WorkoutAssembler:
    """Assembles workouts from modular segments based on target duration."""

    def __init__(self, tsb: float = 0.0, training_goal: str = "", exclude_barcode: bool = False):
        self.tsb = tsb
        self.training_goal = training_goal
        self.exclude_barcode = exclude_barcode

        # Load filtered modules
        from .workout_modules import get_filtered_modules
        self.warmup_modules, self.main_segments, self.rest_segments, self.cooldown_modules = \
            get_filtered_modules(exclude_barcode)

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
            warmup = self.warmup_modules["ramp_short"]
        elif target_duration <= 60:
            warmup = self.warmup_modules["ramp_standard"]
        else:
            warmup = self.warmup_modules["ramp_extended"]

        # 2. Select cooldown based on duration
        if target_duration <= 30:
            cooldown = self.cooldown_modules["ramp_short"]
        elif target_duration <= 60:
            cooldown = self.cooldown_modules["ramp_standard"]
        else:
            cooldown = self.cooldown_modules["flush_and_fade"]

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
                rest = self.rest_segments["rest_short"]
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

    def assemble_from_plan(self, selected_modules: List[str]) -> Dict[str, Any]:
        """Assemble workout from specific list of module keys.

        Ensures workout structure follows: warmup -> main -> cooldown
        If last module is not cooldown, automatically adds one.
        """
        logger.info(f"Assembling from plan: {selected_modules}")

        structure = []
        main_segments = []

        # Validate last module is cooldown
        last_module_key = selected_modules[-1] if selected_modules else None
        if last_module_key and last_module_key not in self.cooldown_modules:
            logger.warning(f"Last module '{last_module_key}' is not a cooldown. Adding cooldown.")
            # Add a default cooldown (flush_and_fade is a proper cooldown with downward ramp)
            selected_modules.append("flush_and_fade")

        # Track module categories for usage statistics
        module_categories = {}

        for key in selected_modules:
            module = None
            category = None

            if key in self.warmup_modules:
                module = self.warmup_modules[key]
                category = "warmup"
            elif key in self.main_segments:
                module = self.main_segments[key]
                main_segments.append(module)
                category = "main"
            elif key in self.rest_segments:
                module = self.rest_segments[key]
                category = "rest"
            elif key in self.cooldown_modules:
                module = self.cooldown_modules[key]
                category = "cooldown"

            if module:
                structure.extend(module["structure"])
                if category:
                    module_categories[key] = category
            else:
                logger.warning(f"Module key '{key}' not found in inventory")

        # Record module usage for statistics
        try:
            from .module_usage_tracker import get_tracker
            tracker = get_tracker()
            tracker.record_selection(selected_modules, module_categories)
        except Exception as e:
            logger.warning(f"Failed to record module usage: {e}")

        # Calculate stats
        actual_duration = self._calculate_duration(structure)

        if main_segments:
            workout_type = self._determine_workout_type(main_segments)
            theme = self._build_theme_name(main_segments, "custom")
        else:
            workout_type = "Mixed"
            theme = "Custom Workout"

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
        # [HOTFIX] Determine intensity based on TSB if auto
        if intensity == "auto" or not intensity:
            if self.tsb < -10:  # Fatigued state
                intensity = "easy"
                logger.debug(f"TSB {self.tsb:.1f}: Auto-selected 'easy' intensity (fatigued)")
            elif self.tsb > 10:  # Fresh state
                intensity = "hard"
                logger.debug(f"TSB {self.tsb:.1f}: Auto-selected 'hard' intensity (fresh)")
            else:  # Neutral state
                intensity = "moderate"
                logger.debug(f"TSB {self.tsb:.1f}: Auto-selected 'moderate' intensity (neutral)")

        # Filter segments by intensity preference
        if intensity == "easy":
            preferred_types = ["Endurance", "SweetSpot"]
        elif intensity == "hard":
            preferred_types = ["VO2max", "Threshold"]
        else:  # moderate
            # For moderate, mix widely
            preferred_types = ["SweetSpot", "Threshold", "Mixed"]

        # Special handling for Long Workouts (>90 min total -> available_time > ~60)
        # Prioritize Endurance/Tempo to fill volume without burnout
        if available_time > 60:
            # Add longer endurance blocks to preferred types effectively
            preferred_types.extend(["Endurance", "SweetSpot"])

        # Get segments matching preference
        matching_segments = [
            (key, seg)
            for key, seg in self.main_segments.items()
            if seg.get("type", "Mixed") in preferred_types
        ]

        # If no matches, use all segments
        if not matching_segments:
            matching_segments = list(self.main_segments.items())

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
