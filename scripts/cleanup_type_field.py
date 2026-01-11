#!/usr/bin/env python3
"""Script to clean up redundant type field from warmup/cooldown/rest modules.

For Main modules: keep both category and type (type = workout type like Threshold)
For Warmup/Cooldown/Rest: keep only category, remove type (redundant)
"""

import json
from pathlib import Path

MODULES_DIR = Path(__file__).parent.parent / "src" / "data" / "workout_modules"


def cleanup_module(file_path: Path, category: str) -> bool:
    """Remove redundant type field if it matches category.

    Returns True if file was modified.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Only remove type if it matches category (redundant)
    if category != "Main" and data.get("type") == category:
        del data["type"]

        # Reorder keys
        key_order = ["name", "duration_minutes", "category", "description", "structure"]
        ordered_data = {}
        for key in key_order:
            if key in data:
                ordered_data[key] = data[key]
        for key, value in data.items():
            if key not in ordered_data:
                ordered_data[key] = value

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(ordered_data, f, indent=2, ensure_ascii=False)
            f.write("\n")

        return True

    return False


def main():
    categories = {"warmup": "Warmup", "cooldown": "Cooldown", "rest": "Rest"}

    modified = 0
    for folder, category in categories.items():
        folder_path = MODULES_DIR / folder
        if not folder_path.exists():
            continue

        for json_file in folder_path.glob("*.json"):
            if cleanup_module(json_file, category):
                print(f"✅ Removed type from: {json_file.name}")
                modified += 1

    print(f"\n{modified} files cleaned up")


if __name__ == "__main__":
    main()
