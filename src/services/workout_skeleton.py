"""Workout Skeleton Schema and Validation.

This module defines the intermediate JSON structure that LLM generates
before conversion to Intervals.icu format.
"""

from dataclasses import dataclass, field
from typing import List, Literal, Optional, Union
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ProtocolType(str, Enum):
    """Supported workout protocol types."""

    WARMUP_RAMP = "warmup_ramp"
    COOLDOWN_RAMP = "cooldown_ramp"
    RAMP = "ramp"
    MAIN_SET_CLASSIC = "main_set_classic"
    STEP_UP = "step_up"
    BARCODE = "barcode"
    OVER_UNDER = "over_under"
    STEADY = "steady"


@dataclass
class RampBlock:
    """Ramp warmup or cooldown block."""

    type: Literal["warmup_ramp", "cooldown_ramp", "ramp"]
    start_power: int  # % of FTP
    end_power: int  # % of FTP
    duration_minutes: int

    def validate(self) -> List[str]:
        errors = []
        if self.type == "warmup_ramp" and self.start_power >= self.end_power:
            errors.append("Warmup ramp should have start_power < end_power")
        if self.type == "cooldown_ramp" and self.start_power <= self.end_power:
            errors.append("Cooldown ramp should have start_power > end_power")
        if not 20 <= self.start_power <= 150:
            errors.append(
                f"start_power {self.start_power}% out of valid range (20-150)"
            )
        if not 20 <= self.end_power <= 150:
            errors.append(f"end_power {self.end_power}% out of valid range (20-150)")
        if not 3 <= self.duration_minutes <= 30:
            errors.append(
                f"duration_minutes {self.duration_minutes} out of valid range (3-30)"
            )
        return errors


@dataclass
class ClassicIntervalBlock:
    """Classic interval block (4x4, 8x8, etc.)."""

    type: Literal["main_set_classic"]
    work_power: int  # % of FTP during work
    rest_power: int  # % of FTP during rest
    work_duration_seconds: int
    rest_duration_seconds: int
    repetitions: int
    name: Optional[str] = None

    def validate(self) -> List[str]:
        errors = []
        if not 50 <= self.work_power <= 200:
            errors.append(f"work_power {self.work_power}% out of valid range")
        if not 20 <= self.rest_power <= 80:
            errors.append(f"rest_power {self.rest_power}% out of valid range")
        if not 30 <= self.work_duration_seconds <= 1800:
            errors.append(f"work_duration_seconds out of valid range")
        if not 1 <= self.repetitions <= 20:
            errors.append(f"repetitions {self.repetitions} out of valid range")
        return errors


@dataclass
class StepUpBlock:
    """Step-up (staircase) progressive loading block."""

    type: Literal["step_up"]
    power_steps: List[int]  # e.g., [75, 85, 95]
    step_duration_seconds: int

    def validate(self) -> List[str]:
        errors = []
        if len(self.power_steps) < 2:
            errors.append("step_up requires at least 2 power steps")
        for i, power in enumerate(self.power_steps):
            if not 40 <= power <= 150:
                errors.append(f"power_steps[{i}] = {power}% out of valid range")
        return errors


@dataclass
class BarcodeBlock:
    """Barcode/micro-burst interval block (30/30, 40/20, etc.)."""

    type: Literal["barcode"]
    on_power: int  # % of FTP during burst
    off_power: int  # % of FTP during recovery
    on_duration_seconds: int  # Typically 15-60 seconds
    off_duration_seconds: int
    repetitions: int

    def validate(self) -> List[str]:
        errors = []
        if not 100 <= self.on_power <= 200:
            errors.append(f"Barcode on_power should be high intensity (100-200%)")
        if not 5 <= self.on_duration_seconds <= 120:
            errors.append(f"Barcode on_duration should be short (5-120s)")
        if not 5 <= self.repetitions <= 30:
            errors.append(f"repetitions {self.repetitions} out of valid range")
        return errors


@dataclass
class OverUnderBlock:
    """Over/Under interval block (alternating above/below FTP)."""

    type: Literal["over_under"]
    over_power: int  # % of FTP (above threshold, e.g., 105%)
    under_power: int  # % of FTP (below threshold, e.g., 95%)
    over_duration_seconds: int
    under_duration_seconds: int
    repetitions: int

    def validate(self) -> List[str]:
        errors = []
        if self.over_power <= 100:
            errors.append(f"over_power should be > 100% FTP")
        if self.under_power >= 100:
            errors.append(f"under_power should be < 100% FTP")
        return errors


@dataclass
class SteadyBlock:
    """Simple steady-state block at fixed power."""

    type: Literal["steady"]
    power: int
    duration_minutes: Optional[int] = None
    duration_seconds: Optional[int] = None  # Some templates use seconds

    def validate(self) -> List[str]:
        errors = []
        if not 30 <= self.power <= 250:
            errors.append(f"power {self.power}% out of valid range")
        return errors


