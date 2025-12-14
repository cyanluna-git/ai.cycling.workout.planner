"""Main entry point for AI Cycling Coach.

This module orchestrates the entire workflow:
1. Fetch activity and wellness data from Intervals.icu
2. Calculate training metrics
3. Generate AI workout
4. Register workout on Intervals.icu calendar
"""

import argparse
import logging
import sys
from datetime import date
from pathlib import Path
from typing import Optional

from .config import load_config, Config
from .clients.intervals import IntervalsClient, IntervalsAPIError
from .clients.llm import LLMClient
from .services.data_processor import DataProcessor
from .services.workout_generator import WorkoutGenerator


def setup_logging(config: Config) -> None:
    """Set up logging configuration.

    Args:
        config: Application configuration.
    """
    log_file = Path(config.scheduler.log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, config.scheduler.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )


def run_daily_workflow(
    config: Config,
    target_date: Optional[date] = None,
    dry_run: bool = False,
    force: bool = False,
    duration: int = 60,
    style: str = "auto",
    notes: str = "",
    intensity: str = "auto",
    indoor: bool = False,
) -> bool:
    """Run the daily workout generation workflow.

    Args:
        config: Application configuration.
        target_date: Date to generate workout for (default: today).
        dry_run: If True, don't actually create the workout.
        force: If True, create workout even if one exists.
        duration: Target workout duration in minutes.
        style: Training style (auto, polarized, norwegian, etc.).
        notes: Additional user notes for the AI.
        intensity: Intensity preference (auto, easy, moderate, hard).
        indoor: If True, generate indoor trainer workout.

    Returns:
        True if successful, False otherwise.
    """
    logger = logging.getLogger(__name__)
    target_date = target_date or date.today()

    logger.info(f"=== AI Cycling Coach - Daily Workflow ===")
    logger.info(f"Target date: {target_date}")
    logger.info(f"Dry run: {dry_run}, Force: {force}")
    logger.info(f"Duration: {duration}min, Style: {style}, Intensity: {intensity}")
    if notes:
        logger.info(f"Notes: {notes}")
    if indoor:
        logger.info("Mode: Indoor trainer")

    try:
        # Initialize clients
        intervals = IntervalsClient(config.intervals)
        llm = LLMClient.from_config(config.llm)
        processor = DataProcessor()
        generator = WorkoutGenerator(
            llm, config.user_profile, max_duration_minutes=duration
        )

        # Step 1: Check for existing workout
        logger.info("Step 1: Checking for existing workout...")
        existing = intervals.check_workout_exists(target_date)

        if existing and not force:
            logger.info(f"Workout already exists: {existing.get('name')}")
            logger.info("Use --force to override. Exiting.")
            return True

        if existing and force:
            logger.warning(f"Force mode: will replace existing workout")

        # Step 2: Fetch activity data (last 42 days)
        logger.info("Step 2: Fetching activity data (42 days)...")
        activities = intervals.get_recent_activities(days=42)
        logger.info(f"Retrieved {len(activities)} activities")

        # Step 3: Fetch wellness data (last 7 days)
        logger.info("Step 3: Fetching wellness data (7 days)...")
        wellness_data = intervals.get_recent_wellness(days=7)
        logger.info(f"Retrieved {len(wellness_data)} wellness records")

        # Step 4: Calculate training metrics
        logger.info("Step 4: Calculating training metrics...")
        training_metrics = processor.calculate_training_metrics(activities)
        wellness_metrics = processor.analyze_wellness(wellness_data)

        logger.info(
            f"Training: CTL={training_metrics.ctl:.1f}, ATL={training_metrics.atl:.1f}, TSB={training_metrics.tsb:.1f}"
        )
        logger.info(f"Wellness: {wellness_metrics.readiness}")

        # Step 5: Generate workout with AI
        logger.info("Step 5: Generating workout with AI...")
        workout = generator.generate(
            training_metrics,
            wellness_metrics,
            target_date,
            style=style,
            notes=notes,
            intensity=intensity,
            indoor=indoor,
        )

        logger.info(f"Generated: {workout.name}")
        logger.info(
            f"Type: {workout.workout_type}, Duration: ~{workout.estimated_duration_minutes}min"
        )
        logger.info(f"Workout text:\n{workout.workout_text}")

        if dry_run:
            logger.info("Dry run mode - not creating workout on Intervals.icu")
            return True

        # Step 6: Create workout on Intervals.icu
        logger.info("Step 6: Creating workout on Intervals.icu...")

        # Delete existing if force mode
        if existing and force:
            intervals.delete_event(existing["id"])

        # Create new workout
        event = intervals.create_workout(
            target_date=target_date,
            name=workout.name,
            description=workout.description,
            moving_time=workout.estimated_duration_minutes * 60,
            training_load=workout.estimated_tss,
        )

        logger.info(f"Workout created successfully! Event ID: {event.get('id')}")
        logger.info("Wahoo sync: Workout will be available on your device after sync")

        return True

    except IntervalsAPIError as e:
        logger.error(f"Intervals.icu API error: {e}")
        return False
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return False


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(
        description="AI Cycling Coach - Generate daily workouts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main                    # Run for today
  python -m src.main --dry-run          # Test without creating workout
  python -m src.main --date 2024-12-20  # Generate for specific date
  python -m src.main --force            # Replace existing workout
        """,
    )

    parser.add_argument(
        "--date",
        type=str,
        help="Target date (YYYY-MM-DD format, default: today)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't create workout, just show what would be generated",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Create workout even if one already exists",
    )
    parser.add_argument(
        "--env-file",
        type=str,
        help="Path to .env file",
    )

    # Workout customization parameters
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Target workout duration in minutes (default: 60)",
    )
    parser.add_argument(
        "--style",
        type=str,
        choices=[
            "auto",
            "polarized",
            "norwegian",
            "pyramidal",
            "threshold",
            "sweetspot",
            "endurance",
        ],
        default="auto",
        help="Training style: auto, polarized, norwegian, pyramidal, threshold, sweetspot, endurance",
    )
    parser.add_argument(
        "--notes",
        type=str,
        default="",
        help="Additional notes or requests for the AI (e.g., 'focus on climbing')",
    )
    parser.add_argument(
        "--intensity",
        type=str,
        choices=["auto", "easy", "moderate", "hard"],
        default="auto",
        help="Intensity preference: auto, easy, moderate, hard",
    )
    parser.add_argument(
        "--indoor",
        action="store_true",
        help="Generate indoor trainer workout (structured intervals)",
    )

    args = parser.parse_args()

    # Load configuration
    try:
        config = load_config(args.env_file)
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        print("Please check your .env file or environment variables.", file=sys.stderr)
        return 1

    # Set up logging
    setup_logging(config)

    # Parse target date
    target_date = None
    if args.date:
        try:
            target_date = date.fromisoformat(args.date)
        except ValueError:
            print(f"Invalid date format: {args.date}. Use YYYY-MM-DD.", file=sys.stderr)
            return 1

    # Run workflow
    success = run_daily_workflow(
        config=config,
        target_date=target_date,
        dry_run=args.dry_run,
        force=args.force,
        duration=args.duration,
        style=args.style,
        notes=args.notes,
        intensity=args.intensity,
        indoor=args.indoor,
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
