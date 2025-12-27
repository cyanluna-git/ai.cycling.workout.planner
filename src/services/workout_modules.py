"""
Modular Workout Segments Library (v3).

Loads composable workout blocks from JSON files in `src/data/workout_modules`.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Base directory for module data
# Assuming src/services/workout_modules.py -> src/data/workout_modules
BASE_DIR = Path(__file__).parent.parent / "data" / "workout_modules"


def _load_modules(category: str) -> Dict[str, Dict[str, Any]]:
    """Load JSON modules from a category directory."""
    modules = {}
    category_dir = BASE_DIR / category

    if not category_dir.exists():
        logger.warning(f"Module directory not found: {category_dir}")
        return modules

    for json_file in category_dir.glob("*.json"):
        try:
            with open(json_file, "r") as f:
                data = json.load(f)
                key = json_file.stem
                modules[key] = data
        except Exception as e:
            logger.error(f"Failed to load module {json_file}: {e}")

    return modules


# Load dictionaries on module import
WARMUP_MODULES = _load_modules("warmup")
MAIN_SEGMENTS = _load_modules("main")
REST_SEGMENTS = _load_modules("rest")
COOLDOWN_MODULES = _load_modules("cooldown")


def get_module_inventory_text() -> str:
    """Format all modules into a text inventory for LLM prompts."""
    inventory = []

    inventory.append("--- WARMUP MODULES ---")
    for key, data in sorted(WARMUP_MODULES.items()):
        inventory.append(f"- [{key}] {data['name']} ({data['duration_minutes']} min)")

    inventory.append("\n--- MAIN SEGMENTS ---")
    for key, data in sorted(MAIN_SEGMENTS.items()):
        type_tag = data.get("type", "Mixed")
        inventory.append(
            f"- [{key}] {data['name']} ({data['duration_minutes']} min, {type_tag})"
        )

    inventory.append("\n--- REST SEGMENTS ---")
    for key, data in sorted(REST_SEGMENTS.items()):
        inventory.append(f"- [{key}] {data['name']} ({data['duration_minutes']} min)")

    inventory.append("\n--- COOLDOWN MODULES ---")
    for key, data in sorted(COOLDOWN_MODULES.items()):
        inventory.append(f"- [{key}] {data['name']} ({data['duration_minutes']} min)")

    return "\n".join(inventory)
