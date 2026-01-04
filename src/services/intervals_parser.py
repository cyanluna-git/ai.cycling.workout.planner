"""
Intervals.icu workout_doc parser.

This module parses workout_doc structures returned from Intervals.icu API
into our internal format for rendering.
"""

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


def parse_workout_doc_steps(workout_doc: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Parse Intervals.icu workout_doc into our internal steps format.

    Args:
        workout_doc: The workout_doc object from Intervals.icu Event API
            Expected structure (varies by workout type):
            {
                "steps": [
                    {
                        "duration": 600,           # seconds
                        "power": 50,              # %FTP (0-100 scale)
                        "text": "Warmup"
                    },
                    {
                        "duration": 300,
                        "power_low": 50,          # For ramps
                        "power_high": 75,
                        "ramp": true,
                        "text": "Ramp up"
                    },
                    {
                        "repeat": 3,
                        "steps": [...]            # Nested steps for intervals
                    }
                ]
            }

    Returns:
        List of steps in our internal format compatible with protocol_builder
        [
            {
                "duration": 600,
                "power": {"value": 50, "units": "%ftp"},
                "text": "Warmup"
            },
            {
                "duration": 300,
                "ramp": True,
                "power": {"start": 50, "end": 75, "units": "%ftp"},
                "warmup": True,
                "text": "Ramp up"
            }
        ]
    """
    if not workout_doc:
        logger.warning("Empty workout_doc provided")
        return []

    intervals_steps = workout_doc.get("steps", [])
    if not intervals_steps:
        logger.warning("No steps found in workout_doc")
        return []

    converted_steps = []

    for step in intervals_steps:
        parsed_step = _parse_single_step(step)
        if parsed_step:
            converted_steps.append(parsed_step)

    logger.info(f"Parsed {len(converted_steps)} steps from workout_doc")
    return converted_steps


def _parse_single_step(step: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse a single step from Intervals.icu format.

    Args:
        step: Single step dict from workout_doc

    Returns:
        Parsed step in internal format, or None if invalid
    """
    duration = step.get("duration", 0)

    # Handle repeat blocks (intervals) - Intervals.icu uses "reps"
    if "reps" in step or "repeat" in step:
        return _parse_repeat_block(step)

    # Handle ramp steps (warmup/cooldown)
    if step.get("ramp") or ("power_low" in step and "power_high" in step):
        return _parse_ramp_step(step, duration)

    # Handle steady state (constant power)
    if "power" in step:
        return _parse_steady_state_step(step, duration)

    # Handle other step types (cadence, HR, etc.)
    logger.debug(f"Unknown step type, using as-is: {step}")
    return step


def _parse_ramp_step(step: Dict[str, Any], duration: int) -> Dict[str, Any]:
    """Parse a ramp step (warmup or cooldown)."""

    # Intervals.icu already uses proper structure: power.start/end
    power_obj = step.get("power", {})
    power_start = power_obj.get("start", 50)
    power_end = power_obj.get("end", 75)

    # Determine if warmup or cooldown based on direction
    is_warmup = power_start < power_end

    parsed = {
        "duration": duration,
        "ramp": True,
        "power": {
            "start": power_start,  # Already in 0-100 scale
            "end": power_end,
            "units": "%ftp"
        },
    }

    # Preserve existing warmup/cooldown flags or infer
    if step.get("warmup"):
        parsed["warmup"] = True
    elif step.get("cooldown"):
        parsed["cooldown"] = True
    elif is_warmup:
        parsed["warmup"] = True
    else:
        parsed["cooldown"] = True

    # Preserve text if present
    if "text" in step:
        parsed["text"] = step["text"]

    return parsed


def _parse_steady_state_step(step: Dict[str, Any], duration: int) -> Dict[str, Any]:
    """Parse a steady state step (constant power)."""

    # Intervals.icu already uses proper structure: power.value
    power_obj = step.get("power", {})

    # Handle both formats: power.value (number) or power object with value
    if isinstance(power_obj, dict):
        power_value = power_obj.get("value", 75)
    else:
        # Fallback if power is a direct number
        power_value = power_obj

    parsed = {
        "duration": duration,
        "power": {
            "value": power_value,  # Just the number, already in 0-100 scale
            "units": "%ftp"
        }
    }

    # Preserve warmup/cooldown flags if present
    if step.get("warmup"):
        parsed["warmup"] = True
    if step.get("cooldown"):
        parsed["cooldown"] = True

    # Preserve text if present
    if "text" in step:
        parsed["text"] = step["text"]

    return parsed


def _parse_repeat_block(step: Dict[str, Any]) -> Dict[str, Any]:
    """Parse a repeat/interval block."""

    # Intervals.icu uses "reps", we use "repeat"
    repeat_count = step.get("reps") or step.get("repeat", 1)
    nested_steps = step.get("steps", [])

    # Parse nested steps
    parsed_nested = []
    for nested_step in nested_steps:
        parsed = _parse_single_step(nested_step)
        if parsed:
            parsed_nested.append(parsed)

    result = {
        "repeat": repeat_count,
        "steps": parsed_nested,
    }

    # Preserve text if present
    if "text" in step:
        result["text"] = step["text"]

    return result


def extract_workout_sections(
    steps: List[Dict[str, Any]]
) -> tuple[List[str], List[str], List[str]]:
    """
    Extract warmup, main, and cooldown sections from steps.

    This is a helper to organize steps into logical sections for display.

    Args:
        steps: List of parsed steps

    Returns:
        Tuple of (warmup_lines, main_lines, cooldown_lines)
    """
    warmup = []
    main = []
    cooldown = []

    in_cooldown = False

    for step in steps:
        # Format step as human-readable text
        text = _format_step_text(step)

        # Detect section
        if step.get("warmup"):
            warmup.append(text)
        elif step.get("cooldown"):
            cooldown.append(text)
            in_cooldown = True
        else:
            # If we haven't hit cooldown yet, it's main set
            if in_cooldown:
                cooldown.append(text)
            else:
                main.append(text)

    return warmup, main, cooldown


def _format_step_text(step: Dict[str, Any]) -> str:
    """Format a step as human-readable text."""

    duration_min = step.get("duration", 0) // 60
    text = step.get("text", "")

    # Ramp
    if step.get("ramp"):
        power_start = step["power"]["start"]
        power_end = step["power"]["end"]
        return f"{duration_min}m {power_start}% -> {power_end}%{' - ' + text if text else ''}"

    # Steady state
    elif "power" in step and "value" in step["power"]:
        power = step["power"]["value"]
        return f"{duration_min}m @ {power}%{' - ' + text if text else ''}"

    # Repeat
    elif "repeat" in step:
        repeat_count = step["repeat"]
        nested_texts = [_format_step_text(s) for s in step.get("steps", [])]
        nested_str = ", ".join(nested_texts)
        return f"{repeat_count}x ({nested_str})"

    # Fallback
    else:
        return f"{duration_min}m{' - ' + text if text else ''}"
