import json
import sys
import os

# Add src to path
sys.path.append(os.getcwd())

from src.services.workout_skeleton import RampBlock
from src.services.protocol_builder import ProtocolBuilder


def test_ramp_builder():
    # Create a dummy ramp block matching user's scenario
    # "duration":480,"warmup":true,"ramp":true,"power":{"start":48,"end":68,"units":"%ftp"}

    block = RampBlock(
        type="warmup_ramp",
        start_power=48,
        end_power=68,
        duration_minutes=8,  # 480 seconds / 60
    )

    builder = ProtocolBuilder()
    # Access private method for direct test, or use public if wrapped in skeleton
    steps = builder._build_ramp(block)

    print(json.dumps(steps, indent=2))


if __name__ == "__main__":
    test_ramp_builder()
