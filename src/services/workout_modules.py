"""
Modular Workout Segments Library (v2).

Small, composable blocks for flexible workout assembly.
Designed for duration-aware composition.
"""

from typing import Dict, List, Any

# ==========================================
# 1. WARMUP MODULES (5-15 min each)
# ==========================================
WARMUP_MODULES: Dict[str, Dict[str, Any]] = {
    "ramp_short": {
        "name": "Quick Ramp",
        "duration_minutes": 5,
        "structure": [
            {
                "type": "warmup_ramp",
                "start_power": 45,
                "end_power": 70,
                "duration_minutes": 5,
            }
        ],
    },
    "ramp_standard": {
        "name": "Standard Ramp",
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
    "ramp_extended": {
        "name": "Extended Warmup",
        "duration_minutes": 15,
        "structure": [
            {
                "type": "warmup_ramp",
                "start_power": 40,
                "end_power": 65,
                "duration_minutes": 8,
            },
            {"type": "steady", "power": 65, "duration_minutes": 4},
            {"type": "steady", "power": 75, "duration_minutes": 3},
        ],
    },
}

# ==========================================
# 2. MAIN SET SEGMENTS (5-15 min each)
# Designed to be combined for longer workouts
# ==========================================
MAIN_SEGMENTS: Dict[str, Dict[str, Any]] = {
    # --- VO2max / High Intensity ---
    "micro_30_15": {
        "name": "30/15 Micro Intervals",
        "duration_minutes": 10,
        "type": "VO2max",
        "structure": [
            {
                "type": "barcode",
                "on_power": 120,
                "off_power": 50,
                "on_duration_seconds": 30,
                "off_duration_seconds": 15,
                "repetitions": 13,
            }
        ],
    },
    "micro_40_20": {
        "name": "40/20 Micro Intervals",
        "duration_minutes": 10,
        "type": "VO2max",
        "structure": [
            {
                "type": "barcode",
                "on_power": 125,
                "off_power": 50,
                "on_duration_seconds": 40,
                "off_duration_seconds": 20,
                "repetitions": 10,
            }
        ],
    },
    "vo2_3x3": {
        "name": "3x3min VO2max",
        "duration_minutes": 15,
        "type": "VO2max",
        "structure": [
            {
                "type": "main_set_classic",
                "work_power": 115,
                "rest_power": 50,
                "work_duration_seconds": 180,
                "rest_duration_seconds": 120,
                "repetitions": 3,
            }
        ],
    },
    # --- Threshold ---
    "threshold_2x8": {
        "name": "2x8min Threshold",
        "duration_minutes": 20,
        "type": "Threshold",
        "structure": [
            {
                "type": "main_set_classic",
                "work_power": 95,
                "rest_power": 50,
                "work_duration_seconds": 480,
                "rest_duration_seconds": 120,
                "repetitions": 2,
            }
        ],
    },
    "over_under_3rep": {
        "name": "Over/Under x3",
        "duration_minutes": 12,
        "type": "Threshold",
        "structure": [
            {
                "type": "over_under",
                "over_power": 105,
                "under_power": 92,
                "over_duration_seconds": 120,
                "under_duration_seconds": 120,
                "repetitions": 3,
            }
        ],
    },
    # --- Sweet Spot ---
    "sst_10min": {
        "name": "Sweet Spot 10min",
        "duration_minutes": 10,
        "type": "SweetSpot",
        "structure": [{"type": "steady", "power": 88, "duration_minutes": 10}],
    },
    "sst_with_bumps": {
        "name": "SST with Surges",
        "duration_minutes": 12,
        "type": "SweetSpot",
        "structure": [
            {"type": "steady", "power": 88, "duration_minutes": 3},
            {"type": "steady", "power": 110, "duration_seconds": 30},
            {"type": "steady", "power": 88, "duration_minutes": 3},
            {"type": "steady", "power": 110, "duration_seconds": 30},
            {"type": "steady", "power": 88, "duration_minutes": 3},
            {"type": "steady", "power": 110, "duration_seconds": 30},
            {"type": "steady", "power": 88, "duration_minutes": 1},
        ],
    },
    # --- Endurance ---
    "tempo_15min": {
        "name": "Tempo 15min",
        "duration_minutes": 15,
        "type": "Endurance",
        "structure": [{"type": "steady", "power": 75, "duration_minutes": 15}],
    },
    "endurance_20min": {
        "name": "Endurance 20min",
        "duration_minutes": 20,
        "type": "Endurance",
        "structure": [{"type": "steady", "power": 65, "duration_minutes": 20}],
    },
    # --- Mixed / Simulation ---
    "attack_block": {
        "name": "Attack Simulation",
        "duration_minutes": 8,
        "type": "Mixed",
        "structure": [
            {"type": "steady", "power": 150, "duration_seconds": 30},
            {"type": "steady", "power": 95, "duration_minutes": 4},
            {"type": "steady", "power": 115, "duration_minutes": 2},
            {"type": "steady", "power": 50, "duration_minutes": 1},
        ],
    },
}

# ==========================================
# 3. REST SEGMENTS (between main blocks)
# ==========================================
REST_SEGMENTS: Dict[str, Dict[str, Any]] = {
    "rest_short": {
        "name": "Short Rest",
        "duration_minutes": 2,
        "structure": [{"type": "steady", "power": 50, "duration_minutes": 2}],
    },
    "rest_medium": {
        "name": "Medium Rest",
        "duration_minutes": 4,
        "structure": [{"type": "steady", "power": 50, "duration_minutes": 4}],
    },
    "rest_active": {
        "name": "Active Recovery",
        "duration_minutes": 5,
        "structure": [{"type": "steady", "power": 55, "duration_minutes": 5}],
    },
}

# ==========================================
# 4. COOLDOWN MODULES (5-15 min each)
# ==========================================
COOLDOWN_MODULES: Dict[str, Dict[str, Any]] = {
    "ramp_short": {
        "name": "Quick Cooldown",
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
    "flush_and_fade": {
        "name": "Flush and Fade",
        "duration_minutes": 15,
        "structure": [
            {"type": "steady", "power": 60, "duration_minutes": 8},
            {
                "type": "cooldown_ramp",
                "start_power": 60,
                "end_power": 40,
                "duration_minutes": 7,
            },
        ],
    },
}
