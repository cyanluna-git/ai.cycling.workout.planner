#!/usr/bin/env python3
"""
Repair Sufferfest Profiles
Re-parse zwo_xml for affected profiles (IDs 106-118, 122) that had all steps
at 100% FTP due to SteadyState parsing bug (missing PowerHigh/PowerLow fallback).
"""

import sqlite3
import json
import xml.etree.ElementTree as ET
from pathlib import Path
import sys

# Add project root to path so we can import from scripts/
sys.path.insert(0, str(Path(__file__).parent))
from import_zwo import (
    parse_zwo_element,
    calculate_normalized_power,
    detect_category,
    detect_target_zone,
)

AFFECTED_IDS = list(range(106, 119)) + [122]  # 106-118, 122
DB_PATH = Path(__file__).parent / '../data/workout_profiles.db'


def repair_profile(cursor, profile_id):
    """Re-parse zwo_xml and update steps_json + derived fields for a single profile."""
    cursor.execute(
        'SELECT name, zwo_xml, tags FROM workout_profiles WHERE id = ?',
        (profile_id,)
    )
    row = cursor.fetchone()
    if not row:
        print(f"  SKIP id={profile_id}: not found")
        return False

    name, zwo_xml, tags_json = row
    if not zwo_xml:
        print(f"  SKIP id={profile_id} ({name}): no zwo_xml")
        return False

    # Parse tags
    try:
        tags = json.loads(tags_json) if tags_json else []
    except json.JSONDecodeError:
        tags = []

    # Re-parse the ZWO XML with the fixed parser
    root = ET.fromstring(zwo_xml)
    workout_elem = root.find('workout')
    if workout_elem is None:
        print(f"  SKIP id={profile_id} ({name}): no <workout> element")
        return False

    steps = []
    for elem in workout_elem:
        step = parse_zwo_element(elem)
        if step:
            steps.append(step)

    if not steps:
        print(f"  SKIP id={profile_id} ({name}): no steps parsed")
        return False

    # Recalculate derived fields
    tss, if_value = calculate_normalized_power(steps)
    category = detect_category(steps, tags)
    target_zone = detect_target_zone(category, steps)

    # Determine fatigue impact from TSS
    if tss < 50:
        fatigue_impact = 'low'
    elif tss < 100:
        fatigue_impact = 'moderate'
    elif tss < 150:
        fatigue_impact = 'high'
    else:
        fatigue_impact = 'very_high'

    # Update the database
    cursor.execute('''
        UPDATE workout_profiles SET
            steps_json = ?,
            estimated_tss = ?,
            estimated_if = ?,
            fatigue_impact = ?,
            category = ?,
            target_zone = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (
        json.dumps({'steps': steps}),
        tss,
        if_value,
        fatigue_impact,
        category,
        target_zone,
        profile_id,
    ))

    print(f"  FIXED id={profile_id} ({name})")
    print(f"    IF: 1.0 -> {if_value} | TSS: -> {tss} | cat: {category} | fatigue: {fatigue_impact}")
    return True


def main():
    db_path = DB_PATH.resolve()
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return

    print(f"Repairing {len(AFFECTED_IDS)} profiles in {db_path}")
    print(f"Affected IDs: {AFFECTED_IDS}\n")

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    fixed = 0
    for pid in AFFECTED_IDS:
        if repair_profile(cursor, pid):
            fixed += 1

    conn.commit()
    conn.close()

    print(f"\nRepaired {fixed}/{len(AFFECTED_IDS)} profiles.")


if __name__ == '__main__':
    main()
