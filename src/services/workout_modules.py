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


def is_barcode_module(module_data: dict) -> bool:
    """Detect if a module is a barcode-style workout.

    Checks:
    1. Module structure contains block with {"type": "barcode"}
    2. Module key/name contains "micro" or "burst"

    Args:
        module_data: Module dictionary from JSON

    Returns:
        True if module is barcode-style
    """
    # Check structure for barcode blocks
    structure = module_data.get("structure", [])
    for block in structure:
        if block.get("type") == "barcode":
            return True

    # Check name for barcode indicators
    name = module_data.get("name", "").lower()
    if "micro" in name or "burst" in name:
        return True

    return False


def filter_barcode_modules(modules: dict, exclude_barcode: bool) -> dict:
    """Filter out barcode workouts if user preference is set.

    Args:
        modules: Dictionary of module_key -> module_data
        exclude_barcode: If True, remove barcode modules

    Returns:
        Filtered dictionary of modules
    """
    if not exclude_barcode:
        return modules

    return {
        key: data
        for key, data in modules.items()
        if not is_barcode_module(data)
    }


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


def _load_modules(category: str, exclude_barcode: bool = False) -> Dict[str, Dict[str, Any]]:
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

    # Apply barcode filter if needed
    return filter_barcode_modules(modules, exclude_barcode)


# Load dictionaries on module import
WARMUP_MODULES = _load_modules("warmup")
MAIN_SEGMENTS = _load_modules("main")
REST_SEGMENTS = _load_modules("rest")
COOLDOWN_MODULES = _load_modules("cooldown")


def get_filtered_modules(exclude_barcode: bool = False) -> tuple:
    """Get all modules with optional barcode filtering.

    Returns:
        Tuple of (warmup, main, rest, cooldown) module dictionaries
    """
    warmup = _load_modules("warmup", exclude_barcode)
    main = _load_modules("main", exclude_barcode)
    rest = _load_modules("rest", exclude_barcode)
    cooldown = _load_modules("cooldown", exclude_barcode)

    return warmup, main, rest, cooldown


def get_module_inventory_text(exclude_barcode: bool = False) -> str:
    """Format all modules into a text inventory for LLM prompts."""
    warmup, main, rest, cooldown = get_filtered_modules(exclude_barcode)

    inventory = []

    def _fmt(key, data):
        # Format: [key] Dur: 10m | TSS: 12 | IF: 0.85 | Fatigue: Med | Desc: Name - Description
        dur = f"{data['duration_minutes']}m"
        tss = data.get("estimated_tss", "?")
        if_val = data.get("estimated_if", "?")
        fatigue = data.get("fatigue_impact", "?")
        name = data["name"]
        desc = data.get("description", "")
        if desc:
            return f"- [{key}] Dur: {dur} | TSS: {tss} | IF: {if_val} | Fatigue: {fatigue} | Desc: {name} - {desc}"
        return f"- [{key}] Dur: {dur} | TSS: {tss} | IF: {if_val} | Fatigue: {fatigue} | Desc: {name}"

    inventory.append("--- WARMUP MODULES ---")
    for key, data in sorted(warmup.items()):
        inventory.append(_fmt(key, data))

    inventory.append("\n--- MAIN SEGMENTS ---")
    for key, data in sorted(main.items()):
        # Group by Intensity for better AI readability? Or just sorted name.
        # Sorted by key is fine.
        inventory.append(_fmt(key, data))

    inventory.append("\n--- REST SEGMENTS ---")
    for key, data in sorted(rest.items()):
        inventory.append(
            f"- [{key}] Dur: {data['duration_minutes']}m | Fatigue: Recovery | Desc: {data['name']}"
        )

    inventory.append("\n--- COOLDOWN MODULES ---")
    for key, data in sorted(cooldown.items()):
        inventory.append(_fmt(key, data))

    return "\n".join(inventory)
