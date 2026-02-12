"""Test script for workout creation without AI.

Requires INTERVALS_API_KEY and ATHLETE_ID env vars.
"""

import os
import pytest

from datetime import date
from src.config import load_config
from src.clients.intervals import IntervalsClient

# Sample workout - each step on its own line, no multiplier
SAMPLE_WORKOUT = """Warmup
- 10m 50%

Main Set
- 5m 100%
- 5m 50%
- 5m 100%
- 5m 50%
- 5m 100%
- 5m 50%

Cooldown
- 10m 50%"""

SAMPLE_NAME = "Test Workout - Sweet Spot v3"


@pytest.mark.skipif(
    not os.getenv("INTERVALS_API_KEY"),
    reason="INTERVALS_API_KEY not set (integration test)"
)
def test_create_workout(target_date: str = None):
    """Create a test workout on the specified date."""
    config = load_config()
    client = IntervalsClient(config.intervals)

    target = date.fromisoformat(target_date) if target_date else date.today()

    print(f"Creating test workout on {target}...")
    print(f"Workout text:\n{SAMPLE_WORKOUT}")
    print()

    # Try creating with just workout text in description
    event = client.create_workout(
        target_date=target,
        name=SAMPLE_NAME,
        description=SAMPLE_WORKOUT,  # Just the workout text, no extra text
        moving_time=55 * 60,  # 55 minutes
    )

    print(f"✅ Created! Event ID: {event.get('id')}")
    print(f"Event details:")
    for key in ["id", "name", "category", "moving_time", "description"]:
        print(f"  {key}: {event.get(key)}")

    return event


if __name__ == "__main__":
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else "2025-12-15"
    test_create_workout(target)
