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

    return {key: data for key, data in modules.items() if not is_barcode_module(data)}


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


def _load_modules(
    category: str, exclude_barcode: bool = False
) -> Dict[str, Dict[str, Any]]:
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

# Combined dictionary of all modules for easy lookup
ALL_MODULES = {**WARMUP_MODULES, **MAIN_SEGMENTS, **REST_SEGMENTS, **COOLDOWN_MODULES}


def get_module_category(module_key: str) -> str:
    """Get the category of a module (Warmup, Main, Cooldown, Rest).

    Uses the 'category' field if available, otherwise falls back to
    checking which dictionary contains the module.

    Args:
        module_key: The module key (filename without extension)

    Returns:
        Category string: 'Warmup', 'Main', 'Cooldown', 'Rest', or 'Unknown'
    """
    module_data = ALL_MODULES.get(module_key)

    if module_data:
        # Use category field if available
        if "category" in module_data:
            return module_data["category"]

        # Fallback: check which dictionary contains the module
        if module_key in WARMUP_MODULES:
            return "Warmup"
        elif module_key in COOLDOWN_MODULES:
            return "Cooldown"
        elif module_key in REST_SEGMENTS:
            return "Rest"
        elif module_key in MAIN_SEGMENTS:
            return "Main"

    return "Unknown"


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


# Mapping of workout types to suitable training styles
TYPE_TO_STYLES = {
    "VO2max": ["polarized"],  # Only for polarized high-intensity days
    "Threshold": ["norwegian", "threshold"],  # Threshold-focused plans
    "SweetSpot": ["sweetspot", "auto"],  # Sweet spot specific
    "Tempo": ["endurance", "auto"],  # Tempo for base building
    "Endurance": ["endurance", "polarized", "norwegian", "auto"],  # Versatile
    "Recovery": [
        "endurance",
        "polarized",
        "norwegian",
        "sweetspot",
        "threshold",
        "auto",
    ],
    "Mixed": ["auto"],  # Flexible
}


def get_module_inventory_text(
    exclude_barcode: bool = False, training_style: str = None
) -> str:
    """Format all modules into a text inventory for LLM prompts.

    Args:
        exclude_barcode: If True, exclude barcode-style workouts
        training_style: If provided, highlight suitable modules for this style
    """
    warmup, main, rest, cooldown = get_filtered_modules(exclude_barcode)

    inventory = []

    def _get_styles(data):
        """Get suitable styles for a module based on its type."""
        m_type = data.get("type", "Mixed")
        return TYPE_TO_STYLES.get(m_type, ["auto"])

    def _style_indicator(data, training_style):
        """Return indicator if module is suitable for current training style."""
        if not training_style or training_style == "auto":
            return ""
        suitable = _get_styles(data)
        if training_style in suitable:
            return " ⭐"  # Star for recommended
        return ""

    def _get_length_category(duration_minutes: int) -> str:
        """Categorize module by length."""
        if duration_minutes < 15:
            return "SHORT"
        elif duration_minutes < 45:
            return "MID"
        elif duration_minutes < 75:
            return "LONG"
        else:
            return "VERYLONG"

    def _fmt(key, data, training_style=None):
        # Format: [key] Dur: 10m (SHORT) | TSS: 12 | IF: 0.85 | Type: Threshold | Styles: [list] | Desc: Name
        dur_min = data["duration_minutes"]
        dur = f"{dur_min}m"
        length_cat = _get_length_category(dur_min)
        tss = data.get("estimated_tss", "?")
        if_val = data.get("estimated_if", "?")
        m_type = data.get("type", "?")
        styles = _get_styles(data)
        name = data["name"]
        star = _style_indicator(data, training_style)

        return f"- [{key}]{star} {length_cat} {dur} | TSS: {tss} | IF: {if_val} | Type: {m_type} | For: {','.join(styles)} | {name}"

    inventory.append("--- WARMUP MODULES ---")
    for key, data in sorted(warmup.items()):
        inventory.append(_fmt(key, data, training_style))

    # Group main segments by type for better organization
    inventory.append("\n--- MAIN SEGMENTS (organized by type and length) ---")
    inventory.append(
        "Length categories: SHORT (<15min) | MID (15-45min) | LONG (45-75min) | VERYLONG (75min+)"
    )
    inventory.append(
        "For workouts 120min+, combine multiple LONG/VERYLONG Endurance modules\n"
    )

    # Group by type
    types_order = ["Endurance", "Tempo", "SweetSpot", "Threshold", "VO2max", "Mixed"]
    type_groups = {t: [] for t in types_order}

    for key, data in sorted(main.items()):
        m_type = data.get("type", "Mixed")
        if m_type in type_groups:
            type_groups[m_type].append((key, data))
        else:
            type_groups["Mixed"].append((key, data))

    for m_type in types_order:
        if type_groups[m_type]:
            styles_for_type = TYPE_TO_STYLES.get(m_type, ["auto"])
            inventory.append(
                f"\n## {m_type} modules (suitable for: {', '.join(styles_for_type)})"
            )
            for key, data in type_groups[m_type]:
                inventory.append(_fmt(key, data, training_style))

    inventory.append("\n--- REST SEGMENTS ---")
    for key, data in sorted(rest.items()):
        inventory.append(f"- [{key}] Dur: {data['duration_minutes']}m | Recovery")

    inventory.append("\n--- COOLDOWN MODULES ---")
    for key, data in sorted(cooldown.items()):
        inventory.append(_fmt(key, data, training_style))

    return "\n".join(inventory)
