"""
Extended Workout Template Library (Pro Edition).

Inspired by modern coaching methodology (TrainerRoad, Wahoo SYSTM, Ronnestad).
Includes:
- Micro-bursts (30/15s)
- Over-Unders (Lactate Clearance)
- Hard Starts (High Torque initiation)
- Sweet Spot Bursts (Fatigue resistance)
"""

from typing import Dict, List, Any

# ==========================================
# 1. ADVANCED WARMUP BLOCKS (Activation Focus)
# ==========================================
WARMUP_BLOCKS: Dict[str, Dict[str, Any]] = {
    "ramp_standard": {
        "name": "Standard Ramp",
        "description": "Linear activation. 45% to 75%.",
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
    "ramp_staircase_activation": {
        "name": "Staircase Activation",
        "description": "Step-wise increase to prime metabolic systems.",
        "duration_minutes": 15,
        "structure": [
            {"type": "steady", "power": 50, "duration_minutes": 5},
            {"type": "steady", "power": 65, "duration_minutes": 3},
            {"type": "steady", "power": 80, "duration_minutes": 3},
            {"type": "steady", "power": 90, "duration_minutes": 2},  # Threshold touch
            {"type": "steady", "power": 55, "duration_minutes": 2},  # Recovery
        ],
    },
    "race_ready_primer": {
        "name": "Race Ready Primer",
        "description": "Includes 3 sprints to wake up neuromuscular pathways.",
        "duration_minutes": 20,
        "structure": [
            {
                "type": "warmup_ramp",
                "start_power": 50,
                "end_power": 75,
                "duration_minutes": 10,
            },
            {"type": "steady", "power": 55, "duration_minutes": 2},
            # 3x 6-second high cadence sprints (approx 150% or perceived exertion)
            {
                "type": "barcode",
                "on_power": 150,
                "off_power": 50,
                "on_duration_seconds": 10,
                "off_duration_seconds": 50,
                "repetitions": 3,
            },
            {"type": "steady", "power": 50, "duration_minutes": 5},
        ],
    },
}

# ==========================================
# 2. MAIN BLOCKS (Pro Protocols)
# ==========================================
MAIN_BLOCKS: Dict[str, Dict[str, Any]] = {
    # --- Category A: VO2 Max & Anaerobic ---
    "ronnestad_intervals_30_15": {
        "name": "Rönnestad 30/15s",
        "type": "VO2max",
        "target_type": "MicroIntervals",
        "description": "Famous short intervals. High HR maintenance with short recovery. 3 Sets.",
        "structure": [
            # Set 1: 10 mins of 30/15
            {
                "type": "barcode",
                "on_power": 120,
                "off_power": 50,
                "on_duration_seconds": 30,
                "off_duration_seconds": 15,
                "repetitions": 13,
            },
            {"type": "steady", "power": 50, "duration_minutes": 5},  # Long Rest
            # Set 2
            {
                "type": "barcode",
                "on_power": 120,
                "off_power": 50,
                "on_duration_seconds": 30,
                "off_duration_seconds": 15,
                "repetitions": 13,
            },
            {"type": "steady", "power": 50, "duration_minutes": 5},
            # Set 3
            {
                "type": "barcode",
                "on_power": 120,
                "off_power": 50,
                "on_duration_seconds": 30,
                "off_duration_seconds": 15,
                "repetitions": 13,
            },
        ],
    },
    "hard_start_vo2": {
        "name": "Hard Start VO2 Max",
        "type": "VO2max",
        "target_type": "VariableIntervals",
        "description": "Start very hard to spike HR, then settle into VO2 max intensity.",
        "structure": [
            # 4 Reps of Hard Starts
            {
                "type": "complex_repeater",  # New logical type needed for complex sub-structures
                "repetitions": 4,
                "rest_duration_seconds": 240,
                "rest_power": 50,
                "blocks": [
                    {
                        "type": "steady",
                        "power": 130,
                        "duration_seconds": 45,
                    },  # The Hard Start
                    {
                        "type": "steady",
                        "power": 110,
                        "duration_seconds": 195,
                    },  # Settle In (Total 4m work)
                ],
            }
        ],
    },
    # --- Category B: Threshold & Sweet Spot ---
    "over_unders_classic": {
        "name": "Classic Over-Unders",
        "type": "Threshold",
        "target_type": "LactateClearance",
        "description": "Alternating above/below threshold to train lactate shuttling.",
        "structure": [
            # 3 Sets of 9 minutes
            {
                "type": "complex_repeater",
                "repetitions": 3,
                "rest_duration_seconds": 300,
                "rest_power": 50,
                "blocks": [
                    # 2m Under, 1m Over x 3 = 9 mins total work per set
                    {
                        "type": "over_under",
                        "over_power": 105,
                        "under_power": 92,
                        "over_duration_seconds": 60,
                        "under_duration_seconds": 120,
                        "repetitions": 3,
                    }
                ],
            }
        ],
    },
    "sst_bursts_lumberjack": {
        "name": "SST with Bursts",
        "type": "SweetSpot",
        "target_type": "FatigueResistance",
        "description": "Long sweet spot intervals with short spikes to simulate hill attacks.",
        "structure": [
            # 20 min block with a burst every 4 mins
            {
                "type": "complex_repeater",
                "repetitions": 2,  # 2 x 20m blocks
                "rest_duration_seconds": 300,
                "rest_power": 50,
                "blocks": [
                    {"type": "steady", "power": 90, "duration_seconds": 230},
                    {"type": "steady", "power": 120, "duration_seconds": 10},  # Burst
                    {"type": "steady", "power": 90, "duration_seconds": 230},
                    {"type": "steady", "power": 120, "duration_seconds": 10},
                    {"type": "steady", "power": 90, "duration_seconds": 230},
                    {"type": "steady", "power": 120, "duration_seconds": 10},
                    {"type": "steady", "power": 90, "duration_seconds": 230},
                    {"type": "steady", "power": 120, "duration_seconds": 10},
                    {"type": "steady", "power": 90, "duration_seconds": 230},
                ],
            }
        ],
    },
    # --- Category C: Simulation / Mixed ---
    "the_breakaway": {
        "name": "The Breakaway Simulation",
        "type": "Mixed",
        "target_type": "Simulation",
        "description": "Attack hard, hold threshold, sprint finish.",
        "structure": [
            {"type": "steady", "power": 150, "duration_seconds": 30},  # Attack!
            {"type": "steady", "power": 95, "duration_minutes": 8},  # Hold the gap
            {"type": "steady", "power": 110, "duration_minutes": 2},  # Increase pace
            {"type": "steady", "power": 200, "duration_seconds": 15},  # Sprint finish
            {"type": "steady", "power": 50, "duration_minutes": 5},  # Recovery
            # Repeat sequence
            {"type": "steady", "power": 150, "duration_seconds": 30},
            {"type": "steady", "power": 95, "duration_minutes": 8},
            {"type": "steady", "power": 110, "duration_minutes": 2},
            {"type": "steady", "power": 200, "duration_seconds": 15},
            {"type": "steady", "power": 50, "duration_minutes": 5},
        ],
    },
}

# ==========================================
# 3. COOLDOWN BLOCKS (Recovery Focus)
# ==========================================
COOLDOWN_BLOCKS: Dict[str, Dict[str, Any]] = {
    "ramp_standard": {
        "name": "Standard Cooldown",
        "duration_minutes": 10,
        "structure": [
            {
                "type": "cooldown_ramp",
                "start_power": 75,
                "end_power": 45,
                "duration_minutes": 10,
            }
        ],
    },
    "flush_and_fade": {
        "name": "Flush and Fade",
        "description": "Short endurance spin to clear lactate before tapering off.",
        "duration_minutes": 15,
        "structure": [
            {"type": "steady", "power": 65, "duration_minutes": 10},  # Flush
            {
                "type": "cooldown_ramp",
                "start_power": 65,
                "end_power": 40,
                "duration_minutes": 5,
            },  # Fade
        ],
    },
}
