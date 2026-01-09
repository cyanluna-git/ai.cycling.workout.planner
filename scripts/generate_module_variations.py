#!/usr/bin/env python3
"""Generate variations of warmup, cooldown, and rest modules.

This script creates multiple variations of basic workout modules
to increase variety in workout generation.

Usage:
    python scripts/generate_module_variations.py --all
    python scripts/generate_module_variations.py --warmup
    python scripts/generate_module_variations.py --cooldown
    python scripts/generate_module_variations.py --rest
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

# Base directories
BASE_DIR = Path(__file__).parent.parent / "src" / "data" / "workout_modules"


def generate_warmup_modules() -> List[Dict[str, Any]]:
    """Generate various warmup module variations.

    Warmups typically:
    - Start at 40-50% FTP
    - Gradually ramp up to 70-80% FTP
    - Duration: 5-20 minutes
    - May include short bursts to "open up" the legs
    """
    modules = []

    # 1. Progressive ramps (different durations)
    for duration in [5, 8, 12, 15, 20]:
        modules.append({
            "name": f"Progressive Ramp {duration}min",
            "duration_minutes": duration,
            "structure": [
                {
                    "type": "warmup_ramp",
                    "start_power": 40,
                    "end_power": 70,
                    "duration_minutes": duration
                }
            ]
        })

    # 2. Stepped warmups (gradual intensity steps)
    for duration in [10, 15, 20]:
        step_duration = duration // 4
        modules.append({
            "name": f"Stepped Warmup {duration}min",
            "duration_minutes": duration,
            "structure": [
                {"type": "steady", "power": 45, "duration_minutes": step_duration},
                {"type": "steady", "power": 55, "duration_minutes": step_duration},
                {"type": "steady", "power": 65, "duration_minutes": step_duration},
                {"type": "steady", "power": 75, "duration_minutes": step_duration},
            ]
        })

    # 3. Warmup with openers (short bursts)
    modules.append({
        "name": "Warmup with Openers 12min",
        "duration_minutes": 12,
        "structure": [
            {"type": "steady", "power": 50, "duration_minutes": 5},
            {"type": "steady", "power": 90, "duration_seconds": 30},
            {"type": "steady", "power": 50, "duration_minutes": 2},
            {"type": "steady", "power": 100, "duration_seconds": 30},
            {"type": "steady", "power": 50, "duration_minutes": 2},
            {"type": "steady", "power": 110, "duration_seconds": 30},
            {"type": "steady", "power": 60, "duration_minutes": 1},
        ]
    })

    modules.append({
        "name": "Warmup with Openers 15min",
        "duration_minutes": 15,
        "structure": [
            {"type": "steady", "power": 50, "duration_minutes": 7},
            {"type": "steady", "power": 90, "duration_seconds": 30},
            {"type": "steady", "power": 50, "duration_minutes": 2},
            {"type": "steady", "power": 100, "duration_seconds": 30},
            {"type": "steady", "power": 50, "duration_minutes": 2},
            {"type": "steady", "power": 110, "duration_seconds": 30},
            {"type": "steady", "power": 50, "duration_minutes": 2},
        ]
    })

    # 4. Quick warmup for time-constrained workouts
    modules.append({
        "name": "Quick Warmup 5min",
        "duration_minutes": 5,
        "structure": [
            {"type": "warmup_ramp", "start_power": 50, "end_power": 75, "duration_minutes": 5}
        ]
    })

    # 5. Extended warmup for races/hard efforts
    modules.append({
        "name": "Race Prep Warmup 25min",
        "duration_minutes": 25,
        "structure": [
            {"type": "steady", "power": 50, "duration_minutes": 10},
            {"type": "steady", "power": 65, "duration_minutes": 5},
            {"type": "steady", "power": 90, "duration_minutes": 2},
            {"type": "steady", "power": 50, "duration_minutes": 3},
            {"type": "steady", "power": 100, "duration_minutes": 1},
            {"type": "steady", "power": 50, "duration_minutes": 2},
            {"type": "steady", "power": 110, "duration_seconds": 30},
            {"type": "steady", "power": 60, "duration_minutes": 1},
            {"type": "steady", "power": 60, "duration_seconds": 30},
        ]
    })

    return modules


def generate_cooldown_modules() -> List[Dict[str, Any]]:
    """Generate various cooldown module variations.

    Cooldowns typically:
    - Start at 60-70% FTP
    - Gradually decrease to 40-50% FTP
    - Duration: 5-20 minutes
    - Smooth, gradual reduction
    """
    modules = []

    # 1. Progressive fade (different durations)
    for duration in [5, 8, 10, 12, 15, 20]:
        modules.append({
            "name": f"Fade Out {duration}min",
            "duration_minutes": duration,
            "structure": [
                {
                    "type": "cooldown_ramp",
                    "start_power": 65,
                    "end_power": 45,
                    "duration_minutes": duration
                }
            ]
        })

    # 2. Stepped cooldowns (gradual steps down)
    for duration in [10, 15, 20]:
        step_duration = duration // 4
        modules.append({
            "name": f"Stepped Cooldown {duration}min",
            "duration_minutes": duration,
            "structure": [
                {"type": "steady", "power": 70, "duration_minutes": step_duration},
                {"type": "steady", "power": 60, "duration_minutes": step_duration},
                {"type": "steady", "power": 50, "duration_minutes": step_duration},
                {"type": "steady", "power": 40, "duration_minutes": step_duration},
            ]
        })

    # 3. Active recovery cooldown (slightly higher intensity)
    modules.append({
        "name": "Active Recovery Cooldown 12min",
        "duration_minutes": 12,
        "structure": [
            {"type": "steady", "power": 70, "duration_minutes": 4},
            {"type": "steady", "power": 60, "duration_minutes": 4},
            {"type": "steady", "power": 50, "duration_minutes": 4},
        ]
    })

    # 4. Quick cooldown
    modules.append({
        "name": "Quick Cooldown 5min",
        "duration_minutes": 5,
        "structure": [
            {"type": "cooldown_ramp", "start_power": 65, "end_power": 50, "duration_minutes": 5}
        ]
    })

    # 5. Extended flush (for hard workouts)
    modules.append({
        "name": "Extended Flush 25min",
        "duration_minutes": 25,
        "structure": [
            {"type": "steady", "power": 65, "duration_minutes": 10},
            {"type": "cooldown_ramp", "start_power": 65, "end_power": 45, "duration_minutes": 15}
        ]
    })

    # 6. Two-stage cooldown
    modules.append({
        "name": "Two Stage Cooldown 15min",
        "duration_minutes": 15,
        "structure": [
            {"type": "steady", "power": 70, "duration_minutes": 5},
            {"type": "steady", "power": 55, "duration_minutes": 5},
            {"type": "cooldown_ramp", "start_power": 55, "end_power": 40, "duration_minutes": 5}
        ]
    })

    return modules


def generate_rest_modules() -> List[Dict[str, Any]]:
    """Generate various rest/recovery module variations.

    Rest modules are inserted between intense main sets.
    - Power: 40-60% FTP
    - Duration: 1-10 minutes
    - Can be active (50-60%) or very easy (40-50%)
    """
    modules = []

    # 1. Standard rest periods (different durations)
    for duration in [1, 2, 3, 4, 5]:
        modules.append({
            "name": f"Easy Rest {duration}min",
            "duration_minutes": duration,
            "structure": [
                {"type": "steady", "power": 50, "duration_minutes": duration}
            ]
        })

    # 2. Active recovery (slightly higher intensity)
    for duration in [2, 3, 4, 5]:
        modules.append({
            "name": f"Active Recovery {duration}min",
            "duration_minutes": duration,
            "structure": [
                {"type": "steady", "power": 60, "duration_minutes": duration}
            ]
        })

    # 3. Very easy rest (for hard intervals)
    for duration in [2, 3, 4, 5, 8, 10]:
        modules.append({
            "name": f"Very Easy Rest {duration}min",
            "duration_minutes": duration,
            "structure": [
                {"type": "steady", "power": 45, "duration_minutes": duration}
            ]
        })

    # 4. Short rest (for short intervals)
    for seconds in [30, 45, 60, 90]:
        minutes = seconds / 60
        modules.append({
            "name": f"Short Rest {seconds}s",
            "duration_minutes": round(minutes, 2),
            "structure": [
                {"type": "steady", "power": 50, "duration_seconds": seconds}
            ]
        })

    # 5. Graduated rest (start easy, gradually increase)
    modules.append({
        "name": "Graduated Rest 5min",
        "duration_minutes": 5,
        "structure": [
            {"type": "steady", "power": 45, "duration_minutes": 2},
            {"type": "steady", "power": 55, "duration_minutes": 2},
            {"type": "steady", "power": 65, "duration_minutes": 1},
        ]
    })

    # 6. Flushing rest (higher cadence, moderate power)
    modules.append({
        "name": "Flush Rest 3min",
        "duration_minutes": 3,
        "structure": [
            {"type": "steady", "power": 60, "duration_minutes": 3}
        ]
    })

    modules.append({
        "name": "Flush Rest 5min",
        "duration_minutes": 5,
        "structure": [
            {"type": "steady", "power": 60, "duration_minutes": 5}
        ]
    })

    return modules


def save_modules(modules: List[Dict[str, Any]], category: str):
    """Save generated modules to JSON files.

    Args:
        modules: List of module dictionaries
        category: Category name (warmup/cooldown/rest)
    """
    output_dir = BASE_DIR / category
    output_dir.mkdir(parents=True, exist_ok=True)

    saved_count = 0
    skipped_count = 0

    for module in modules:
        # Generate filename from name
        filename = module["name"].lower().replace(" ", "_").replace("/", "_") + ".json"
        filepath = output_dir / filename

        # Check if already exists
        if filepath.exists():
            logger.debug(f"Skipping existing: {filename}")
            skipped_count += 1
            continue

        # Save JSON
        with open(filepath, 'w') as f:
            json.dump(module, f, indent=2)

        logger.info(f"Created: {category}/{filename}")
        saved_count += 1

    logger.info(f"Category '{category}': Created {saved_count}, Skipped {skipped_count} (already exist)")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Generate workout module variations')
    parser.add_argument('--all', action='store_true', help='Generate all categories')
    parser.add_argument('--warmup', action='store_true', help='Generate warmup modules')
    parser.add_argument('--cooldown', action='store_true', help='Generate cooldown modules')
    parser.add_argument('--rest', action='store_true', help='Generate rest modules')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be created without creating')

    args = parser.parse_args()

    # If no specific category selected, show help
    if not (args.all or args.warmup or args.cooldown or args.rest):
        parser.print_help()
        return

    # Generate modules
    if args.all or args.warmup:
        logger.info("Generating warmup modules...")
        modules = generate_warmup_modules()
        logger.info(f"Generated {len(modules)} warmup variations")
        if not args.dry_run:
            save_modules(modules, "warmup")
        else:
            for m in modules:
                print(f"  - {m['name']} ({m['duration_minutes']}min)")

    if args.all or args.cooldown:
        logger.info("Generating cooldown modules...")
        modules = generate_cooldown_modules()
        logger.info(f"Generated {len(modules)} cooldown variations")
        if not args.dry_run:
            save_modules(modules, "cooldown")
        else:
            for m in modules:
                print(f"  - {m['name']} ({m['duration_minutes']}min)")

    if args.all or args.rest:
        logger.info("Generating rest modules...")
        modules = generate_rest_modules()
        logger.info(f"Generated {len(modules)} rest variations")
        if not args.dry_run:
            save_modules(modules, "rest")
        else:
            for m in modules:
                print(f"  - {m['name']} ({m['duration_minutes']}min)")

    if not args.dry_run:
        logger.info("✓ Module generation complete!")
    else:
        logger.info("Dry run complete. Use without --dry-run to create files.")


if __name__ == '__main__':
    main()
