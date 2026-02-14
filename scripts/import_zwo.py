#!/usr/bin/env python3
"""
ZWO Import Utility
Import Zwift workout files (.zwo) into the workout profiles database
"""

import sqlite3
import json
import xml.etree.ElementTree as ET
import argparse
import math
from pathlib import Path
from datetime import datetime


def parse_zwo_file(zwo_path):
    """
    Parse a ZWO (Zwift Workout) XML file
    Returns: dict with workout metadata and steps
    """
    tree = ET.parse(zwo_path)
    root = tree.getroot()
    
    # Extract metadata
    name = root.find('name').text if root.find('name') is not None else Path(zwo_path).stem
    description = root.find('description').text if root.find('description') is not None else ''
    author = root.find('author').text if root.find('author') is not None else ''
    tags_elem = root.find('tags')
    tags = [tag.get('name') for tag in tags_elem.findall('tag')] if tags_elem is not None else []
    
    # Parse workout steps
    workout = root.find('workout')
    steps = []
    
    if workout is not None:
        for elem in workout:
            step = parse_zwo_element(elem)
            if step:
                steps.append(step)
    
    return {
        'name': name,
        'description': description,
        'author': author,
        'tags': tags,
        'steps': steps,
        'zwo_xml': ET.tostring(root, encoding='unicode')
    }


def parse_zwo_element(elem):
    """
    Parse a single ZWO workout element
    """
    tag = elem.tag.lower()
    
    if tag == 'warmup':
        return {
            'type': 'warmup',
            'start_power': int(float(elem.get('PowerLow', '0.5')) * 100),
            'end_power': int(float(elem.get('PowerHigh', '0.75')) * 100),
            'duration_sec': int(elem.get('Duration', '600'))
        }
    
    elif tag == 'cooldown':
        return {
            'type': 'cooldown',
            'start_power': int(float(elem.get('PowerLow', '0.65')) * 100),
            'end_power': int(float(elem.get('PowerHigh', '0.4')) * 100),
            'duration_sec': int(elem.get('Duration', '300'))
        }
    
    elif tag == 'steadystate':
        return {
            'type': 'steady',
            'power': int(float(elem.get('Power', '1.0')) * 100),
            'duration_sec': int(elem.get('Duration', '300'))
        }
    
    elif tag == 'ramp':
        return {
            'type': 'ramp',
            'start_power': int(float(elem.get('PowerLow', '0.85')) * 100),
            'end_power': int(float(elem.get('PowerHigh', '0.95')) * 100),
            'duration_sec': int(elem.get('Duration', '600'))
        }
    
    elif tag == 'intervalst':
        # Zwift intervals
        repeat = int(elem.get('Repeat', '1'))
        on_duration = int(elem.get('OnDuration', '60'))
        off_duration = int(elem.get('OffDuration', '60'))
        on_power = int(float(elem.get('OnPower', '1.05')) * 100)
        off_power = int(float(elem.get('OffPower', '0.55')) * 100)
        
        return {
            'type': 'intervals',
            'on_power': on_power,
            'off_power': off_power,
            'on_sec': on_duration,
            'off_sec': off_duration,
            'repeat': repeat
        }
    
    elif tag == 'freeride':
        return {
            'type': 'steady',
            'power': 60,
            'duration_sec': int(elem.get('Duration', '300'))
        }
    
    return None


def calculate_normalized_power(steps):
    """
    Calculate normalized power from workout steps
    """
    total_time = 0
    weighted_sum = 0
    
    for step in steps:
        if step['type'] in ['warmup', 'ramp', 'cooldown']:
            avg_power = (step['start_power'] + step['end_power']) / 2
            duration = step['duration_sec']
            weighted_sum += (avg_power ** 4) * duration
            total_time += duration
        elif step['type'] == 'steady':
            power = step['power']
            duration = step['duration_sec']
            weighted_sum += (power ** 4) * duration
            total_time += duration
        elif step['type'] == 'intervals':
            on_power = step['on_power']
            off_power = step['off_power']
            on_sec = step['on_sec']
            off_sec = step['off_sec']
            repeat = step['repeat']
            
            for _ in range(repeat):
                weighted_sum += (on_power ** 4) * on_sec
                weighted_sum += (off_power ** 4) * off_sec
                total_time += on_sec + off_sec
    
    if total_time == 0:
        return 0, 0
    
    np = (weighted_sum / total_time) ** 0.25
    intensity_factor = np / 100
    tss = (total_time * (intensity_factor ** 2) * 100) / 3600
    
    return round(tss, 1), round(intensity_factor, 2)


def detect_category(steps, tags):
    """
    Auto-detect workout category from steps and tags
    """
    # Analyze power zones
    max_power = 0
    avg_power = 0
    has_intervals = False
    
    for step in steps:
        if step['type'] == 'intervals':
            has_intervals = True
            max_power = max(max_power, step['on_power'])
        elif step['type'] == 'steady':
            max_power = max(max_power, step['power'])
            avg_power += step['power']
        elif step['type'] in ['warmup', 'ramp', 'cooldown']:
            max_power = max(max_power, step.get('end_power', 0))
    
    # Check tags
    tag_str = ' '.join(tags).lower()
    
    if 'recovery' in tag_str or max_power < 60:
        return 'recovery'
    elif 'sprint' in tag_str or 'neuromuscular' in tag_str or max_power > 150:
        return 'sprint'
    elif 'vo2max' in tag_str or (has_intervals and max_power > 110):
        return 'vo2max'
    elif 'threshold' in tag_str or 'ftp' in tag_str or (95 <= max_power <= 105):
        return 'threshold'
    elif 'sweetspot' in tag_str or 'sst' in tag_str or (88 <= max_power <= 94):
        return 'sweetspot'
    elif 'tempo' in tag_str or (76 <= max_power <= 87):
        return 'tempo'
    elif 'endurance' in tag_str or max_power < 75:
        return 'endurance'
    elif 'climbing' in tag_str or 'climb' in tag_str:
        return 'climbing'
    elif 'race' in tag_str or 'crit' in tag_str:
        return 'race_sim'
    else:
        return 'mixed'


