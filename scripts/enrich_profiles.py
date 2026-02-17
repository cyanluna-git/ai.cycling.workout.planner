#!/usr/bin/env python3
"""
Enrich Workout Profiles
Post-import script that assigns difficulty levels, adds coach_notes,
and refines "mixed" categories so profiles are fully usable by the app.
"""

import json
import sqlite3
import argparse
from pathlib import Path


# ---------------------------------------------------------------------------
# Difficulty assignment based on Intensity Factor (IF)
# ---------------------------------------------------------------------------
def assign_difficulty(estimated_if: float, estimated_tss: float, duration: int) -> str:
    """Assign difficulty from IF and TSS/hr.

    Thresholds calibrated against Zwift's own training plans:
      - beginner: easy recovery / Z1-Z2 rides
      - intermediate: tempo / sweetspot / moderate intervals
      - advanced: threshold+ / high-intensity intervals
    """
    if estimated_if is None or estimated_if == 0:
        # Fallback to TSS per hour
        if duration and duration > 0 and estimated_tss:
            tss_per_hr = estimated_tss / (duration / 60)
            if tss_per_hr < 45:
                return "beginner"
            elif tss_per_hr < 75:
                return "intermediate"
            else:
                return "advanced"
        return "intermediate"

    if estimated_if < 0.70:
        return "beginner"
    elif estimated_if < 0.85:
        return "intermediate"
    else:
        return "advanced"


# ---------------------------------------------------------------------------
# Coach notes (customisation ranges for LLM)
# ---------------------------------------------------------------------------
def generate_coach_notes(steps: list) -> dict:
    """Generate sensible coach_notes based on workout step structure."""
    has_intervals = any(s.get("type") == "intervals" for s in steps)

    notes = {
        "warmup_adjust": [-2, 5],
        "cooldown_adjust": [-2, 5],
    }

    if has_intervals:
        notes["repeat_adjust"] = [-2, 2]
        notes["power_adjust"] = [-5, 5]
    else:
        notes["repeat_adjust"] = [0, 0]
        notes["power_adjust"] = [-5, 5]

    return notes


# ---------------------------------------------------------------------------
# Category refinement for "mixed"
# ---------------------------------------------------------------------------
def refine_category(steps: list, current_category: str) -> str:
    """Re-categorize 'mixed' profiles based on step power analysis."""
    if current_category != "mixed":
        return current_category

    max_power = 0
    has_intervals = False
    interval_on_power = 0
    total_duration = 0
    weighted_power = 0

    for step in steps:
        stype = step.get("type", "")
        if stype == "intervals":
            has_intervals = True
            on_pwr = step.get("on_power", 0)
            interval_on_power = max(interval_on_power, on_pwr)
            max_power = max(max_power, on_pwr)
            dur = (step.get("on_sec", 0) + step.get("off_sec", 0)) * step.get("repeat", 1)
            total_duration += dur
            weighted_power += on_pwr * step.get("on_sec", 0) * step.get("repeat", 1)
            weighted_power += step.get("off_power", 50) * step.get("off_sec", 0) * step.get("repeat", 1)
        elif stype == "steady":
            pwr = step.get("power", 0)
            max_power = max(max_power, pwr)
            dur = step.get("duration_sec", 0)
            total_duration += dur
            weighted_power += pwr * dur
        elif stype in ("warmup", "cooldown", "ramp"):
            start = step.get("start_power", 0)
            end = step.get("end_power", 0)
            avg = (start + end) / 2
            max_power = max(max_power, max(start, end))
            dur = step.get("duration_sec", 0)
            total_duration += dur
            weighted_power += avg * dur

    avg_power = weighted_power / total_duration if total_duration > 0 else 0

    # Classification rules (same as detect_category but with weighted avg)
    if max_power > 150 or (has_intervals and interval_on_power > 150):
        return "sprint"
    elif has_intervals and interval_on_power > 110:
        return "vo2max"
    elif has_intervals and 95 <= interval_on_power <= 110:
        return "threshold"
    elif has_intervals and 88 <= interval_on_power < 95:
        return "sweetspot"
    elif avg_power >= 88:
        return "sweetspot"
    elif avg_power >= 76:
        return "tempo"
    elif avg_power >= 56:
        return "endurance"
    elif avg_power < 56:
        return "recovery"
    else:
        return "mixed"


