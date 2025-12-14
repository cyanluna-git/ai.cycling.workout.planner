"""CLI utility for viewing Intervals.icu data."""

import argparse
from datetime import date, timedelta

from .config import load_config
from .clients.intervals import IntervalsClient
from .services.data_processor import DataProcessor


def format_activity(activity: dict) -> str:
    """Format activity for CLI display."""
    name = activity.get("name") or activity.get("type") or "Unknown"
    date_str = activity.get("start_date_local", "")[:10]
    tss = activity.get("icu_training_load") or activity.get("hr_load") or 0
    duration = activity.get("moving_time") or activity.get("elapsed_time") or 0
    duration_min = duration // 60
    distance = (
        activity.get("distance") or activity.get("icu_distance") or 0
    ) / 1000  # km
    avg_power = activity.get("icu_average_watts") or activity.get("average_watts") or 0
    avg_hr = activity.get("average_heartrate") or 0
    activity_type = activity.get("type", "")[:4]

    # Use heart rate if no power
    power_or_hr = (
        f"{avg_power:>3.0f}W"
        if avg_power
        else f"{avg_hr:>3.0f}❤️" if avg_hr else "  -  "
    )

    return f"  {date_str} | {activity_type:<4} | {name[:25]:<25} | TSS:{tss:>3.0f} | {duration_min:>3}min | {distance:>5.1f}km | {power_or_hr}"


def format_wellness(wellness: dict) -> str:
    """Format wellness data for CLI display."""
    date_str = wellness.get("id", "")
    hrv = wellness.get("hrv") or "-"
    rhr = wellness.get("restingHR") or "-"
    sleep_secs = wellness.get("sleepSecs") or 0
    sleep_h = sleep_secs / 3600 if sleep_secs else 0
    fatigue = wellness.get("fatigue") or "-"
    soreness = wellness.get("soreness") or "-"

    return f"  {date_str} | HRV: {hrv:>3} | RHR: {rhr:>3} | Sleep: {sleep_h:>4.1f}h | Fatigue: {fatigue} | Soreness: {soreness}"


def format_event(event: dict) -> str:
    """Format calendar event for CLI display."""
    date_str = event.get("start_date_local", "")[:10]
    name = event.get("name", "Unknown")
    category = event.get("category", "")
    duration = event.get("moving_time") or 0
    duration_min = duration // 60

    return f"  {date_str} | [{category:<8}] {name[:35]:<35} | {duration_min:>3}min"


def cmd_profile(client: IntervalsClient) -> None:
    """Show athlete profile."""
    print("\n🚴 Athlete Profile")
    print("=" * 50)

    profile = client.get_athlete_profile()

    print(f"  ID: {profile.get('id')}")
    print(f"  Name: {profile.get('name')}")
    print(f"  FTP: {profile.get('icu_ftp') or 'Not set'}W")
    print(f"  Weight: {profile.get('icu_weight') or 'Not set'}kg")
    print(f"  Max HR: {profile.get('max_hr') or 'Not set'}bpm")
    print(f"  LTHR: {profile.get('lthr') or 'Not set'}bpm")
    print()


def cmd_activities(
    client: IntervalsClient, days: int = 14, show_empty: bool = False
) -> None:
    """Show recent activities."""
    print(f"\n📊 Recent Activities (last {days} days)")
    print("=" * 95)
    print(
        f"  {'Date':<10} | {'Type':<5} | {'Name':<25} |  TSS | Time | Distance | Power/HR"
    )
    print("-" * 95)

    activities = client.get_recent_activities(days=days)

    # Filter out empty activities unless show_empty is True
    if not show_empty:
        activities = [
            a for a in activities if (a.get("moving_time") or 0) > 0 or (a.get("name"))
        ]

    if not activities:
        print("  No activities found. (Use --all to show empty records)")
    else:
        for activity in sorted(
            activities, key=lambda x: x.get("start_date_local", ""), reverse=True
        ):
            print(format_activity(activity))

        print(f"\n  Total: {len(activities)} activities")
        if not show_empty:
            print("  (Empty Strava sync records hidden. Use --all to show all)")

    print()


