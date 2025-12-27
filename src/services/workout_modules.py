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


def _enrich_metadata(data: dict, category: str):
    """Calculate and inject metadata if missing."""
    if "estimated_tss" in data and "estimated_if" in data and "fatigue_impact" in data:
        return

    duration = data.get("duration_minutes", 10)
    m_type = data.get("type", "Mixed")
    name = data.get("name", "").lower()

    # Defaults
    if_score = 0.65
    fatigue = "Low"

    if category == "rest":
        if_score = 0.4
        fatigue = "Recovery"
    elif category == "warmup" or category == "cooldown":
        if_score = 0.55
        fatigue = "Low"
    else:  # main
        if m_type == "VO2max":
            if_score = 0.95
            fatigue = "High" if duration < 15 else "Very High"
        elif m_type == "Threshold":
            if_score = 0.95
            fatigue = "High"
        elif m_type == "SweetSpot":
            if_score = 0.90
            fatigue = "Medium"
        elif m_type == "Endurance":
            if_score = 0.70
            fatigue = "Low"
        elif m_type == "Mixed":
            if_score = 0.85
            fatigue = "Medium"

    # Refine for specific hard known modules
    if "micro" in name or "burst" in name:
        if_score = 1.0
    if "mesoburst" in name:
        fatigue = "Very High"

    tss = int((duration / 60) * (if_score**2) * 100)

    # Inject missing values
    if "estimated_tss" not in data:
        data["estimated_tss"] = tss
    if "estimated_if" not in data:
        data["estimated_if"] = if_score
    if "fatigue_impact" not in data:
        data["fatigue_impact"] = fatigue


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
                # Auto-calculate metadata if missing
                _enrich_metadata(data, category)

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

    def _fmt(key, data):
        # Format: [key] Dur: 10m | TSS: 12 | IF: 0.85 | Fatigue: Med | Desc: Name
        dur = f"{data['duration_minutes']}m"
        tss = data.get("estimated_tss", "?")
        if_val = data.get("estimated_if", "?")
        fatigue = data.get("fatigue_impact", "?")
        name = data["name"]
        return f"- [{key}] Dur: {dur} | TSS: {tss} | IF: {if_val} | Fatigue: {fatigue} | Desc: {name}"

    inventory.append("--- WARMUP MODULES ---")
    for key, data in sorted(WARMUP_MODULES.items()):
        inventory.append(_fmt(key, data))

    inventory.append("\n--- MAIN SEGMENTS ---")
    for key, data in sorted(MAIN_SEGMENTS.items()):
        # Group by Intensity for better AI readability? Or just sorted name.
        # Sorted by key is fine.
        inventory.append(_fmt(key, data))

    inventory.append("\n--- REST SEGMENTS ---")
    for key, data in sorted(REST_SEGMENTS.items()):
        inventory.append(
            f"- [{key}] Dur: {data['duration_minutes']}m | Fatigue: Recovery | Desc: {data['name']}"
        )

    inventory.append("\n--- COOLDOWN MODULES ---")
    for key, data in sorted(COOLDOWN_MODULES.items()):
        inventory.append(_fmt(key, data))

    return "\n".join(inventory)