@dataclass
class ComplexRepeaterBlock:
    """Complex repeater block with nested sub-blocks and rest intervals."""

    type: Literal["complex_repeater"]
    repetitions: int
    rest_duration_seconds: int
    rest_power: int
    blocks: List[dict]  # Nested blocks (will be flattened during build)

    def validate(self) -> List[str]:
        errors = []
        if not 1 <= self.repetitions <= 10:
            errors.append(f"repetitions {self.repetitions} out of valid range")
        if not self.blocks:
            errors.append("complex_repeater must have at least one block")
        return errors


# Union type for all block types
WorkoutBlock = Union[
    RampBlock,
    ClassicIntervalBlock,
    StepUpBlock,
    BarcodeBlock,
    OverUnderBlock,
    SteadyBlock,
    ComplexRepeaterBlock,
]


@dataclass
class WorkoutSkeleton:
    """Complete workout skeleton structure."""

    workout_theme: str
    total_duration_minutes: int
    structure: List[dict]  # Raw dicts from LLM, will be parsed to blocks
    workout_type: str = "Endurance"  # Endurance, Threshold, VO2max, Recovery
    estimated_tss: Optional[int] = None

    def parse_blocks(self) -> List[WorkoutBlock]:
        """Parse raw structure dicts into typed blocks."""
        blocks = []
        for item in self.structure:
            block = self._parse_block(item)
            if block:
                blocks.append(block)
        return blocks

    def _parse_block(self, data: dict) -> Optional[WorkoutBlock]:
        """Parse a single block dict into a typed block."""
        block_type = data.get("type", "")

        try:
            if block_type in ("warmup_ramp", "cooldown_ramp", "ramp"):
                return RampBlock(
                    type=block_type,
                    start_power=data.get("start_power", 40),
                    end_power=data.get("end_power", 75),
                    duration_minutes=data.get("duration_minutes", 10),
                )

            elif block_type == "main_set_classic":
                return ClassicIntervalBlock(
                    type=block_type,
                    work_power=data.get("work_power", 100),
                    rest_power=data.get("rest_power", 50),
                    work_duration_seconds=data.get("work_duration_seconds", 240),
                    rest_duration_seconds=data.get("rest_duration_seconds", 180),
                    repetitions=data.get("repetitions", 4),
                    name=data.get("name"),
                )

            elif block_type == "step_up":
                return StepUpBlock(
                    type=block_type,
                    power_steps=data.get("power_steps", [75, 85, 95]),
                    step_duration_seconds=data.get("step_duration_seconds", 300),
                )

            elif block_type == "barcode":
                return BarcodeBlock(
                    type=block_type,
                    on_power=data.get("on_power", 120),
                    off_power=data.get("off_power", 50),
                    on_duration_seconds=data.get("on_duration_seconds", 30),
                    off_duration_seconds=data.get("off_duration_seconds", 30),
                    repetitions=data.get("repetitions", 10),
                )

            elif block_type == "over_under":
                return OverUnderBlock(
                    type=block_type,
                    over_power=data.get("over_power", 105),
                    under_power=data.get("under_power", 95),
                    over_duration_seconds=data.get("over_duration_seconds", 120),
                    under_duration_seconds=data.get("under_duration_seconds", 120),
                    repetitions=data.get("repetitions", 4),
                )

            elif block_type == "steady":
                return SteadyBlock(
                    type=block_type,
                    power=data.get("power", 65),
                    duration_minutes=data.get("duration_minutes"),
                    duration_seconds=data.get("duration_seconds"),
                )

            elif block_type == "complex_repeater":
                return ComplexRepeaterBlock(
                    type=block_type,
                    repetitions=data.get("repetitions", 1),
                    rest_duration_seconds=data.get("rest_duration_seconds", 240),
                    rest_power=data.get("rest_power", 50),
                    blocks=data.get("blocks", []),
                )

            else:
                logger.warning(f"Unknown block type: {block_type}")
                return None

        except Exception as e:
            logger.error(f"Error parsing block {data}: {e}")
            return None

    def validate(self) -> List[str]:
        """Validate the entire skeleton structure."""
        errors = []

        if not self.workout_theme:
            errors.append("workout_theme is required")

        if not 15 <= self.total_duration_minutes <= 300:
            errors.append(
                f"total_duration_minutes {self.total_duration_minutes} out of range (15-300)"
            )

        if not self.structure:
            errors.append("structure cannot be empty")

        # Validate each block
        blocks = self.parse_blocks()
        for i, block in enumerate(blocks):
            block_errors = block.validate()
            for err in block_errors:
                errors.append(f"Block {i} ({block.type}): {err}")

        return errors


def parse_skeleton_from_dict(data: dict) -> WorkoutSkeleton:
    """Parse a raw dict (from LLM JSON) into a WorkoutSkeleton."""
    return WorkoutSkeleton(
        workout_theme=data.get("workout_theme", "AI Workout"),
        total_duration_minutes=data.get("total_duration_minutes", 60),
        structure=data.get("structure", []),
        workout_type=data.get("workout_type", "Endurance"),
        estimated_tss=data.get("estimated_tss"),
    )