# ---------------------------------------------------------------------------
# Target zone update (must match new category)
# ---------------------------------------------------------------------------
ZONE_MAP = {
    "recovery": "Z1",
    "endurance": "Z2",
    "tempo": "Z3",
    "sweetspot": "SST",
    "threshold": "Z4",
    "vo2max": "VO2max",
    "sprint": "anaerobic",
    "anaerobic": "anaerobic",
    "climbing": "SST",
    "race_sim": "mixed",
    "mixed": "mixed",
}


# ---------------------------------------------------------------------------
# Main enrichment
# ---------------------------------------------------------------------------
def enrich_profiles(db_path: str, dry_run: bool = False, verbose: bool = False):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM workout_profiles")
    total = cursor.fetchone()[0]
    print(f"Total profiles: {total}\n")

    # Fetch all profiles that need enrichment
    cursor.execute("""
        SELECT id, name, category, target_zone, difficulty,
               estimated_if, estimated_tss, duration_minutes,
               steps_json, coach_notes, source
        FROM workout_profiles
    """)
    rows = cursor.fetchall()

    stats = {
        "difficulty_changed": 0,
        "coach_notes_added": 0,
        "category_refined": 0,
    }

    for row in rows:
        profile = dict(row)
        pid = profile["id"]
        updates = {}

        # Parse steps
        try:
            steps_data = json.loads(profile["steps_json"]) if profile["steps_json"] else {}
            steps = steps_data.get("steps", [])
        except (json.JSONDecodeError, TypeError):
            steps = []

        # 1. Difficulty assignment
        new_diff = assign_difficulty(
            profile["estimated_if"], profile["estimated_tss"], profile["duration_minutes"]
        )
        if new_diff != profile["difficulty"]:
            updates["difficulty"] = new_diff
            stats["difficulty_changed"] += 1

        # 2. Coach notes
        if not profile["coach_notes"]:
            notes = generate_coach_notes(steps)
            updates["coach_notes"] = json.dumps(notes)
            stats["coach_notes_added"] += 1

        # 3. Category refinement ("mixed" → specific)
        new_cat = refine_category(steps, profile["category"])
        if new_cat != profile["category"]:
            updates["category"] = new_cat
            updates["target_zone"] = ZONE_MAP.get(new_cat, "mixed")
            stats["category_refined"] += 1

        # Apply updates
        if updates and not dry_run:
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            values = list(updates.values()) + [pid]
            cursor.execute(f"UPDATE workout_profiles SET {set_clause} WHERE id = ?", values)

        if verbose and updates:
            changes = ", ".join(f"{k}={v}" for k, v in updates.items() if k != "coach_notes")
            if "coach_notes" in updates:
                changes += ", +coach_notes"
            print(f"  [{pid}] {profile['name'][:50]}: {changes}")

    if not dry_run:
        conn.commit()

    conn.close()

    prefix = "[dry-run] " if dry_run else ""
    print(f"\n{prefix}Enrichment complete:")
    print(f"  Difficulty changed: {stats['difficulty_changed']}")
    print(f"  Coach notes added:  {stats['coach_notes_added']}")
    print(f"  Category refined:   {stats['category_refined']}")

    # Show new distributions
    if not dry_run:
        show_distributions(db_path)


def show_distributions(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n=== Difficulty Distribution ===")
    cursor.execute("SELECT difficulty, COUNT(*) FROM workout_profiles GROUP BY difficulty ORDER BY difficulty")
    for row in cursor.fetchall():
        print(f"  {row[0]:15s} {row[1]}")

    print("\n=== Category Distribution ===")
    cursor.execute("SELECT category, COUNT(*) FROM workout_profiles GROUP BY category ORDER BY COUNT(*) DESC")
    for row in cursor.fetchall():
        print(f"  {row[0]:15s} {row[1]}")

    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Enrich workout profiles with difficulty, coach_notes, and categories")
    parser.add_argument("--db", default="../data/workout_profiles.db", help="Database path")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    parser.add_argument("--verbose", action="store_true", help="Show each change")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    db_path = str((script_dir / args.db).resolve())

    if not Path(db_path).exists():
        print(f"Database not found: {db_path}")
        return

    enrich_profiles(db_path, dry_run=args.dry_run, verbose=args.verbose)


if __name__ == "__main__":
    main()
