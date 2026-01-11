#!/usr/bin/env python3
"""Script to standardize workout module JSON files.

Ensures all module files have consistent structure:
- category: Folder category (Warmup, Main, Cooldown, Rest)
- type: Workout type (for Main: VO2max, Threshold, etc. For others: same as category)
- name: Module name
- duration_minutes: Total duration
- description: (added if missing)
- structure: Array of workout blocks
"""

import os
import json
from pathlib import Path

# Base directory for workout modules
MODULES_DIR = Path(__file__).parent.parent / "src" / "data" / "workout_modules"

# Category type mapping based on folder
FOLDER_TO_TYPE = {
    "warmup": "Warmup",
    "cooldown": "Cooldown",
    "main": "Main",
    "rest": "Rest",
}


def standardize_module(file_path: Path, category_type: str) -> tuple:
    """Standardize a single module file.

    Args:
        file_path: Path to the JSON file
        category_type: The category (Warmup, Main, Cooldown, Rest)

    Returns:
        Tuple of (modified JSON data, list of changes made)
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    changes = []

    # Add category field (folder-based)
    if data.get("category") != category_type:
        data["category"] = category_type
        changes.append(f"category: {category_type}")

    # Handle type field based on category
    current_type = data.get("type")

    if category_type != "Main":
        # Warmup, Cooldown, Rest: type should match category
        if current_type not in ["Warmup", "Cooldown", "Rest"]:
            data["type"] = category_type
            changes.append(f"type: {current_type} → {category_type}")
    else:
        # Main modules: preserve workout type (VO2max, Threshold, etc.)
        # Only infer if missing or invalid
        valid_main_types = [
            "VO2max",
            "Threshold",
            "SweetSpot",
            "Tempo",
            "Endurance",
            "Recovery",
            "Mixed",
            "Anaerobic",
        ]
        if current_type not in valid_main_types:
            # Try to infer from filename
            filename = file_path.stem.lower()
            if "vo2" in filename:
                data["type"] = "VO2max"
            elif "threshold" in filename:
                data["type"] = "Threshold"
            elif "sst" in filename or "sweetspot" in filename:
                data["type"] = "SweetSpot"
            elif "tempo" in filename:
                data["type"] = "Tempo"
            elif "endurance" in filename or "fatmax" in filename:
                data["type"] = "Endurance"
            elif "recovery" in filename:
                data["type"] = "Recovery"
            elif "sprint" in filename:
                data["type"] = "Anaerobic"
            else:
                data["type"] = "Mixed"
            changes.append(f"type inferred: {data['type']}")

    # Ensure name exists
    if "name" not in data:
        name = file_path.stem.replace("_", " ").title()
        data["name"] = name
        changes.append(f"Added name: {name}")

    # Ensure duration_minutes exists
    if "duration_minutes" not in data:
        total_duration = sum(
            block.get("duration_minutes", 0) for block in data.get("structure", [])
        )
        if total_duration > 0:
            data["duration_minutes"] = total_duration
            changes.append(f"Added duration: {total_duration}min")

    # Ensure description exists
    if "description" not in data:
        data["description"] = (
            f"{category_type} module: {data.get('name', file_path.stem)}"
        )
        changes.append("Added description")

    # Reorder keys for consistency
    key_order = [
        "name",
        "duration_minutes",
        "category",
        "type",
        "description",
        "structure",
    ]
    ordered_data = {}
    for key in key_order:
        if key in data:
            ordered_data[key] = data[key]
    for key, value in data.items():
        if key not in ordered_data:
            ordered_data[key] = value

    return ordered_data, changes


def process_all_modules():
    """Process all module files in all categories."""
    stats = {"processed": 0, "modified": 0, "errors": []}

    for folder_name, category_type in FOLDER_TO_TYPE.items():
        folder_path = MODULES_DIR / folder_name
        if not folder_path.exists():
            print(f"⚠️  Folder not found: {folder_path}")
            continue

        print(f"\n{'='*60}")
        print(f"Processing {folder_name}/ → category: {category_type}")
        print(f"{'='*60}")

        for json_file in sorted(folder_path.glob("*.json")):
            try:
                new_data, changes = standardize_module(json_file, category_type)

                if changes:
                    with open(json_file, "w", encoding="utf-8") as f:
                        json.dump(new_data, f, indent=2, ensure_ascii=False)
                        f.write("\n")

                    print(f"✅ {json_file.name}: {', '.join(changes)}")
                    stats["modified"] += 1
                else:
                    print(f"○  {json_file.name}: No changes needed")

                stats["processed"] += 1

            except Exception as e:
                print(f"❌ {json_file.name}: Error - {e}")
                stats["errors"].append(str(json_file.name))

    print(f"\n{'='*60}")
    print(
        f"Summary: {stats['processed']} processed, {stats['modified']} modified, {len(stats['errors'])} errors"
    )


if __name__ == "__main__":
    process_all_modules()
