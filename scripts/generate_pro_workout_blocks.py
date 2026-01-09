#!/usr/bin/env python3
"""Generate professional-grade workout blocks based on famous cycling training programs.

This script creates workout modules inspired by TrainerRoad, Zwift, Sufferfest,
and other professional cycling training platforms.

Usage:
    python scripts/generate_pro_workout_blocks.py --all
    python scripts/generate_pro_workout_blocks.py --vo2max
    python scripts/generate_pro_workout_blocks.py --threshold
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Base directory
BASE_DIR = Path(__file__).parent.parent / "src" / "data" / "workout_modules" / "main"


def generate_vo2max_blocks() -> List[Dict[str, Any]]:
    """Generate VO2max interval blocks.

    VO2max workouts focus on maximum aerobic capacity.
    Typical: 3-8min @ 105-120% FTP, with equal or longer rest.
    """
    modules = []

    # Classic VO2max intervals (inspired by TrainerRoad)
    vo2_variations = [
        # Short hard intervals
        {"name": "VO2 Blast 8x2min", "reps": 8, "work_min": 2, "rest_min": 2, "power": 120},
        {"name": "VO2 Short 10x1min", "reps": 10, "work_min": 1, "rest_min": 1, "power": 125},
        {"name": "VO2 Power 12x30s", "reps": 12, "work_sec": 30, "rest_sec": 30, "power": 130},

        # Classic 3-minute intervals
        {"name": "VO2 Classic 5x3min", "reps": 5, "work_min": 3, "rest_min": 3, "power": 115},
        {"name": "VO2 Hard 6x3min", "reps": 6, "work_min": 3, "rest_min": 3, "power": 118},
        {"name": "VO2 Max 4x3min", "reps": 4, "work_min": 3, "rest_min": 4, "power": 120},

        # 4-minute intervals (inspired by Zwift)
        {"name": "VO2 Build 5x4min", "reps": 5, "work_min": 4, "rest_min": 4, "power": 115},
        {"name": "VO2 Strong 4x4min", "reps": 4, "work_min": 4, "rest_min": 4, "power": 118},

        # 5-minute intervals (Norwegian method inspired)
        {"name": "VO2 Long 4x5min", "reps": 4, "work_min": 5, "rest_min": 5, "power": 110},
        {"name": "VO2 Extended 5x5min", "reps": 5, "work_min": 5, "rest_min": 3, "power": 108},

        # 6-8 minute intervals (longer aerobic capacity work)
        {"name": "VO2 Aerobic 3x6min", "reps": 3, "work_min": 6, "rest_min": 6, "power": 108},
        {"name": "VO2 Endurance 3x8min", "reps": 3, "work_min": 8, "rest_min": 8, "power": 105},
    ]

    for spec in vo2_variations:
        structure = []
        reps = spec["reps"]
        power = spec["power"]

        # Work intervals
        if "work_sec" in spec:
            work_dur_sec = spec["work_sec"]
            rest_dur_sec = spec["rest_sec"]
        else:
            work_dur_sec = spec["work_min"] * 60
            rest_dur_sec = spec["rest_min"] * 60

        # Build structure
        for i in range(reps):
            # Work
            if work_dur_sec >= 60:
                structure.append({
                    "type": "steady",
                    "power": power,
                    "duration_minutes": work_dur_sec // 60
                })
            else:
                structure.append({
                    "type": "steady",
                    "power": power,
                    "duration_seconds": work_dur_sec
                })

            # Rest (except after last rep)
            if i < reps - 1:
                if rest_dur_sec >= 60:
                    structure.append({
                        "type": "steady",
                        "power": 50,
                        "duration_minutes": rest_dur_sec // 60
                    })
                else:
                    structure.append({
                        "type": "steady",
                        "power": 50,
                        "duration_seconds": rest_dur_sec
                    })

        total_duration = (work_dur_sec + rest_dur_sec) * reps // 60 - rest_dur_sec // 60

        modules.append({
            "name": spec["name"],
            "duration_minutes": total_duration,
            "type": "VO2max",
            "structure": structure
        })

    return modules


def generate_threshold_blocks() -> List[Dict[str, Any]]:
    """Generate threshold/FTP interval blocks.

    Threshold workouts at 95-105% FTP.
    Builds lactate threshold and sustainable power.
    """
    modules = []

    threshold_variations = [
        # Classic 2x20 (TrainerRoad staple)
        {"name": "Threshold Classic 2x20min", "reps": 2, "work_min": 20, "rest_min": 10, "power": 95},

        # 3x10 variations
        {"name": "Threshold Build 3x10min", "reps": 3, "work_min": 10, "rest_min": 5, "power": 98},
        {"name": "Threshold Power 3x12min", "reps": 3, "work_min": 12, "rest_min": 6, "power": 97},

        # 4x8 Norwegian-style
        {"name": "Threshold Norwegian 4x8min", "reps": 4, "work_min": 8, "rest_min": 4, "power": 98},
        {"name": "Threshold Hard 4x8min", "reps": 4, "work_min": 8, "rest_min": 3, "power": 100},

        # 5x5 variations
        {"name": "Threshold Short 5x5min", "reps": 5, "work_min": 5, "rest_min": 3, "power": 100},
        {"name": "Threshold Sustained 5x6min", "reps": 5, "work_min": 6, "rest_min": 4, "power": 98},

        # Single long efforts
        {"name": "Threshold Continuous 1x30min", "reps": 1, "work_min": 30, "rest_min": 0, "power": 95},
        {"name": "Threshold Extended 1x40min", "reps": 1, "work_min": 40, "rest_min": 0, "power": 93},

        # Ladder workouts
        {"name": "Threshold Ladder 3x15min", "reps": 3, "work_min": 15, "rest_min": 5, "power": 96},
    ]

    for spec in threshold_variations:
        structure = []
        reps = spec["reps"]
        work_min = spec["work_min"]
        rest_min = spec["rest_min"]
        power = spec["power"]

        for i in range(reps):
            # Work
            structure.append({
                "type": "steady",
                "power": power,
                "duration_minutes": work_min
            })

            # Rest (except after last rep)
            if i < reps - 1 and rest_min > 0:
                structure.append({
                    "type": "steady",
                    "power": 55,
                    "duration_minutes": rest_min
                })

        total_duration = work_min * reps + rest_min * (reps - 1)

        modules.append({
            "name": spec["name"],
            "duration_minutes": total_duration,
            "type": "Threshold",
            "structure": structure
        })

    return modules


def generate_sweetspot_blocks() -> List[Dict[str, Any]]:
    """Generate Sweet Spot interval blocks.

    Sweet Spot at 88-94% FTP.
    Maximum training benefit with manageable fatigue.
    """
    modules = []

    sst_variations = [
        # Classic SST (inspired by TrainerRoad)
        {"name": "SST Classic 3x10min", "reps": 3, "work_min": 10, "rest_min": 5, "power": 90},
        {"name": "SST Extended 3x12min", "reps": 3, "work_min": 12, "rest_min": 5, "power": 90},
        {"name": "SST Long 3x15min", "reps": 3, "work_min": 15, "rest_min": 5, "power": 88},

        # 4x intervals
        {"name": "SST Build 4x8min", "reps": 4, "work_min": 8, "rest_min": 4, "power": 92},
        {"name": "SST Power 4x10min", "reps": 4, "work_min": 10, "rest_min": 5, "power": 90},

        # 5x intervals
        {"name": "SST Short 5x6min", "reps": 5, "work_min": 6, "rest_min": 3, "power": 92},
        {"name": "SST Steady 5x8min", "reps": 5, "work_min": 8, "rest_min": 4, "power": 90},

        # 6x intervals (shorter but more reps)
        {"name": "SST Reps 6x5min", "reps": 6, "work_min": 5, "rest_min": 3, "power": 92},
        {"name": "SST Volume 6x6min", "reps": 6, "work_min": 6, "rest_min": 3, "power": 90},

        # Single long efforts (Zwift style)
        {"name": "SST Continuous 2x20min", "reps": 2, "work_min": 20, "rest_min": 5, "power": 88},
        {"name": "SST Long 1x30min", "reps": 1, "work_min": 30, "rest_min": 0, "power": 88},
        {"name": "SST Extended 1x40min", "reps": 1, "work_min": 40, "rest_min": 0, "power": 86},
    ]

    for spec in sst_variations:
        structure = []
        reps = spec["reps"]
        work_min = spec["work_min"]
        rest_min = spec["rest_min"]
        power = spec["power"]

        for i in range(reps):
            structure.append({
                "type": "steady",
                "power": power,
                "duration_minutes": work_min
            })

            if i < reps - 1 and rest_min > 0:
                structure.append({
                    "type": "steady",
                    "power": 60,
                    "duration_minutes": rest_min
                })

        total_duration = work_min * reps + rest_min * (reps - 1)

        modules.append({
            "name": spec["name"],
            "duration_minutes": total_duration,
            "type": "SweetSpot",
            "structure": structure
        })

    return modules


def generate_tempo_blocks() -> List[Dict[str, Any]]:
    """Generate tempo blocks (75-85% FTP).

    Tempo builds aerobic base with moderate intensity.
    """
    modules = []

    tempo_variations = [
        {"name": "Tempo Steady 20min", "duration": 20, "power": 80},
        {"name": "Tempo Extended 30min", "duration": 30, "power": 78},
        {"name": "Tempo Long 40min", "duration": 40, "power": 76},
        {"name": "Tempo Build 2x15min", "reps": 2, "work_min": 15, "rest_min": 5, "power": 82},
        {"name": "Tempo Sustained 2x20min", "reps": 2, "work_min": 20, "rest_min": 5, "power": 80},
        {"name": "Tempo Volume 3x12min", "reps": 3, "work_min": 12, "rest_min": 4, "power": 82},
    ]

    for spec in tempo_variations:
        if "reps" in spec:
            # Interval format
            structure = []
            for i in range(spec["reps"]):
                structure.append({
                    "type": "steady",
                    "power": spec["power"],
                    "duration_minutes": spec["work_min"]
                })
                if i < spec["reps"] - 1:
                    structure.append({
                        "type": "steady",
                        "power": 65,
                        "duration_minutes": spec["rest_min"]
                    })

            total_duration = spec["work_min"] * spec["reps"] + spec["rest_min"] * (spec["reps"] - 1)
        else:
            # Continuous format
            structure = [{
                "type": "steady",
                "power": spec["power"],
                "duration_minutes": spec["duration"]
            }]
            total_duration = spec["duration"]

        modules.append({
            "name": spec["name"],
            "duration_minutes": total_duration,
            "type": "Tempo",
            "structure": structure
        })

    return modules


def generate_mixed_blocks() -> List[Dict[str, Any]]:
    """Generate mixed/pyramid/over-under blocks.

    Complex workouts combining multiple zones.
    """
    modules = []

    # Over-under intervals (Sufferfest style)
    modules.append({
        "name": "Over Under 4x9min",
        "duration_minutes": 36,
        "type": "Mixed",
        "structure": [
            # Rep 1
            {"type": "steady", "power": 95, "duration_minutes": 2},
            {"type": "steady", "power": 105, "duration_minutes": 1},
            {"type": "steady", "power": 95, "duration_minutes": 2},
            {"type": "steady", "power": 105, "duration_minutes": 1},
            {"type": "steady", "power": 95, "duration_minutes": 2},
            {"type": "steady", "power": 105, "duration_minutes": 1},
            {"type": "steady", "power": 60, "duration_minutes": 3},
            # Rep 2
            {"type": "steady", "power": 95, "duration_minutes": 2},
            {"type": "steady", "power": 105, "duration_minutes": 1},
            {"type": "steady", "power": 95, "duration_minutes": 2},
            {"type": "steady", "power": 105, "duration_minutes": 1},
            {"type": "steady", "power": 95, "duration_minutes": 2},
            {"type": "steady", "power": 105, "duration_minutes": 1},
            {"type": "steady", "power": 60, "duration_minutes": 3},
            # Rep 3
            {"type": "steady", "power": 95, "duration_minutes": 2},
            {"type": "steady", "power": 105, "duration_minutes": 1},
            {"type": "steady", "power": 95, "duration_minutes": 2},
            {"type": "steady", "power": 105, "duration_minutes": 1},
            {"type": "steady", "power": 95, "duration_minutes": 2},
            {"type": "steady", "power": 105, "duration_minutes": 1},
            {"type": "steady", "power": 60, "duration_minutes": 3},
            # Rep 4
            {"type": "steady", "power": 95, "duration_minutes": 2},
            {"type": "steady", "power": 105, "duration_minutes": 1},
            {"type": "steady", "power": 95, "duration_minutes": 2},
            {"type": "steady", "power": 105, "duration_minutes": 1},
            {"type": "steady", "power": 95, "duration_minutes": 2},
            {"type": "steady", "power": 105, "duration_minutes": 1},
        ]
    })

    # Pyramid (TrainerRoad style)
    modules.append({
        "name": "Pyramid 1-2-3-2-1min",
        "duration_minutes": 17,
        "type": "Mixed",
        "structure": [
            {"type": "steady", "power": 120, "duration_minutes": 1},
            {"type": "steady", "power": 50, "duration_minutes": 1},
            {"type": "steady", "power": 115, "duration_minutes": 2},
            {"type": "steady", "power": 50, "duration_minutes": 2},
            {"type": "steady", "power": 110, "duration_minutes": 3},
            {"type": "steady", "power": 50, "duration_minutes": 2},
            {"type": "steady", "power": 115, "duration_minutes": 2},
            {"type": "steady", "power": 50, "duration_minutes": 1},
            {"type": "steady", "power": 120, "duration_minutes": 1},
        ]
    })

    return modules


def save_modules(modules: List[Dict[str, Any]], category_name: str):
    """Save generated modules to JSON files."""
    BASE_DIR.mkdir(parents=True, exist_ok=True)

    saved_count = 0
    skipped_count = 0

    for module in modules:
        filename = module["name"].lower().replace(" ", "_").replace("/", "_") + ".json"
        filepath = BASE_DIR / filename

        if filepath.exists():
            logger.debug(f"Skipping existing: {filename}")
            skipped_count += 1
            continue

        with open(filepath, 'w') as f:
            json.dump(module, f, indent=2)

        logger.info(f"Created: {filename}")
        saved_count += 1

    logger.info(f"{category_name}: Created {saved_count}, Skipped {skipped_count}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Generate pro workout blocks')
    parser.add_argument('--all', action='store_true', help='Generate all types')
    parser.add_argument('--vo2max', action='store_true', help='Generate VO2max blocks')
    parser.add_argument('--threshold', action='store_true', help='Generate threshold blocks')
    parser.add_argument('--sweetspot', action='store_true', help='Generate sweet spot blocks')
    parser.add_argument('--tempo', action='store_true', help='Generate tempo blocks')
    parser.add_argument('--mixed', action='store_true', help='Generate mixed/pyramid blocks')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be created')

    args = parser.parse_args()

    if not any([args.all, args.vo2max, args.threshold, args.sweetspot, args.tempo, args.mixed]):
        parser.print_help()
        return

    # Generate modules
    if args.all or args.vo2max:
        logger.info("Generating VO2max blocks...")
        modules = generate_vo2max_blocks()
        logger.info(f"Generated {len(modules)} VO2max variations")
        if not args.dry_run:
            save_modules(modules, "VO2max")
        else:
            for m in modules:
                print(f"  - {m['name']} ({m['duration_minutes']}min)")

    if args.all or args.threshold:
        logger.info("Generating threshold blocks...")
        modules = generate_threshold_blocks()
        logger.info(f"Generated {len(modules)} threshold variations")
        if not args.dry_run:
            save_modules(modules, "Threshold")
        else:
            for m in modules:
                print(f"  - {m['name']} ({m['duration_minutes']}min)")

    if args.all or args.sweetspot:
        logger.info("Generating sweet spot blocks...")
        modules = generate_sweetspot_blocks()
        logger.info(f"Generated {len(modules)} sweet spot variations")
        if not args.dry_run:
            save_modules(modules, "Sweet Spot")
        else:
            for m in modules:
                print(f"  - {m['name']} ({m['duration_minutes']}min)")

    if args.all or args.tempo:
        logger.info("Generating tempo blocks...")
        modules = generate_tempo_blocks()
        logger.info(f"Generated {len(modules)} tempo variations")
        if not args.dry_run:
            save_modules(modules, "Tempo")
        else:
            for m in modules:
                print(f"  - {m['name']} ({m['duration_minutes']}min)")

    if args.all or args.mixed:
        logger.info("Generating mixed blocks...")
        modules = generate_mixed_blocks()
        logger.info(f"Generated {len(modules)} mixed variations")
        if not args.dry_run:
            save_modules(modules, "Mixed")
        else:
            for m in modules:
                print(f"  - {m['name']} ({m['duration_minutes']}min)")

    if not args.dry_run:
        logger.info("✓ Pro workout block generation complete!")
    else:
        logger.info("Dry run complete. Use without --dry-run to create files.")


if __name__ == '__main__':
    main()
