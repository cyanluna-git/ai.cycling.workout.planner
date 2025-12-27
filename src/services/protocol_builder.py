"""Protocol Builder.

Converts WorkoutSkeleton blocks into Intervals.icu compatible JSON steps.
"""

import logging
from typing import List, Dict, Any, Optional
from .workout_skeleton import (
    WorkoutSkeleton,
    WorkoutBlock,
    RampBlock,
    ClassicIntervalBlock,
    StepUpBlock,
    BarcodeBlock,
    OverUnderBlock,
    SteadyBlock,
    ComplexRepeaterBlock,
)

logger = logging.getLogger(__name__)


class ProtocolBuilder:
    """Converts workout skeleton blocks to Intervals.icu steps format."""

    def build_steps(self, skeleton: WorkoutSkeleton) -> List[Dict[str, Any]]:
        """Convert entire skeleton structure to Intervals.icu steps.

        Args:
            skeleton: WorkoutSkeleton with parsed blocks.

        Returns:
            List of step dicts compatible with Intervals.icu JSON format.
        """
        steps = []
        blocks = skeleton.parse_blocks()

        for block in blocks:
            block_steps = self._convert_block(block)
            steps.extend(block_steps)

        logger.info(f"Built {len(steps)} steps from {len(blocks)} blocks")
        return steps

    def _convert_block(self, block: WorkoutBlock) -> List[Dict[str, Any]]:
        """Convert a single block to Intervals.icu steps.

        Args:
            block: A typed workout block.

        Returns:
            List of step dicts for this block.
        """
        if isinstance(block, RampBlock):
            return [self._build_ramp(block)]
        elif isinstance(block, ClassicIntervalBlock):
            return self._build_classic_intervals(block)
        elif isinstance(block, StepUpBlock):
            return self._build_step_up(block)
        elif isinstance(block, BarcodeBlock):
            return self._build_barcode(block)
        elif isinstance(block, OverUnderBlock):
            return self._build_over_under(block)
        elif isinstance(block, SteadyBlock):
            return [self._build_steady(block)]
        elif isinstance(block, ComplexRepeaterBlock):
            return self._build_complex_repeater(block)
        else:
            logger.warning(f"Unknown block type: {type(block)}")
            return []

    def _build_ramp(self, block: RampBlock) -> Dict[str, Any]:
        """Build a ramp warmup or cooldown step.

        Creates a step with power start != end for gradient effect.
        Based on Intervals.icu working format from 3x9_Ciabatta.json.
        """
        # Base ramp structure
        step_data = {
            "duration": block.duration_minutes * 60,
            "ramp": True,
            "power": {
                "start": block.start_power,
                "end": block.end_power,
                "units": "%ftp",
            },
        }

        # Add warmup/cooldown flags based on block type (required by Intervals.icu)
        if block.type == "warmup_ramp":
            step_data["warmup"] = True
        elif block.type == "cooldown_ramp":
            step_data["cooldown"] = True
        # For generic "ramp" type, no additional flags needed

        return step_data

    def _build_classic_intervals(
        self, block: ClassicIntervalBlock
    ) -> List[Dict[str, Any]]:
        """Build classic interval steps (4x4, 8x8, etc.).

        Returns a nested repetitions block if count > 1.
        """
        # Define the base unit (work + rest)
        unit_steps = [
            {
                "type": "Interval",
                "duration": block.work_duration_seconds,
                "power": {"value": block.work_power, "units": "%ftp"},
            },
            {
                "type": "Recovery",
                "duration": block.rest_duration_seconds,
                "power": {"value": block.rest_power, "units": "%ftp"},
            },
        ]

        # Use nested format for cleaner Intervals.icu representation
        if block.repetitions > 1:
            return [{"reps": block.repetitions, "steps": unit_steps}]

        # If just 1 rep, flatten it (rare for "classic intervals" but possible)
        return unit_steps

    def _build_step_up(self, block: StepUpBlock) -> List[Dict[str, Any]]:
        """Build step-up (staircase) progressive loading.

        Creates multiple steady intervals with increasing power.
        """
        steps = []

        for i, power in enumerate(block.power_steps):
            steps.append(
                {
                    "type": "Interval",
                    "duration": block.step_duration_seconds,
                    "power": {"value": power, "units": "%ftp"},
                    "name": f"Step {i + 1}",
                }
            )

        return steps

    def _build_barcode(self, block: BarcodeBlock) -> List[Dict[str, Any]]:
        """Build barcode/micro-burst intervals.

        Returns a nested repetitions block.
        """
        # Define the base unit (on + off)
        unit_steps = [
            {
                "type": "Interval",
                "duration": block.on_duration_seconds,
                "power": {"value": block.on_power, "units": "%ftp"},
            },
            {
                "type": "Recovery",
                "duration": block.off_duration_seconds,
                "power": {"value": block.off_power, "units": "%ftp"},
            },
        ]

        if block.repetitions > 1:
            return [{"reps": block.repetitions, "steps": unit_steps}]

        return unit_steps

    def _build_over_under(self, block: OverUnderBlock) -> List[Dict[str, Any]]:
        """Build over/under intervals (alternating above/below FTP).

        Returns a nested repetitions block.
        """
        # Define the base unit (over + under)
        unit_steps = [
            {
                "type": "Interval",
                "duration": block.over_duration_seconds,
                "power": {"value": block.over_power, "units": "%ftp"},
                "name": "Over",
            },
            {
                "type": "Interval",
                "duration": block.under_duration_seconds,
                "power": {"value": block.under_power, "units": "%ftp"},
                "name": "Under",
            },
        ]

        if block.repetitions > 1:
            return [{"reps": block.repetitions, "steps": unit_steps}]

        return unit_steps

    def _build_steady(self, block: SteadyBlock) -> Dict[str, Any]:
        """Build a steady-state interval at fixed power."""
        # Handle both duration_minutes and duration_seconds
        if block.duration_seconds:
            duration = block.duration_seconds
        elif block.duration_minutes:
            duration = block.duration_minutes * 60
        else:
            duration = 60  # Default 1 minute

        return {
            "type": "Interval",
            "duration": duration,
            "power": {"value": block.power, "units": "%ftp"},
        }

    def _build_complex_repeater(
        self, block: ComplexRepeaterBlock
    ) -> List[Dict[str, Any]]:
        """Build complex repeater with nested blocks and rest intervals.

        Flattens the nested structure by repeating the inner blocks
        and adding rest intervals between sets.
        """
        steps = []

        for rep in range(block.repetitions):
            # Build each nested block
            for nested_block_data in block.blocks:
                nested_type = nested_block_data.get("type", "steady")

                if nested_type == "steady":
                    # Handle both duration_minutes and duration_seconds
                    duration = nested_block_data.get("duration_seconds") or (
                        nested_block_data.get("duration_minutes", 1) * 60
                    )
                    steps.append(
                        {
                            "type": "Interval",
                            "duration": duration,
                            "power": {
                                "value": nested_block_data.get("power", 90),
                                "units": "%ftp",
                            },
                        }
                    )
                elif nested_type == "over_under":
                    # Handle nested over_under
                    for _ in range(nested_block_data.get("repetitions", 1)):
                        steps.append(
                            {
                                "type": "Interval",
                                "duration": nested_block_data.get(
                                    "over_duration_seconds", 60
                                ),
                                "power": {
                                    "value": nested_block_data.get("over_power", 105),
                                    "units": "%ftp",
                                },
                                "name": "Over",
                            }
                        )
                        steps.append(
                            {
                                "type": "Interval",
                                "duration": nested_block_data.get(
                                    "under_duration_seconds", 120
                                ),
                                "power": {
                                    "value": nested_block_data.get("under_power", 92),
                                    "units": "%ftp",
                                },
                                "name": "Under",
                            }
                        )
                # Add more nested types as needed

            # Add rest between sets (except after last rep)
            if rep < block.repetitions - 1:
                steps.append(
                    {
                        "type": "Recovery",
                        "duration": block.rest_duration_seconds,
                        "power": {"value": block.rest_power, "units": "%ftp"},
                    }
                )

        return steps

    def build_workout_text(self, skeleton: WorkoutSkeleton) -> str:
        """Build human-readable workout text for Intervals.icu.

        This is the legacy format that can be pasted into Intervals.icu
        workout description field.

        Args:
            skeleton: WorkoutSkeleton with parsed blocks.

        Returns:
            Formatted workout text string.
        """
        lines = []
        blocks = skeleton.parse_blocks()

        current_section = None

        for block in blocks:
            # Determine section
            if isinstance(block, RampBlock) and block.type == "warmup_ramp":
                if current_section != "warmup":
                    lines.append("Warmup")
                    current_section = "warmup"
                lines.append(
                    f"- {block.duration_minutes}m {block.start_power}% -> {block.end_power}%"
                )

            elif isinstance(block, RampBlock) and block.type == "cooldown_ramp":
                if current_section != "cooldown":
                    lines.append("")
                    lines.append("Cooldown")
                    current_section = "cooldown"

                if block.start_power != block.end_power:
                    lines.append(
                        f"- {block.duration_minutes}m {block.start_power}% -> {block.end_power}%"
                    )
                else:
                    lines.append(f"- {block.duration_minutes}m {block.start_power}%")

            else:
                # Main set
                if current_section != "main":
                    lines.append("")
                    lines.append("Main Set")
                    current_section = "main"

                if isinstance(block, ClassicIntervalBlock):
                    work_min = block.work_duration_seconds // 60
                    rest_min = block.rest_duration_seconds // 60
                    lines.append(
                        f"- {block.repetitions}x ({work_min}m {block.work_power}% / {rest_min}m {block.rest_power}%)"
                    )

                elif isinstance(block, StepUpBlock):
                    step_min = block.step_duration_seconds // 60
                    powers = " -> ".join([f"{p}%" for p in block.power_steps])
                    lines.append(f"- Step-up: {step_min}m each @ {powers}")

                elif isinstance(block, BarcodeBlock):
                    lines.append(
                        f"- {block.repetitions}x ({block.on_duration_seconds}s {block.on_power}% / {block.off_duration_seconds}s {block.off_power}%)"
                    )

                elif isinstance(block, OverUnderBlock):
                    over_min = block.over_duration_seconds // 60
                    under_min = block.under_duration_seconds // 60
                    lines.append(
                        f"- {block.repetitions}x Over/Under ({over_min}m {block.over_power}% / {under_min}m {block.under_power}%)"
                    )

                elif isinstance(block, SteadyBlock):
                    if block.duration_minutes:
                        lines.append(f"- {block.duration_minutes}m {block.power}%")
                    elif block.duration_seconds:
                        lines.append(f"- {block.duration_seconds}s {block.power}%")

        return "\n".join(lines)


def build_intervals_icu_json(skeleton: WorkoutSkeleton) -> Dict[str, Any]:
    """Build complete Intervals.icu workout JSON.

    Args:
        skeleton: WorkoutSkeleton with workout structure.

    Returns:
        Complete JSON dict for Intervals.icu API.
    """
    builder = ProtocolBuilder()
    steps = builder.build_steps(skeleton)
    workout_text = builder.build_workout_text(skeleton)

    return {
        "name": f"[AICoach] {skeleton.workout_theme}",
        "type": skeleton.workout_type,
        "description": workout_text,
        "estimatedTss": skeleton.estimated_tss,
        "steps": steps,
    }
