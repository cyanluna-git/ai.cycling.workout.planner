import json
import sys
import os

# Add src to path
sys.path.append(os.getcwd())

from src.services.workout_skeleton import BarcodeBlock
from src.services.protocol_builder import ProtocolBuilder


def test_barcode_builder():
    # Create a dummy barcode block: 10x 40s/20s
    block = BarcodeBlock(
        type="barcode",
        on_power=120,
        off_power=50,
        on_duration_seconds=40,
        off_duration_seconds=20,
        repetitions=10,
    )

    builder = ProtocolBuilder()
    steps = builder._convert_block(block)

    print(json.dumps(steps, indent=2))


if __name__ == "__main__":
    test_barcode_builder()