def cmd_wellness(client: IntervalsClient, days: int = 7) -> None:
    """Show recent wellness data."""
    print(f"\n💚 Wellness Data (last {days} days)")
    print("=" * 70)
    print(
        f"  {'Date':<10} | {'HRV':>4} | {'RHR':>4} | {'Sleep':>6} | {'Fatigue'} | {'Soreness'}"
    )
    print("-" * 70)

    wellness = client.get_recent_wellness(days=days)

    if not wellness:
        print("  No wellness data found.")
    else:
        for w in sorted(wellness, key=lambda x: x.get("id", ""), reverse=True):
            print(format_wellness(w))

    print()


def cmd_events(client: IntervalsClient, days: int = 14) -> None:
    """Show upcoming calendar events."""
    print(f"\n📅 Calendar Events (next {days} days)")
    print("=" * 70)
    print(f"  {'Date':<10} | {'Category':<10} {'Name':<35} | {'Duration':>4}")
    print("-" * 70)

    oldest = date.today()
    newest = oldest + timedelta(days=days)
    events = client.get_events(oldest, newest)

    if not events:
        print("  No events found.")
    else:
        for event in sorted(events, key=lambda x: x.get("start_date_local", "")):
            print(format_event(event))

    print()


def cmd_metrics(client: IntervalsClient) -> None:
    """Show current training metrics."""
    print("\n📈 Training Metrics")
    print("=" * 50)

    processor = DataProcessor()
    activities = client.get_recent_activities(days=42)
    wellness = client.get_recent_wellness(days=7)

    metrics = processor.calculate_training_metrics(activities)
    well = processor.analyze_wellness(wellness)

    print(f"  CTL (Fitness):  {metrics.ctl:>6.1f}")
    print(f"  ATL (Fatigue):  {metrics.atl:>6.1f}")
    print(f"  TSB (Form):     {metrics.tsb:>6.1f}  ({metrics.form_status})")
    print()
    print(f"  Wellness Readiness: {well.readiness}")
    if well.hrv:
        print(f"  HRV: {well.hrv}")
    if well.rhr:
        print(f"  RHR: {well.rhr}bpm")
    if well.sleep_hours:
        print(f"  Sleep: {well.sleep_hours:.1f}h")
    print()


def cmd_summary(client: IntervalsClient) -> None:
    """Show full summary (profile + metrics + recent)."""
    cmd_profile(client)
    cmd_metrics(client)
    cmd_activities(client, days=7)
    cmd_wellness(client, days=7)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="View Intervals.icu data from command line",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  summary      Show full summary (default)
  profile      Show athlete profile
  activities   Show recent activities
  wellness     Show recent wellness data
  events       Show calendar events
  metrics      Show training metrics (CTL/ATL/TSB)

Examples:
  python -m src.cli summary
  python -m src.cli activities --days 30
  python -m src.cli wellness
        """,
    )

    parser.add_argument(
        "command",
        nargs="?",
        default="summary",
        choices=["summary", "profile", "activities", "wellness", "events", "metrics"],
        help="Command to run (default: summary)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=14,
        help="Number of days to show (default: 14)",
    )
    parser.add_argument(
        "--env-file",
        type=str,
        help="Path to .env file",
    )

    args = parser.parse_args()

    # Load config and create client
    config = load_config(args.env_file)
    client = IntervalsClient(config.intervals)

    # Run command
    commands = {
        "summary": lambda: cmd_summary(client),
        "profile": lambda: cmd_profile(client),
        "activities": lambda: cmd_activities(client, args.days),
        "wellness": lambda: cmd_wellness(client, args.days),
        "events": lambda: cmd_events(client, args.days),
        "metrics": lambda: cmd_metrics(client),
    }

    commands[args.command]()


if __name__ == "__main__":
    main()