def detect_target_zone(category, steps):
    """
    Detect target training zone
    """
    zone_map = {
        'recovery': 'Z1',
        'endurance': 'Z2',
        'tempo': 'Z3',
        'sweetspot': 'SST',
        'threshold': 'Z4',
        'vo2max': 'VO2max',
        'sprint': 'anaerobic',
        'anaerobic': 'anaerobic',
        'climbing': 'SST',
        'race_sim': 'mixed',
        'mixed': 'mixed'
    }
    return zone_map.get(category, 'mixed')


def calculate_duration(steps):
    """
    Calculate total workout duration in minutes
    """
    total_sec = 0
    for step in steps:
        if step['type'] == 'intervals':
            total_sec += (step['on_sec'] + step['off_sec']) * step['repeat']
        else:
            total_sec += step.get('duration_sec', 0)
    return int(total_sec / 60)


def import_zwo_to_db(zwo_path, db_path, category=None, difficulty='intermediate'):
    """
    Import a ZWO file into the database
    """
    # Parse ZWO file
    workout = parse_zwo_file(zwo_path)
    
    # Auto-detect category if not provided
    if category is None:
        category = detect_category(workout['steps'], workout['tags'])
    
    target_zone = detect_target_zone(category, workout['steps'])
    duration_minutes = calculate_duration(workout['steps'])
    tss, if_value = calculate_normalized_power(workout['steps'])
    
    # Determine fatigue impact from TSS
    if tss < 50:
        fatigue_impact = 'low'
    elif tss < 100:
        fatigue_impact = 'moderate'
    elif tss < 150:
        fatigue_impact = 'high'
    else:
        fatigue_impact = 'very_high'
    
    # Create slug
    slug = workout['name'].lower().replace(' ', '-').replace('×', 'x')
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if already exists
    cursor.execute('SELECT id FROM workout_profiles WHERE slug = ?', (slug,))
    existing = cursor.fetchone()
    
    if existing:
        print(f"⚠️  Workout '{workout['name']}' already exists (slug: {slug})")
        conn.close()
        return False
    
    # Insert into database
    cursor.execute('''
        INSERT INTO workout_profiles (
            name, slug, category, tags, target_zone,
            duration_minutes, estimated_tss, estimated_if,
            fatigue_impact, difficulty, steps_json, zwo_xml,
            source, description, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        workout['name'],
        slug,
        category,
        json.dumps(workout['tags']),
        target_zone,
        duration_minutes,
        tss,
        if_value,
        fatigue_impact,
        difficulty,
        json.dumps({'steps': workout['steps']}),
        workout['zwo_xml'],
        'zwift',
        workout['description'],
        1
    ))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Imported: {workout['name']}")
    print(f"   Category: {category} | Zone: {target_zone} | Duration: {duration_minutes}min")
    print(f"   TSS: {tss} | IF: {if_value} | Fatigue: {fatigue_impact}")
    return True


def main():
    parser = argparse.ArgumentParser(description='Import Zwift workout files (.zwo) into database')
    parser.add_argument('zwo_file', help='Path to .zwo file or directory containing .zwo files')
    parser.add_argument('--db', default='../data/workout_profiles.db', help='Database path')
    parser.add_argument('--category', help='Override category detection')
    parser.add_argument('--difficulty', default='intermediate', choices=['beginner', 'intermediate', 'advanced'],
                       help='Workout difficulty level')
    
    args = parser.parse_args()
    
    # Resolve paths
    script_dir = Path(__file__).parent
    db_path = (script_dir / args.db).resolve()
    zwo_path = Path(args.zwo_file)
    
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        print("   Run seed_profiles.py first to create the database.")
        return
    
    # Import single file or directory
    if zwo_path.is_file():
        if zwo_path.suffix.lower() == '.zwo':
            import_zwo_to_db(zwo_path, db_path, args.category, args.difficulty)
        else:
            print(f"❌ Not a .zwo file: {zwo_path}")
    elif zwo_path.is_dir():
        zwo_files = list(zwo_path.glob('*.zwo')) + list(zwo_path.glob('**/*.zwo'))
        if not zwo_files:
            print(f"❌ No .zwo files found in: {zwo_path}")
            return
        
        print(f"Found {len(zwo_files)} .zwo files\n")
        success_count = 0
        for zwo_file in zwo_files:
            if import_zwo_to_db(zwo_file, db_path, args.category, args.difficulty):
                success_count += 1
            print()
        
        print(f"\n✅ Imported {success_count}/{len(zwo_files)} workouts")
    else:
        print(f"❌ Path not found: {zwo_path}")


if __name__ == '__main__':
    main()
