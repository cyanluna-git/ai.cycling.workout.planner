"""Scheduler for daily workout generation.

This module sets up a scheduler to run the workout generation
at a specified time each day.
"""

import logging
import time
from datetime import datetime
from typing import Callable, Optional

import schedule

from .config import load_config, SchedulerConfig
from .main import run_daily_workflow

logger = logging.getLogger(__name__)


def create_job(config_path: Optional[str] = None) -> Callable:
    """Create a scheduled job function.

    Args:
        config_path: Optional path to .env file.

    Returns:
        Job function to run daily.
    """

    def job():
        logger.info("Starting scheduled workout generation...")

        try:
            config = load_config(config_path)
            success = run_daily_workflow(config)

            if success:
                logger.info("Scheduled job completed successfully")
            else:
                logger.error("Scheduled job failed")

        except Exception as e:
            logger.exception(f"Error in scheduled job: {e}")

    return job


def run_scheduler(
    schedule_time: str = "06:00",
    config_path: Optional[str] = None,
) -> None:
    """Run the scheduler.

    Args:
        schedule_time: Time to run daily (HH:MM format).
        config_path: Optional path to .env file.
    """
    logger.info(f"Starting scheduler - daily at {schedule_time}")

    # Create job
    job = create_job(config_path)

    # Schedule daily execution
    schedule.every().day.at(schedule_time).do(job)

    logger.info("Scheduler is running. Press Ctrl+C to stop.")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")


def main():
    """Main entry point for scheduler."""
    import argparse

    parser = argparse.ArgumentParser(description="AI Cycling Coach Scheduler")
    parser.add_argument(
        "--time",
        type=str,
        default="06:00",
        help="Time to run daily (HH:MM format, default: 06:00)",
    )
    parser.add_argument(
        "--env-file",
        type=str,
        help="Path to .env file",
    )
    parser.add_argument(
        "--run-now",
        action="store_true",
        help="Run immediately and then start scheduler",
    )

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run immediately if requested
    if args.run_now:
        logger.info("Running immediately as requested...")
        job = create_job(args.env_file)
        job()

    # Start scheduler
    run_scheduler(schedule_time=args.time, config_path=args.env_file)


if __name__ == "__main__":
    main()
