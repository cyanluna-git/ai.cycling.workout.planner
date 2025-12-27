"""Workout Template Library.

This module contains modular blocks for assembling diverse workouts.
Each block category (Warmup, Main, Cooldown) contains varied protocols.
"""

from typing import Dict, List, Any

# Warmup Blocks
WARMUP_BLOCKS: Dict[str, Dict[str, Any]] = {
    "ramp_standard": {
        "name": "Standard Ramp",
        "description": "Progressive warm-up to prepare cycling muscles.",
        "duration_minutes": 10,
        "structure": [
            {
                "type": "warmup_ramp",
                "start_power": 45,
                "end_power": 75,
                "duration_minutes": 10,
            }
        ],
    },
    "ramp_gentle": {
        "name": "Gentle Ramp",
        "description": "Slow, easy start for recovery days.",
        "duration_minutes": 15,
        "structure": [
            {"type": "steady", "power": 40, "duration_minutes": 5},
            {
                "type": "warmup_ramp",
                "start_power": 40,
                "end_power": 65,
                "duration_minutes": 10,
            },
        ],
    },
    "active_opener": {
        "name": "Active Opener",
        "description": "Warm-up with 3 short bursts to prime VO2max.",
        "duration_minutes": 12,
        "structure": [
            {
                "type": "warmup_ramp",
                "start_power": 40,
                "end_power": 70,
                "duration_minutes": 6,
            },
            {"type": "steady", "power": 55, "duration_minutes": 2},
            {
                "type": "barcode",
                "on_power": 110,
                "off_power": 50,
                "on_duration_seconds": 30,
                "off_duration_seconds": 30,
                "repetitions": 3,
            },
            {"type": "steady", "power": 50, "duration_minutes": 1},
        ],
    },
}

# Main Sets (Complex & Varied)
MAIN_BLOCKS: Dict[str, Dict[str, Any]] = {
    # 1. Ciabatta Style (Varied Intervals)
    "ciabatta_light": {
        "name": "Ciabatta Light",
        "type": "Mixed",
        "target_type": "Varied",
        "description": "Mix of ramp intervals and steady state work.",
        "structure": [
            # Set 1: Ramp + Steady
            {
                "type": "warmup_ramp",
                "start_power": 80,
                "end_power": 95,
                "duration_minutes": 5,
            },
            {"type": "steady", "power": 88, "duration_minutes": 5},
            {"type": "steady", "power": 50, "duration_minutes": 3},
            # Set 2: Inverse layout
            {"type": "steady", "power": 90, "duration_minutes": 4},
            {
                "type": "step_up",
                "power_steps": [90, 95, 100],
                "step_duration_seconds": 120,
            },
            {"type": "steady", "power": 50, "duration_minutes": 3},
        ],
    },
    "ciabatta_classic": {
        "name": "Ciabatta Classic",
        "type": "VO2max",
        "target_type": "Varied",
        "description": "Intense mix of ramps, bursts, and threshold work.",
        "structure": [
            # Set 1: Ramp into Bursts
            {
                "type": "warmup_ramp",
                "start_power": 85,
                "end_power": 105,
                "duration_minutes": 4,
            },
            {
                "type": "barcode",
                "on_power": 120,
                "off_power": 50,
                "on_duration_seconds": 30,
                "off_duration_seconds": 30,
                "repetitions": 6,
            },
            {"type": "steady", "power": 50, "duration_minutes": 4},
            # Set 2: Threshold block
            {
                "type": "step_up",
                "power_steps": [90, 95, 100, 95, 90],
                "step_duration_seconds": 120,
            },
            {"type": "steady", "power": 50, "duration_minutes": 4},
            # Set 3: Finale Ramp
            {
                "type": "warmup_ramp",
                "start_power": 90,
                "end_power": 110,
                "duration_minutes": 3,
            },
        ],
    },
    # 2. Classic Intervals
    "norwegian_4x4": {
        "name": "Norwegian 4x4",
        "type": "VO2max",
        "target_type": "Intervals",
        "description": "Long intervals at high aerobic intensity.",
        "structure": [
            {
                "type": "main_set_classic",
                "work_power": 108,
                "rest_power": 50,
                "work_duration_seconds": 240,
                "rest_duration_seconds": 180,
                "repetitions": 4,
            }
        ],
    },
    "threshold_8x8": {
        "name": "Threshold 8 mins",
        "type": "Threshold",
        "target_type": "Intervals",
        "structure": [
            {
                "type": "main_set_classic",
                "work_power": 92,
                "rest_power": 50,
                "work_duration_seconds": 480,
                "rest_duration_seconds": 120,
                "repetitions": 4,
            }
        ],
    },
    # 3. Specific Protocols
    "over_under_crisscross": {
        "name": "Over/Under Crisscross",
        "type": "Threshold",
        "target_type": "OverUnder",
        "description": "Alternating above and below threshold to clear lactate.",
        "structure": [
            {
                "type": "over_under",
                "over_power": 105,
                "under_power": 92,
                "over_duration_seconds": 120,
                "under_duration_seconds": 120,
                "repetitions": 3,
            },
            {"type": "steady", "power": 50, "duration_minutes": 5},
            {
                "type": "over_under",
                "over_power": 105,
                "under_power": 92,
                "over_duration_seconds": 120,
                "under_duration_seconds": 120,
                "repetitions": 3,
            },
        ],
    },
    "pyramid_intervals": {
        "name": "Pyramid Intervals",
        "type": "VO2max",
        "target_type": "Intervals",
        "description": "Increasing difficulty then decreasing.",
        "structure": [
            {"type": "steady", "power": 95, "duration_minutes": 3},
            {"type": "steady", "power": 50, "duration_minutes": 2},
            {"type": "steady", "power": 105, "duration_minutes": 2},
            {"type": "steady", "power": 50, "duration_minutes": 2},
            {"type": "steady", "power": 115, "duration_minutes": 1},
            {"type": "steady", "power": 50, "duration_minutes": 2},
            {"type": "steady", "power": 105, "duration_minutes": 2},
            {"type": "steady", "power": 50, "duration_minutes": 2},
            {"type": "steady", "power": 95, "duration_minutes": 3},
        ],
    },
    "steady_endurance": {
        "name": "Steady Endurance",
        "type": "Endurance",
        "target_type": "Steady",
        "structure": [
            {"type": "steady", "power": 70, "duration_minutes": 20},
            {"type": "steady", "power": 75, "duration_minutes": 10},
            {"type": "steady", "power": 70, "duration_minutes": 20},
        ],
    },
}

# Cooldown Blocks
COOLDOWN_BLOCKS: Dict[str, Dict[str, Any]] = {
    "ramp_standard": {
        "name": "Standard Cooldown",
        "duration_minutes": 10,
        "structure": [
            {
                "type": "cooldown_ramp",
                "start_power": 70,
                "end_power": 40,
                "duration_minutes": 10,
            }
        ],
    },
    "ramp_fast": {
        "name": "Fast Cooldown",
        "duration_minutes": 5,
        "structure": [
            {
                "type": "cooldown_ramp",
                "start_power": 65,
                "end_power": 40,
                "duration_minutes": 5,
            }
        ],
    },
    "active_flush": {
        "name": "Active Flush",
        "duration_minutes": 15,
        "structure": [
            {"type": "steady", "power": 60, "duration_minutes": 5},
            {
                "type": "cooldown_ramp",
                "start_power": 60,
                "end_power": 40,
                "duration_minutes": 10,
            },
        ],
    },
}
