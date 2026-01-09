#!/usr/bin/env python3
"""Import popular workouts from Intervals.icu and convert to JSON modules.

This script fetches workout events from your Intervals.icu calendar,
extracts the main segments, and converts them to JSON module format
for use in the workout generator.

Usage:
    python scripts/import_intervals_workouts.py --days 90 --limit 20
"""

import json
import logging
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clients.intervals import IntervalsClient
from src.config import load_config
from src.services.intervals_parser import parse_workout_doc_steps

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def sanitize_filename(name: str) -> str:
    """Convert workout name to valid filename."""
    # Remove special characters, keep alphanumeric and spaces
    name = re.sub(r'[^\w\s-]', '', name)
    # Replace spaces and hyphens with underscore
    name = re.sub(r'[-\s]+', '_', name)
    # Lowercase
    name = name.lower()
    # Limit length
    return name[:50]


def convert_intervals_step_to_module_structure(step: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Convert Intervals.icu workout_doc step to our module structure format.

    Args:
        step: Intervals.icu workout_doc step

    Returns:
        Module structure block or None
    """
    # Handle repeat blocks (intervals)
    if 'repeat' in step and 'steps' in step:
        # For now, skip nested repeats - too complex for simple module import
        return None

    duration_sec = step.get('duration', 0)
    if duration_sec == 0:
        return None

    # Get power - handle both single power and ramps
    if step.get('ramp'):
        # This is a ramp
        power_low = step.get('power_low', step.get('power', 50))
        power_high = step.get('power_high', step.get('power', 50))

        return {
            "type": "ramp",
            "start_power": int(power_low),
            "end_power": int(power_high),
            "duration_seconds": int(duration_sec)
        }
    else:
        # Steady power
        power = step.get('power', step.get('power_low', 50))

        if duration_sec >= 60:
            return {
                "type": "steady",
                "power": int(power),
                "duration_minutes": int(duration_sec / 60)
            }
        else:
            return {
                "type": "steady",
                "power": int(power),
                "duration_seconds": int(duration_sec)
            }


def extract_main_segment(workout_doc: Optional[Dict[str, Any]], workout_name: str) -> Optional[Dict[str, Any]]:
    """Extract main segment from workout_doc, excluding warmup/cooldown.

    Args:
        workout_doc: Intervals.icu workout_doc structure
        workout_name: Name of the workout

    Returns:
        JSON module dict or None if unable to extract
    """
    if not workout_doc or 'steps' not in workout_doc:
        return None

    try:
        steps = workout_doc['steps']

        if len(steps) < 3:
            # Need at least warmup + main + cooldown
            return None

        # Heuristic: Skip first step (warmup) and last step (cooldown)
        # Take middle steps as "main"
        main_steps = steps[1:-1]

        if not main_steps:
            return None

        # Convert steps to our structure format
        structure = []
        total_duration = 0
        power_values = []

        for step in main_steps:
            # Skip repeat blocks for simplicity
            if 'repeat' in step:
                continue

            converted = convert_intervals_step_to_module_structure(step)
            if converted:
                structure.append(converted)

                # Track duration and power for metadata
                duration_sec = step.get('duration', 0)
                total_duration += duration_sec

                power = step.get('power', step.get('power_low', 50))
                power_values.append(power)

        if not structure:
            return None

        # Determine workout type based on average power
        avg_power = sum(power_values) / len(power_values) if power_values else 50

        if avg_power >= 115:
            workout_type = "VO2max"
        elif avg_power >= 95:
            workout_type = "Threshold"
        elif avg_power >= 88:
            workout_type = "SweetSpot"
        else:
            workout_type = "Endurance"

        # Build module
        module = {
            "name": workout_name,
            "duration_minutes": int(total_duration / 60),
            "type": workout_type,
            "structure": structure,
        }

        return module

    except Exception as e:
        logger.error(f"Failed to extract main segment from '{workout_name}': {e}")
        return None


def fetch_workouts_from_intervals(
    client: IntervalsClient,
    days: int = 90,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """Fetch workout events from Intervals.icu.

    Args:
        client: Intervals.icu API client
        days: Number of days to look back
        limit: Maximum number of workouts to import

    Returns:
        List of workout modules
    """
    logger.info(f"Fetching workouts from last {days} days...")

    newest = date.today()
    oldest = newest - timedelta(days=days)

    events = client.get_events(oldest, newest)

    # Filter workout events that have descriptions
    workouts = []
    for event in events:
        if event.get('category') != 'WORKOUT':
            continue

        description = event.get('description', '').strip()
        if not description or len(description) < 10:
            continue

        name = event.get('name', 'Unnamed Workout')

        # Skip AI-generated workouts (avoid importing our own generated workouts)
        if 'AI Generated' in name or 'Generated by AI' in name:
            continue

        workouts.append({
            'name': name,
            'description': description,
            'date': event.get('start_date_local'),
            'tss': event.get('icu_training_load'),
        })

    logger.info(f"Found {len(workouts)} workout events")

    # Limit number of workouts
    workouts = workouts[:limit]

    # Convert to modules
    modules = []
    for workout in workouts:
        module = extract_main_segment(workout['description'], workout['name'])
        if module:
            modules.append(module)
            logger.info(f"Extracted: {module['name']} ({module['type']}, {module['duration_minutes']}min)")

    return modules


def save_modules(modules: List[Dict[str, Any]], output_dir: Path):
    """Save modules as JSON files.

    Args:
        modules: List of workout modules
        output_dir: Directory to save JSON files
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    saved_count = 0
    for module in modules:
        filename = sanitize_filename(module['name']) + '.json'
        filepath = output_dir / filename

        # Check if file already exists
        if filepath.exists():
            logger.warning(f"File already exists, skipping: {filename}")
            continue

        # Save JSON
        with open(filepath, 'w') as f:
            json.dump(module, f, indent=2)

        logger.info(f"Saved: {filepath}")
        saved_count += 1

    logger.info(f"Saved {saved_count} new modules")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Import workouts from Intervals.icu')
    parser.add_argument('--days', type=int, default=90, help='Days to look back (default: 90)')
    parser.add_argument('--limit', type=int, default=20, help='Max workouts to import (default: 20)')
    parser.add_argument('--output', type=str, default='src/data/workout_modules/main',
                        help='Output directory (default: src/data/workout_modules/main)')

    args = parser.parse_args()

    # Load config
    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        logger.error("Make sure .env file is configured with Intervals.icu credentials")
        sys.exit(1)

    # Create client
    client = IntervalsClient(config.intervals)

    # Fetch workouts
    try:
        modules = fetch_workouts_from_intervals(client, days=args.days, limit=args.limit)
    except Exception as e:
        logger.error(f"Failed to fetch workouts: {e}")
        sys.exit(1)

    if not modules:
        logger.warning("No workouts imported")
        return

    # Save modules
    output_dir = Path(args.output)
    save_modules(modules, output_dir)

    logger.info("✓ Import complete!")


if __name__ == '__main__':
    main()
