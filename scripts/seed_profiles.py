#!/usr/bin/env python3
"""
Workout Profile DB Seed Script
Generates 100 realistic cycling workout profiles
"""

import sqlite3
import json
import math
from datetime import datetime
from pathlib import Path


def calculate_normalized_power(steps):
    """Calculate normalized power from workout steps (simplified)"""
    total_time = 0
    weighted_sum = 0
    
    for step in steps:
        if step['type'] == 'warmup' or step['type'] == 'ramp':
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
        elif step['type'] == 'cooldown':
            avg_power = (step['start_power'] + step['end_power']) / 2
            duration = step['duration_sec']
            weighted_sum += (avg_power ** 4) * duration
            total_time += duration
    
    if total_time == 0:
        return 0
    
    np = (weighted_sum / total_time) ** 0.25
    return np


def calculate_tss_if(steps):
    """Calculate TSS and IF from workout steps"""
    np = calculate_normalized_power(steps)
    total_duration = sum(
        step.get('duration_sec', 0) if step['type'] != 'intervals' 
        else (step['on_sec'] + step['off_sec']) * step['repeat']
        for step in steps
    )
    
    intensity_factor = np / 100  # NP as % of FTP
    tss = (total_duration * (intensity_factor ** 2) * 100) / 3600
    
    return round(tss, 1), round(intensity_factor, 2)


def slugify(text):
    """Convert text to slug"""
    return text.lower().replace(' ', '-').replace('×', 'x').replace('/', '-').replace('—', '-').replace('@', 'at')


def create_schema(conn):
    """Create database schema"""
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workout_profiles (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT,
            tags TEXT,
            target_zone TEXT NOT NULL,
            interval_type TEXT,
            interval_length TEXT,
            duration_minutes INTEGER NOT NULL,
            estimated_tss REAL,
            estimated_if REAL,
            fatigue_impact TEXT,
            difficulty TEXT DEFAULT 'intermediate',
            min_ftp INTEGER,
            zwo_xml TEXT,
            steps_json TEXT NOT NULL,
            source TEXT,
            source_url TEXT,
            description TEXT,
            coach_notes TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_profiles_category ON workout_profiles(category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_profiles_zone ON workout_profiles(target_zone)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_profiles_duration ON workout_profiles(duration_minutes)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_profiles_difficulty ON workout_profiles(difficulty)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_profiles_tss ON workout_profiles(estimated_tss)')
    
    conn.commit()


def insert_profile(conn, profile):
    """Insert a workout profile"""
    cursor = conn.cursor()
    
    steps = profile['steps']
    tss, if_value = calculate_tss_if(steps)
    
    cursor.execute('''
        INSERT INTO workout_profiles (
            name, slug, category, subcategory, tags, target_zone,
            interval_type, interval_length, duration_minutes,
            estimated_tss, estimated_if, fatigue_impact, difficulty,
            min_ftp, steps_json, source, description, coach_notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        profile['name'],
        slugify(profile['name']),
        profile['category'],
        profile.get('subcategory'),
        json.dumps(profile.get('tags', [])),
        profile['target_zone'],
        profile.get('interval_type'),
        profile.get('interval_length'),
        profile['duration_minutes'],
        tss,
        if_value,
        profile['fatigue_impact'],
        profile['difficulty'],
        profile.get('min_ftp'),
        json.dumps({'steps': steps}),
        profile.get('source', 'custom'),
        profile.get('description'),
        json.dumps(profile.get('coach_notes', {}))
    ))
    
    conn.commit()


def get_profiles():
    """Return all 100 workout profiles"""
    profiles = []
    
    # VO2max Intervals (12)
    profiles.append({
        'name': 'Micro Burst 30/30s ×10',
        'category': 'vo2max',
        'subcategory': 'micro_intervals',
        'tags': ['vo2max', 'microburst', 'short'],
        'target_zone': 'VO2max',
        'interval_type': 'intervals',
        'interval_length': '30s',
        'duration_minutes': 30,
        'fatigue_impact': 'high',
        'difficulty': 'advanced',
        'min_ftp': 200,
        'description': '10 rounds of 30-second VO2max efforts with 30-second recovery. Perfect for developing anaerobic capacity and neuromuscular power.',
        'coach_notes': {'repeat_adjust': [-2, 2], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 600},
            {'type': 'intervals', 'on_power': 120, 'off_power': 50, 'on_sec': 30, 'off_sec': 30, 'repeat': 10},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 300}
        ]
    })
    
    profiles.append({
        'name': 'Micro Burst 30/30s ×15',
        'category': 'vo2max',
        'subcategory': 'micro_intervals',
        'tags': ['vo2max', 'microburst', 'extended'],
        'target_zone': 'VO2max',
        'interval_type': 'intervals',
        'interval_length': '30s',
        'duration_minutes': 40,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 220,
        'description': 'Extended microburst session with 15 rounds. High neuromuscular demand.',
        'coach_notes': {'repeat_adjust': [-3, 2], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 720},
            {'type': 'intervals', 'on_power': 120, 'off_power': 50, 'on_sec': 30, 'off_sec': 30, 'repeat': 15},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'Ronnestad 30/15s ×3sets',
        'category': 'vo2max',
        'subcategory': 'ronnestad',
        'tags': ['vo2max', 'ronnestad', 'research_based'],
        'target_zone': 'VO2max',
        'interval_type': 'intervals',
        'interval_length': '30s',
        'duration_minutes': 45,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 230,
        'description': 'Research-backed Ronnestad intervals: 30s max / 15s easy, repeated in 3 sets. Extremely effective for VO2max gains.',
        'coach_notes': {'repeat_adjust': [-1, 1], 'power_adjust': [0, 0], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 720},
            {'type': 'intervals', 'on_power': 125, 'off_power': 50, 'on_sec': 30, 'off_sec': 15, 'repeat': 13},
            {'type': 'steady', 'power': 55, 'duration_sec': 300},
            {'type': 'intervals', 'on_power': 125, 'off_power': 50, 'on_sec': 30, 'off_sec': 15, 'repeat': 13},
            {'type': 'steady', 'power': 55, 'duration_sec': 300},
            {'type': 'intervals', 'on_power': 125, 'off_power': 50, 'on_sec': 30, 'off_sec': 15, 'repeat': 13},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 420}
        ]
    })
    
    profiles.append({
        'name': 'Billat 30/30s ×3sets',
        'category': 'vo2max',
        'subcategory': 'billat',
        'tags': ['vo2max', 'billat', 'classic'],
        'target_zone': 'VO2max',
        'interval_type': 'intervals',
        'interval_length': '30s',
        'duration_minutes': 50,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 220,
        'description': 'Classic Billat 30/30 protocol: 3 sets of sustained VO2max work. High time at VO2max.',
        'coach_notes': {'repeat_adjust': [-1, 1], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 720},
            {'type': 'intervals', 'on_power': 120, 'off_power': 55, 'on_sec': 30, 'off_sec': 30, 'repeat': 12},
            {'type': 'steady', 'power': 55, 'duration_sec': 360},
            {'type': 'intervals', 'on_power': 120, 'off_power': 55, 'on_sec': 30, 'off_sec': 30, 'repeat': 12},
            {'type': 'steady', 'power': 55, 'duration_sec': 360},
            {'type': 'intervals', 'on_power': 120, 'off_power': 55, 'on_sec': 30, 'off_sec': 30, 'repeat': 12},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'VO2max 1min ×5',
        'category': 'vo2max',
        'subcategory': 'classic',
        'tags': ['vo2max', '1min', 'moderate_volume'],
        'target_zone': 'VO2max',
        'interval_type': 'intervals',
        'interval_length': '1min',
        'duration_minutes': 40,
        'fatigue_impact': 'high',
        'difficulty': 'intermediate',
        'min_ftp': 200,
        'description': '5×1min VO2max efforts with full recovery. Great for building aerobic power without excessive fatigue.',
        'coach_notes': {'repeat_adjust': [-1, 3], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 720},
            {'type': 'intervals', 'on_power': 118, 'off_power': 55, 'on_sec': 60, 'off_sec': 240, 'repeat': 5},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'VO2max 1min ×8',
        'category': 'vo2max',
        'subcategory': 'classic',
        'tags': ['vo2max', '1min', 'high_volume'],
        'target_zone': 'VO2max',
        'interval_type': 'intervals',
        'interval_length': '1min',
        'duration_minutes': 50,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 220,
        'description': '8×1min VO2max efforts. High volume session for experienced athletes.',
        'coach_notes': {'repeat_adjust': [-2, 2], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 720},
            {'type': 'intervals', 'on_power': 118, 'off_power': 55, 'on_sec': 60, 'off_sec': 240, 'repeat': 8},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'VO2max 2min ×5',
        'category': 'vo2max',
        'subcategory': 'classic',
        'tags': ['vo2max', '2min', 'moderate_volume'],
        'target_zone': 'VO2max',
        'interval_type': 'intervals',
        'interval_length': '2min',
        'duration_minutes': 45,
        'fatigue_impact': 'high',
        'difficulty': 'intermediate',
        'min_ftp': 210,
        'description': '5×2min VO2max efforts. Classic interval session for building aerobic capacity.',
        'coach_notes': {'repeat_adjust': [-1, 2], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 720},
            {'type': 'intervals', 'on_power': 115, 'off_power': 55, 'on_sec': 120, 'off_sec': 240, 'repeat': 5},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'VO2max 3min ×4',
        'category': 'vo2max',
        'subcategory': 'classic',
        'tags': ['vo2max', '3min', 'sustainable'],
        'target_zone': 'VO2max',
        'interval_type': 'intervals',
        'interval_length': '3min',
        'duration_minutes': 50,
        'fatigue_impact': 'high',
        'difficulty': 'intermediate',
        'min_ftp': 210,
        'description': '4×3min VO2max efforts. Longer intervals for sustained aerobic power.',
        'coach_notes': {'repeat_adjust': [-1, 2], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 900},
            {'type': 'intervals', 'on_power': 112, 'off_power': 55, 'on_sec': 180, 'off_sec': 300, 'repeat': 4},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'VO2max 3min ×5',
        'category': 'vo2max',
        'subcategory': 'classic',
        'tags': ['vo2max', '3min', 'high_volume'],
        'target_zone': 'VO2max',
        'interval_type': 'intervals',
        'interval_length': '3min',
        'duration_minutes': 55,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 220,
        'description': '5×3min VO2max efforts. High volume session requiring strong aerobic base.',
        'coach_notes': {'repeat_adjust': [-1, 1], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 900},
            {'type': 'intervals', 'on_power': 112, 'off_power': 55, 'on_sec': 180, 'off_sec': 300, 'repeat': 5},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'VO2max 4min ×4',
        'category': 'vo2max',
        'subcategory': 'classic',
        'tags': ['vo2max', '4min', 'endurance'],
        'target_zone': 'VO2max',
        'interval_type': 'intervals',
        'interval_length': '4min',
        'duration_minutes': 55,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 220,
        'description': '4×4min VO2max efforts. Long intervals for maximum time at VO2max.',
        'coach_notes': {'repeat_adjust': [-1, 1], 'power_adjust': [-5, 3], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 900},
            {'type': 'intervals', 'on_power': 110, 'off_power': 55, 'on_sec': 240, 'off_sec': 300, 'repeat': 4},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 540}
        ]
    })
    
    profiles.append({
        'name': 'VO2max 5min ×3',
        'category': 'vo2max',
        'subcategory': 'classic',
        'tags': ['vo2max', '5min', 'long'],
        'target_zone': 'VO2max',
        'interval_type': 'intervals',
        'interval_length': '5min',
        'duration_minutes': 50,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 230,
        'description': '3×5min VO2max efforts. Long sustained intervals for advanced athletes.',
        'coach_notes': {'repeat_adjust': [-1, 1], 'power_adjust': [-5, 3], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 900},
            {'type': 'intervals', 'on_power': 108, 'off_power': 55, 'on_sec': 300, 'off_sec': 300, 'repeat': 3},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 540}
        ]
    })
    
    profiles.append({
        'name': 'VO2max Pyramid 1-2-3-2-1min',
        'category': 'vo2max',
        'subcategory': 'pyramid',
        'tags': ['vo2max', 'pyramid', 'varied'],
        'target_zone': 'VO2max',
        'interval_type': 'intervals',
        'interval_length': 'mixed',
        'duration_minutes': 45,
        'fatigue_impact': 'high',
        'difficulty': 'intermediate',
        'min_ftp': 210,
        'description': 'Pyramid VO2max session with varied interval lengths. Mentally engaging workout.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 720},
            {'type': 'steady', 'power': 118, 'duration_sec': 60},
            {'type': 'steady', 'power': 55, 'duration_sec': 180},
            {'type': 'steady', 'power': 115, 'duration_sec': 120},
            {'type': 'steady', 'power': 55, 'duration_sec': 240},
            {'type': 'steady', 'power': 112, 'duration_sec': 180},
            {'type': 'steady', 'power': 55, 'duration_sec': 240},
            {'type': 'steady', 'power': 115, 'duration_sec': 120},
            {'type': 'steady', 'power': 55, 'duration_sec': 180},
            {'type': 'steady', 'power': 118, 'duration_sec': 60},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    # Threshold (12)
    profiles.append({
        'name': 'Classic 2×20min FTP',
        'category': 'threshold',
        'subcategory': 'classic',
        'tags': ['threshold', 'classic', '2x20'],
        'target_zone': 'Z4',
        'interval_type': 'intervals',
        'interval_length': '20min',
        'duration_minutes': 70,
        'fatigue_impact': 'high',
        'difficulty': 'intermediate',
        'min_ftp': 200,
        'description': 'The classic 2×20min FTP workout. Gold standard for threshold development.',
        'coach_notes': {'repeat_adjust': [0, 1], 'power_adjust': [-5, 3], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 900},
            {'type': 'steady', 'power': 100, 'duration_sec': 1200},
            {'type': 'steady', 'power': 55, 'duration_sec': 600},
            {'type': 'steady', 'power': 100, 'duration_sec': 1200},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 600}
        ]
    })
    
    profiles.append({
        'name': 'Classic 3×15min FTP',
        'category': 'threshold',
        'subcategory': 'classic',
        'tags': ['threshold', 'classic', '3x15'],
        'target_zone': 'Z4',
        'interval_type': 'intervals',
        'interval_length': '15min',
        'duration_minutes': 75,
        'fatigue_impact': 'high',
        'difficulty': 'intermediate',
        'min_ftp': 200,
        'description': '3×15min FTP intervals. More mentally manageable than 2×20.',
        'coach_notes': {'repeat_adjust': [-1, 1], 'power_adjust': [-5, 3], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 900},
            {'type': 'steady', 'power': 100, 'duration_sec': 900},
            {'type': 'steady', 'power': 55, 'duration_sec': 480},
            {'type': 'steady', 'power': 100, 'duration_sec': 900},
            {'type': 'steady', 'power': 55, 'duration_sec': 480},
            {'type': 'steady', 'power': 100, 'duration_sec': 900},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 600}
        ]
    })
    
    profiles.append({
        'name': 'Over/Under 3×9min',
        'category': 'threshold',
        'subcategory': 'over_under',
        'tags': ['threshold', 'over_under', 'race_specific'],
        'target_zone': 'Z4',
        'interval_type': 'over_under',
        'interval_length': '9min',
        'duration_minutes': 55,
        'fatigue_impact': 'high',
        'difficulty': 'advanced',
        'min_ftp': 220,
        'description': 'Over/under intervals: alternating between 95% and 105% FTP. Simulates race surges.',
        'coach_notes': {'repeat_adjust': [-1, 1], 'power_adjust': [-3, 3], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 720},
            {'type': 'intervals', 'on_power': 105, 'off_power': 95, 'on_sec': 90, 'off_sec': 90, 'repeat': 3},
            {'type': 'steady', 'power': 55, 'duration_sec': 300},
            {'type': 'intervals', 'on_power': 105, 'off_power': 95, 'on_sec': 90, 'off_sec': 90, 'repeat': 3},
            {'type': 'steady', 'power': 55, 'duration_sec': 300},
            {'type': 'intervals', 'on_power': 105, 'off_power': 95, 'on_sec': 90, 'off_sec': 90, 'repeat': 3},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 540}
        ]
    })
    
    profiles.append({
        'name': 'Over/Under 4×8min',
        'category': 'threshold',
        'subcategory': 'over_under',
        'tags': ['threshold', 'over_under', 'high_volume'],
        'target_zone': 'Z4',
        'interval_type': 'over_under',
        'interval_length': '8min',
        'duration_minutes': 60,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 220,
        'description': 'Extended over/under session with 4 sets. High-quality threshold work.',
        'coach_notes': {'repeat_adjust': [-1, 1], 'power_adjust': [-3, 3], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 720},
            {'type': 'intervals', 'on_power': 105, 'off_power': 95, 'on_sec': 80, 'off_sec': 80, 'repeat': 3},
            {'type': 'steady', 'power': 55, 'duration_sec': 240},
            {'type': 'intervals', 'on_power': 105, 'off_power': 95, 'on_sec': 80, 'off_sec': 80, 'repeat': 3},
            {'type': 'steady', 'power': 55, 'duration_sec': 240},
            {'type': 'intervals', 'on_power': 105, 'off_power': 95, 'on_sec': 80, 'off_sec': 80, 'repeat': 3},
            {'type': 'steady', 'power': 55, 'duration_sec': 240},
            {'type': 'intervals', 'on_power': 105, 'off_power': 95, 'on_sec': 80, 'off_sec': 80, 'repeat': 3},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 600}
        ]
    })
    
    profiles.append({
        'name': 'Over/Under 5×6min',
        'category': 'threshold',
        'subcategory': 'over_under',
        'tags': ['threshold', 'over_under', 'varied'],
        'target_zone': 'Z4',
        'interval_type': 'over_under',
        'interval_length': '6min',
        'duration_minutes': 55,
        'fatigue_impact': 'high',
        'difficulty': 'advanced',
        'min_ftp': 210,
        'description': '5 sets of 6-minute over/under intervals. Shorter sets for better power consistency.',
        'coach_notes': {'repeat_adjust': [-1, 2], 'power_adjust': [-3, 3], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 600},
            {'type': 'intervals', 'on_power': 105, 'off_power': 95, 'on_sec': 60, 'off_sec': 60, 'repeat': 3},
            {'type': 'steady', 'power': 55, 'duration_sec': 180},
            {'type': 'intervals', 'on_power': 105, 'off_power': 95, 'on_sec': 60, 'off_sec': 60, 'repeat': 3},
            {'type': 'steady', 'power': 55, 'duration_sec': 180},
            {'type': 'intervals', 'on_power': 105, 'off_power': 95, 'on_sec': 60, 'off_sec': 60, 'repeat': 3},
            {'type': 'steady', 'power': 55, 'duration_sec': 180},
            {'type': 'intervals', 'on_power': 105, 'off_power': 95, 'on_sec': 60, 'off_sec': 60, 'repeat': 3},
            {'type': 'steady', 'power': 55, 'duration_sec': 180},
            {'type': 'intervals', 'on_power': 105, 'off_power': 95, 'on_sec': 60, 'off_sec': 60, 'repeat': 3},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'Criss-Cross 3×10min',
        'category': 'threshold',
        'subcategory': 'criss_cross',
        'tags': ['threshold', 'criss_cross', 'tempo'],
        'target_zone': 'Z4',
        'interval_type': 'over_under',
        'interval_length': '10min',
        'duration_minutes': 55,
        'fatigue_impact': 'moderate',
        'difficulty': 'intermediate',
        'min_ftp': 200,
        'description': 'Criss-cross intervals alternating between tempo and threshold. Great for building aerobic base.',
        'coach_notes': {'repeat_adjust': [-1, 1], 'power_adjust': [-5, 3], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 600},
            {'type': 'intervals', 'on_power': 100, 'off_power': 85, 'on_sec': 120, 'off_sec': 120, 'repeat': 2},
            {'type': 'steady', 'power': 120, 'duration_sec': 60},
            {'type': 'steady', 'power': 55, 'duration_sec': 300},
            {'type': 'intervals', 'on_power': 100, 'off_power': 85, 'on_sec': 120, 'off_sec': 120, 'repeat': 2},
            {'type': 'steady', 'power': 120, 'duration_sec': 60},
            {'type': 'steady', 'power': 55, 'duration_sec': 300},
            {'type': 'intervals', 'on_power': 100, 'off_power': 85, 'on_sec': 120, 'off_sec': 120, 'repeat': 2},
            {'type': 'steady', 'power': 120, 'duration_sec': 60},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'Progressive Threshold 10-15-20min',
        'category': 'threshold',
        'subcategory': 'progressive',
        'tags': ['threshold', 'progressive', 'pyramid'],
        'target_zone': 'Z4',
        'interval_type': 'steady',
        'interval_length': 'mixed',
        'duration_minutes': 70,
        'fatigue_impact': 'high',
        'difficulty': 'advanced',
        'min_ftp': 220,
        'description': 'Progressive threshold intervals building from 10 to 20 minutes. Mentally engaging.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-3, 3], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 900},
            {'type': 'steady', 'power': 100, 'duration_sec': 600},
            {'type': 'steady', 'power': 55, 'duration_sec': 480},
            {'type': 'steady', 'power': 100, 'duration_sec': 900},
            {'type': 'steady', 'power': 55, 'duration_sec': 540},
            {'type': 'steady', 'power': 100, 'duration_sec': 1200},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 600}
        ]
    })
    
    profiles.append({
        'name': 'Sub-Threshold 2×20min @95%',
        'category': 'threshold',
        'subcategory': 'sub_threshold',
        'tags': ['threshold', 'sub_threshold', 'sustainable'],
        'target_zone': 'SST',
        'interval_type': 'steady',
        'interval_length': '20min',
        'duration_minutes': 65,
        'fatigue_impact': 'moderate',
        'difficulty': 'intermediate',
        'min_ftp': 200,
        'description': '2×20min at 95% FTP. Slightly easier than full threshold for higher volume weeks.',
        'coach_notes': {'repeat_adjust': [0, 1], 'power_adjust': [-5, 3], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 720},
            {'type': 'steady', 'power': 95, 'duration_sec': 1200},
            {'type': 'steady', 'power': 55, 'duration_sec': 600},
            {'type': 'steady', 'power': 95, 'duration_sec': 1200},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'Supra-Threshold 3×8min @105%',
        'category': 'threshold',
        'subcategory': 'supra_threshold',
        'tags': ['threshold', 'supra_threshold', 'hard'],
        'target_zone': 'Z4',
        'interval_type': 'steady',
        'interval_length': '8min',
        'duration_minutes': 50,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 230,
        'description': '3×8min at 105% FTP. Above threshold for maximal aerobic stress.',
        'coach_notes': {'repeat_adjust': [-1, 1], 'power_adjust': [-3, 0], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 720},
            {'type': 'steady', 'power': 105, 'duration_sec': 480},
            {'type': 'steady', 'power': 55, 'duration_sec': 360},
            {'type': 'steady', 'power': 105, 'duration_sec': 480},
            {'type': 'steady', 'power': 55, 'duration_sec': 360},
            {'type': 'steady', 'power': 105, 'duration_sec': 480},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'Step-Up Threshold 3×12min',
        'category': 'threshold',
        'subcategory': 'step_up',
        'tags': ['threshold', 'step_up', 'progressive'],
        'target_zone': 'Z4',
        'interval_type': 'ramp',
        'interval_length': '12min',
        'duration_minutes': 60,
        'fatigue_impact': 'high',
        'difficulty': 'advanced',
        'min_ftp': 210,
        'description': '3×12min with stepped power increases within each interval.',
        'coach_notes': {'repeat_adjust': [-1, 1], 'power_adjust': [-3, 3], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 720},
            {'type': 'steady', 'power': 95, 'duration_sec': 240},
            {'type': 'steady', 'power': 100, 'duration_sec': 240},
            {'type': 'steady', 'power': 105, 'duration_sec': 240},
            {'type': 'steady', 'power': 55, 'duration_sec': 300},
            {'type': 'steady', 'power': 95, 'duration_sec': 240},
            {'type': 'steady', 'power': 100, 'duration_sec': 240},
            {'type': 'steady', 'power': 105, 'duration_sec': 240},
            {'type': 'steady', 'power': 55, 'duration_sec': 300},
            {'type': 'steady', 'power': 95, 'duration_sec': 240},
            {'type': 'steady', 'power': 100, 'duration_sec': 240},
            {'type': 'steady', 'power': 105, 'duration_sec': 240},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 540}
        ]
    })
    
    profiles.append({
        'name': 'Threshold Surge 2×15min with 30s surges',
        'category': 'threshold',
        'subcategory': 'surge',
        'tags': ['threshold', 'surge', 'race_specific'],
        'target_zone': 'Z4',
        'interval_type': 'intervals',
        'interval_length': '15min',
        'duration_minutes': 60,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 220,
        'description': '2×15min threshold with 30s surges every 3 minutes. Race simulation.',
        'coach_notes': {'repeat_adjust': [0, 1], 'power_adjust': [-3, 3], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 720},
            {'type': 'steady', 'power': 100, 'duration_sec': 150},
            {'type': 'steady', 'power': 120, 'duration_sec': 30},
            {'type': 'steady', 'power': 100, 'duration_sec': 150},
            {'type': 'steady', 'power': 120, 'duration_sec': 30},
            {'type': 'steady', 'power': 100, 'duration_sec': 150},
            {'type': 'steady', 'power': 120, 'duration_sec': 30},
            {'type': 'steady', 'power': 100, 'duration_sec': 150},
            {'type': 'steady', 'power': 120, 'duration_sec': 30},
            {'type': 'steady', 'power': 100, 'duration_sec': 210},
            {'type': 'steady', 'power': 55, 'duration_sec': 600},
            {'type': 'steady', 'power': 100, 'duration_sec': 150},
            {'type': 'steady', 'power': 120, 'duration_sec': 30},
            {'type': 'steady', 'power': 100, 'duration_sec': 150},
            {'type': 'steady', 'power': 120, 'duration_sec': 30},
            {'type': 'steady', 'power': 100, 'duration_sec': 150},
            {'type': 'steady', 'power': 120, 'duration_sec': 30},
            {'type': 'steady', 'power': 100, 'duration_sec': 150},
            {'type': 'steady', 'power': 120, 'duration_sec': 30},
            {'type': 'steady', 'power': 100, 'duration_sec': 210},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 600}
        ]
    })
    
    profiles.append({
        'name': 'Race-Pace Threshold 40min steady',
        'category': 'threshold',
        'subcategory': 'race_pace',
        'tags': ['threshold', 'race_pace', 'tt'],
        'target_zone': 'Z4',
        'interval_type': 'steady',
        'interval_length': '40min',
        'duration_minutes': 60,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 230,
        'description': 'Single 40min threshold effort. Time trial simulation.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-3, 3], 'warmup_adjust': [-2, 10], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 900},
            {'type': 'steady', 'power': 100, 'duration_sec': 2400},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 600}
        ]
    })
    
    # SweetSpot (10)
    profiles.append({
        'name': 'SST 3×10min',
        'category': 'sweetspot',
        'tags': ['sweetspot', 'sst', 'classic'],
        'target_zone': 'SST',
        'interval_type': 'steady',
        'interval_length': '10min',
        'duration_minutes': 50,
        'fatigue_impact': 'moderate',
        'difficulty': 'intermediate',
        'min_ftp': 200,
        'description': '3×10min sweet spot intervals. High TSS with manageable fatigue.',
        'coach_notes': {'repeat_adjust': [-1, 2], 'power_adjust': [-5, 3], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 600},
            {'type': 'steady', 'power': 90, 'duration_sec': 600},
            {'type': 'steady', 'power': 55, 'duration_sec': 300},
            {'type': 'steady', 'power': 90, 'duration_sec': 600},
            {'type': 'steady', 'power': 55, 'duration_sec': 300},
            {'type': 'steady', 'power': 90, 'duration_sec': 600},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'SST 2×20min',
        'category': 'sweetspot',
        'tags': ['sweetspot', 'sst', 'classic'],
        'target_zone': 'SST',
        'interval_type': 'steady',
        'interval_length': '20min',
        'duration_minutes': 60,
        'fatigue_impact': 'moderate',
        'difficulty': 'intermediate',
        'min_ftp': 200,
        'description': '2×20min sweet spot. Classic sweet spot workout format.',
        'coach_notes': {'repeat_adjust': [0, 1], 'power_adjust': [-5, 3], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 720},
            {'type': 'steady', 'power': 90, 'duration_sec': 1200},
            {'type': 'steady', 'power': 55, 'duration_sec': 480},
            {'type': 'steady', 'power': 90, 'duration_sec': 1200},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 600}
        ]
    })
    
    profiles.append({
        'name': 'SST 3×15min',
        'category': 'sweetspot',
        'tags': ['sweetspot', 'sst', 'extended'],
        'target_zone': 'SST',
        'interval_type': 'steady',
        'interval_length': '15min',
        'duration_minutes': 70,
        'fatigue_impact': 'high',
        'difficulty': 'intermediate',
        'min_ftp': 210,
        'description': '3×15min sweet spot. Higher volume sweet spot session.',
        'coach_notes': {'repeat_adjust': [-1, 1], 'power_adjust': [-5, 3], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 900},
            {'type': 'steady', 'power': 90, 'duration_sec': 900},
            {'type': 'steady', 'power': 55, 'duration_sec': 360},
            {'type': 'steady', 'power': 90, 'duration_sec': 900},
            {'type': 'steady', 'power': 55, 'duration_sec': 360},
            {'type': 'steady', 'power': 90, 'duration_sec': 900},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 600}
        ]
    })
    
    profiles.append({
        'name': 'SST Progressive 85→92% 30min',
        'category': 'sweetspot',
        'subcategory': 'progressive',
        'tags': ['sweetspot', 'progressive', 'ramp'],
        'target_zone': 'SST',
        'interval_type': 'ramp',
        'interval_length': '30min',
        'duration_minutes': 50,
        'fatigue_impact': 'moderate',
        'difficulty': 'intermediate',
        'min_ftp': 200,
        'description': 'Single 30min progressive sweet spot from 85% to 92% FTP.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 3], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 600},
            {'type': 'ramp', 'start_power': 85, 'end_power': 92, 'duration_sec': 1800},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 600}
        ]
    })
    
    profiles.append({
        'name': 'SST + VO2 Finish 2×15min + 3×2min',
        'category': 'sweetspot',
        'subcategory': 'mixed',
        'tags': ['sweetspot', 'vo2max', 'combo'],
        'target_zone': 'mixed',
        'interval_type': 'intervals',
        'interval_length': 'mixed',
        'duration_minutes': 65,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 220,
        'description': '2×15min SST followed by 3×2min VO2max. Compound workout.',
        'coach_notes': {'repeat_adjust': [-1, 1], 'power_adjust': [-5, 3], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 720},
            {'type': 'steady', 'power': 90, 'duration_sec': 900},
            {'type': 'steady', 'power': 55, 'duration_sec': 360},
            {'type': 'steady', 'power': 90, 'duration_sec': 900},
            {'type': 'steady', 'power': 55, 'duration_sec': 480},
            {'type': 'intervals', 'on_power': 115, 'off_power': 55, 'on_sec': 120, 'off_sec': 240, 'repeat': 3},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'SST Climbing Sim 3×12min @88-92%',
        'category': 'sweetspot',
        'subcategory': 'climbing',
        'tags': ['sweetspot', 'climbing', 'simulation'],
        'target_zone': 'SST',
        'interval_type': 'steady',
        'interval_length': '12min',
        'duration_minutes': 55,
        'fatigue_impact': 'moderate',
        'difficulty': 'intermediate',
        'min_ftp': 200,
        'description': '3×12min sweet spot climb simulation. Steady climbing power.',
        'coach_notes': {'repeat_adjust': [-1, 1], 'power_adjust': [-5, 3], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 600},
            {'type': 'steady', 'power': 90, 'duration_sec': 720},
            {'type': 'steady', 'power': 55, 'duration_sec': 300},
            {'type': 'steady', 'power': 90, 'duration_sec': 720},
            {'type': 'steady', 'power': 55, 'duration_sec': 300},
            {'type': 'steady', 'power': 90, 'duration_sec': 720},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'SST Over/Under Light 3×10min',
        'category': 'sweetspot',
        'subcategory': 'over_under',
        'tags': ['sweetspot', 'over_under', 'varied'],
        'target_zone': 'SST',
        'interval_type': 'over_under',
        'interval_length': '10min',
        'duration_minutes': 50,
        'fatigue_impact': 'moderate',
        'difficulty': 'intermediate',
        'min_ftp': 200,
        'description': '3×10min sweet spot with light over/under variations.',
        'coach_notes': {'repeat_adjust': [-1, 2], 'power_adjust': [-5, 3], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 600},
            {'type': 'intervals', 'on_power': 92, 'off_power': 88, 'on_sec': 120, 'off_sec': 120, 'repeat': 2},
            {'type': 'steady', 'power': 90, 'duration_sec': 120},
            {'type': 'steady', 'power': 55, 'duration_sec': 300},
            {'type': 'intervals', 'on_power': 92, 'off_power': 88, 'on_sec': 120, 'off_sec': 120, 'repeat': 2},
            {'type': 'steady', 'power': 90, 'duration_sec': 120},
            {'type': 'steady', 'power': 55, 'duration_sec': 300},
            {'type': 'intervals', 'on_power': 92, 'off_power': 88, 'on_sec': 120, 'off_sec': 120, 'repeat': 2},
            {'type': 'steady', 'power': 90, 'duration_sec': 120},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'SST Extended 45min steady',
        'category': 'sweetspot',
        'subcategory': 'extended',
        'tags': ['sweetspot', 'long', 'steady'],
        'target_zone': 'SST',
        'interval_type': 'steady',
        'interval_length': '45min',
        'duration_minutes': 65,
        'fatigue_impact': 'high',
        'difficulty': 'advanced',
        'min_ftp': 220,
        'description': 'Single 45min sweet spot effort. Extended time in zone.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 3], 'warmup_adjust': [-2, 10], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 900},
            {'type': 'steady', 'power': 90, 'duration_sec': 2700},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 600}
        ]
    })
    
    profiles.append({
        'name': 'SST Tempo Sandwich Z3-SST-Z3',
        'category': 'sweetspot',
        'subcategory': 'tempo',
        'tags': ['sweetspot', 'tempo', 'sandwich'],
        'target_zone': 'SST',
        'interval_type': 'steady',
        'interval_length': 'mixed',
        'duration_minutes': 60,
        'fatigue_impact': 'moderate',
        'difficulty': 'intermediate',
        'min_ftp': 200,
        'description': 'Tempo-Sweet Spot-Tempo sandwich. Progressive intensity.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 3], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 600},
            {'type': 'steady', 'power': 80, 'duration_sec': 900},
            {'type': 'steady', 'power': 90, 'duration_sec': 1200},
            {'type': 'steady', 'power': 80, 'duration_sec': 900},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'SST Burst 3×12min with 20s sprints',
        'category': 'sweetspot',
        'subcategory': 'burst',
        'tags': ['sweetspot', 'sprint', 'neuromuscular'],
        'target_zone': 'SST',
        'interval_type': 'intervals',
        'interval_length': '12min',
        'duration_minutes': 55,
        'fatigue_impact': 'high',
        'difficulty': 'advanced',
        'min_ftp': 210,
        'description': '3×12min SST with 20s sprints every 3 minutes. Neuromuscular + aerobic.',
        'coach_notes': {'repeat_adjust': [-1, 1], 'power_adjust': [-5, 3], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 600},
            {'type': 'steady', 'power': 90, 'duration_sec': 160},
            {'type': 'steady', 'power': 150, 'duration_sec': 20},
            {'type': 'steady', 'power': 90, 'duration_sec': 160},
            {'type': 'steady', 'power': 150, 'duration_sec': 20},
            {'type': 'steady', 'power': 90, 'duration_sec': 160},
            {'type': 'steady', 'power': 150, 'duration_sec': 20},
            {'type': 'steady', 'power': 90, 'duration_sec': 160},
            {'type': 'steady', 'power': 55, 'duration_sec': 300},
            {'type': 'steady', 'power': 90, 'duration_sec': 160},
            {'type': 'steady', 'power': 150, 'duration_sec': 20},
            {'type': 'steady', 'power': 90, 'duration_sec': 160},
            {'type': 'steady', 'power': 150, 'duration_sec': 20},
            {'type': 'steady', 'power': 90, 'duration_sec': 160},
            {'type': 'steady', 'power': 150, 'duration_sec': 20},
            {'type': 'steady', 'power': 90, 'duration_sec': 160},
            {'type': 'steady', 'power': 55, 'duration_sec': 300},
            {'type': 'steady', 'power': 90, 'duration_sec': 160},
            {'type': 'steady', 'power': 150, 'duration_sec': 20},
            {'type': 'steady', 'power': 90, 'duration_sec': 160},
            {'type': 'steady', 'power': 150, 'duration_sec': 20},
            {'type': 'steady', 'power': 90, 'duration_sec': 160},
            {'type': 'steady', 'power': 150, 'duration_sec': 20},
            {'type': 'steady', 'power': 90, 'duration_sec': 160},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 540}
        ]
    })

    
    # Race Simulation (10)
    profiles.append({
        'name': 'Crit Sim — surges every 2min, final sprint',
        'category': 'race_sim',
        'subcategory': 'criterium',
        'tags': ['race', 'crit', 'surges', 'sprint'],
        'target_zone': 'mixed',
        'interval_type': 'intervals',
        'interval_length': 'mixed',
        'duration_minutes': 45,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 220,
        'description': 'Criterium race simulation with repeated surges and final sprint finish.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 3]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 600},
            {'type': 'intervals', 'on_power': 130, 'off_power': 85, 'on_sec': 20, 'off_sec': 100, 'repeat': 15},
            {'type': 'steady', 'power': 85, 'duration_sec': 120},
            {'type': 'steady', 'power': 180, 'duration_sec': 30},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 300}
        ]
    })
    
    profiles.append({
        'name': 'Road Race Sim — tempo + attacks + sprint finish',
        'category': 'race_sim',
        'subcategory': 'road_race',
        'tags': ['race', 'road_race', 'attacks', 'sprint'],
        'target_zone': 'mixed',
        'interval_type': 'free_form',
        'interval_length': 'mixed',
        'duration_minutes': 75,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 230,
        'description': 'Road race simulation with tempo riding, multiple attacks, and sprint finish.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 3]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 720},
            {'type': 'steady', 'power': 80, 'duration_sec': 1200},
            {'type': 'steady', 'power': 120, 'duration_sec': 60},
            {'type': 'steady', 'power': 85, 'duration_sec': 300},
            {'type': 'steady', 'power': 125, 'duration_sec': 90},
            {'type': 'steady', 'power': 85, 'duration_sec': 600},
            {'type': 'steady', 'power': 90, 'duration_sec': 900},
            {'type': 'steady', 'power': 130, 'duration_sec': 45},
            {'type': 'steady', 'power': 85, 'duration_sec': 240},
            {'type': 'steady', 'power': 170, 'duration_sec': 30},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 360}
        ]
    })
    
    profiles.append({
        'name': 'Breakaway Sim — threshold + attacks',
        'category': 'race_sim',
        'subcategory': 'breakaway',
        'tags': ['race', 'breakaway', 'threshold', 'attacks'],
        'target_zone': 'Z4',
        'interval_type': 'free_form',
        'interval_length': 'mixed',
        'duration_minutes': 60,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 230,
        'description': 'Breakaway simulation: sustained threshold with periodic attacks.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 720},
            {'type': 'steady', 'power': 100, 'duration_sec': 600},
            {'type': 'steady', 'power': 125, 'duration_sec': 45},
            {'type': 'steady', 'power': 100, 'duration_sec': 480},
            {'type': 'steady', 'power': 125, 'duration_sec': 60},
            {'type': 'steady', 'power': 100, 'duration_sec': 600},
            {'type': 'steady', 'power': 130, 'duration_sec': 30},
            {'type': 'steady', 'power': 100, 'duration_sec': 465},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 600}
        ]
    })
    
    profiles.append({
        'name': 'Group Ride Surges — Z2 with random surges',
        'category': 'race_sim',
        'subcategory': 'group_ride',
        'tags': ['endurance', 'surges', 'group_ride'],
        'target_zone': 'Z2',
        'interval_type': 'intervals',
        'interval_length': 'mixed',
        'duration_minutes': 60,
        'fatigue_impact': 'moderate',
        'difficulty': 'intermediate',
        'min_ftp': 200,
        'description': 'Group ride simulation with endurance base and random surges.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 70, 'duration_sec': 600},
            {'type': 'steady', 'power': 70, 'duration_sec': 600},
            {'type': 'steady', 'power': 110, 'duration_sec': 30},
            {'type': 'steady', 'power': 68, 'duration_sec': 450},
            {'type': 'steady', 'power': 115, 'duration_sec': 45},
            {'type': 'steady', 'power': 70, 'duration_sec': 720},
            {'type': 'steady', 'power': 105, 'duration_sec': 60},
            {'type': 'steady', 'power': 68, 'duration_sec': 600},
            {'type': 'steady', 'power': 120, 'duration_sec': 20},
            {'type': 'steady', 'power': 70, 'duration_sec': 415},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'Sprint Finish — build to max sprint',
        'category': 'race_sim',
        'subcategory': 'sprint_finish',
        'tags': ['sprint', 'finish', 'race'],
        'target_zone': 'anaerobic',
        'interval_type': 'free_form',
        'interval_length': 'mixed',
        'duration_minutes': 45,
        'fatigue_impact': 'high',
        'difficulty': 'advanced',
        'min_ftp': 220,
        'description': 'Race finish simulation with progressive build to maximal sprint.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 720},
            {'type': 'steady', 'power': 75, 'duration_sec': 1200},
            {'type': 'steady', 'power': 90, 'duration_sec': 300},
            {'type': 'steady', 'power': 110, 'duration_sec': 120},
            {'type': 'steady', 'power': 140, 'duration_sec': 30},
            {'type': 'steady', 'power': 180, 'duration_sec': 20},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'TT Simulation — 20min race pace',
        'category': 'race_sim',
        'subcategory': 'time_trial',
        'tags': ['tt', 'time_trial', 'race_pace'],
        'target_zone': 'Z4',
        'interval_type': 'steady',
        'interval_length': '20min',
        'duration_minutes': 50,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 230,
        'description': 'Time trial race simulation. Single sustained 20min effort at race pace.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-3, 3], 'warmup_adjust': [0, 10], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 900},
            {'type': 'steady', 'power': 85, 'duration_sec': 180},
            {'type': 'steady', 'power': 100, 'duration_sec': 60},
            {'type': 'steady', 'power': 55, 'duration_sec': 180},
            {'type': 'steady', 'power': 103, 'duration_sec': 1200},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 600}
        ]
    })
    
    profiles.append({
        'name': 'Cyclocross Intervals — 1min max efforts',
        'category': 'race_sim',
        'subcategory': 'cyclocross',
        'tags': ['cyclocross', 'cx', 'high_intensity'],
        'target_zone': 'anaerobic',
        'interval_type': 'intervals',
        'interval_length': '1min',
        'duration_minutes': 45,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 220,
        'description': 'Cyclocross race simulation with repeated 1-minute maximal efforts.',
        'coach_notes': {'repeat_adjust': [-1, 2], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 720},
            {'type': 'intervals', 'on_power': 135, 'off_power': 60, 'on_sec': 60, 'off_sec': 180, 'repeat': 8},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'Hill Sprint Race — short steep repeats',
        'category': 'race_sim',
        'subcategory': 'hill_sprint',
        'tags': ['climbing', 'sprint', 'steep'],
        'target_zone': 'anaerobic',
        'interval_type': 'intervals',
        'interval_length': '45s',
        'duration_minutes': 40,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 220,
        'description': 'Hill sprint race simulation. Short, steep, maximal efforts.',
        'coach_notes': {'repeat_adjust': [-1, 2], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 720},
            {'type': 'intervals', 'on_power': 145, 'off_power': 55, 'on_sec': 45, 'off_sec': 240, 'repeat': 6},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'Stage Race Sim — varied terrain/intensity',
        'category': 'race_sim',
        'subcategory': 'stage_race',
        'tags': ['stage_race', 'varied', 'long'],
        'target_zone': 'mixed',
        'interval_type': 'free_form',
        'interval_length': 'mixed',
        'duration_minutes': 90,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 230,
        'description': 'Stage race simulation with varied terrain and intensity changes.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 900},
            {'type': 'steady', 'power': 70, 'duration_sec': 1200},
            {'type': 'steady', 'power': 85, 'duration_sec': 600},
            {'type': 'steady', 'power': 95, 'duration_sec': 480},
            {'type': 'steady', 'power': 72, 'duration_sec': 420},
            {'type': 'steady', 'power': 110, 'duration_sec': 180},
            {'type': 'steady', 'power': 75, 'duration_sec': 600},
            {'type': 'steady', 'power': 88, 'duration_sec': 720},
            {'type': 'steady', 'power': 120, 'duration_sec': 60},
            {'type': 'steady', 'power': 70, 'duration_sec': 600},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 600}
        ]
    })
    
    profiles.append({
        'name': 'Criterium Attack Practice — attack + recover loops',
        'category': 'race_sim',
        'subcategory': 'criterium',
        'tags': ['crit', 'attacks', 'practice'],
        'target_zone': 'anaerobic',
        'interval_type': 'intervals',
        'interval_length': '30s',
        'duration_minutes': 50,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 220,
        'description': 'Criterium attack practice: repeated attack and recovery loops.',
        'coach_notes': {'repeat_adjust': [-2, 2], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 720},
            {'type': 'intervals', 'on_power': 140, 'off_power': 75, 'on_sec': 30, 'off_sec': 150, 'repeat': 12},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 540}
        ]
    })
    
    # Climbing (10)
    profiles.append({
        'name': 'Short Hill Repeats 6×3min @105%',
        'category': 'climbing',
        'subcategory': 'hill_repeats',
        'tags': ['climbing', 'repeats', 'short'],
        'target_zone': 'Z4',
        'interval_type': 'intervals',
        'interval_length': '3min',
        'duration_minutes': 50,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 220,
        'description': '6×3min hill repeats at supra-threshold power. Build climbing strength.',
        'coach_notes': {'repeat_adjust': [-1, 2], 'power_adjust': [-5, 3], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 720},
            {'type': 'intervals', 'on_power': 105, 'off_power': 55, 'on_sec': 180, 'off_sec': 300, 'repeat': 6},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'Hill Climb 3×10min @90-95%',
        'category': 'climbing',
        'subcategory': 'steady_climb',
        'tags': ['climbing', 'steady', 'moderate'],
        'target_zone': 'SST',
        'interval_type': 'intervals',
        'interval_length': '10min',
        'duration_minutes': 55,
        'fatigue_impact': 'high',
        'difficulty': 'intermediate',
        'min_ftp': 200,
        'description': '3×10min steady climbing intervals. Sustained climbing power.',
        'coach_notes': {'repeat_adjust': [-1, 1], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 720},
            {'type': 'steady', 'power': 92, 'duration_sec': 600},
            {'type': 'steady', 'power': 55, 'duration_sec': 300},
            {'type': 'steady', 'power': 92, 'duration_sec': 600},
            {'type': 'steady', 'power': 55, 'duration_sec': 300},
            {'type': 'steady', 'power': 92, 'duration_sec': 600},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'Tempo Climb 20min @85% steady',
        'category': 'climbing',
        'subcategory': 'tempo_climb',
        'tags': ['climbing', 'tempo', 'steady'],
        'target_zone': 'Z3',
        'interval_type': 'steady',
        'interval_length': '20min',
        'duration_minutes': 40,
        'fatigue_impact': 'moderate',
        'difficulty': 'intermediate',
        'min_ftp': 200,
        'description': 'Single 20min tempo climb. Sustainable climbing pace.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 600},
            {'type': 'steady', 'power': 85, 'duration_sec': 1200},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'Alpe Sim — progressive 30min climb',
        'category': 'climbing',
        'subcategory': 'long_climb',
        'tags': ['climbing', 'alpe', 'long', 'progressive'],
        'target_zone': 'SST',
        'interval_type': 'ramp',
        'interval_length': '30min',
        'duration_minutes': 50,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 220,
        'description': 'Alpe d\'Huez simulation. Progressive 30min climb.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 10], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 600},
            {'type': 'ramp', 'start_power': 85, 'end_power': 95, 'duration_sec': 1800},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 600}
        ]
    })
    
    profiles.append({
        'name': 'Climbing Attacks — 15min climb + 30s attacks',
        'category': 'climbing',
        'subcategory': 'climb_attack',
        'tags': ['climbing', 'attacks', 'race'],
        'target_zone': 'Z4',
        'interval_type': 'free_form',
        'interval_length': 'mixed',
        'duration_minutes': 50,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 230,
        'description': 'Climbing with attacks. 15min steady climb with 30s surges.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 720},
            {'type': 'steady', 'power': 95, 'duration_sec': 270},
            {'type': 'steady', 'power': 125, 'duration_sec': 30},
            {'type': 'steady', 'power': 95, 'duration_sec': 270},
            {'type': 'steady', 'power': 125, 'duration_sec': 30},
            {'type': 'steady', 'power': 95, 'duration_sec': 270},
            {'type': 'steady', 'power': 125, 'duration_sec': 30},
            {'type': 'steady', 'power': 95, 'duration_sec': 270},
            {'type': 'steady', 'power': 125, 'duration_sec': 30},
            {'type': 'steady', 'power': 95, 'duration_sec': 300},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 600}
        ]
    })
    
    profiles.append({
        'name': 'Mountain Stage — 2×20min w/ gradient changes',
        'category': 'climbing',
        'subcategory': 'mountain_stage',
        'tags': ['climbing', 'long', 'varied'],
        'target_zone': 'SST',
        'interval_type': 'intervals',
        'interval_length': '20min',
        'duration_minutes': 70,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 220,
        'description': 'Mountain stage simulation. 2×20min with power variations.',
        'coach_notes': {'repeat_adjust': [0, 1], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 900},
            {'type': 'intervals', 'on_power': 95, 'off_power': 88, 'on_sec': 240, 'off_sec': 240, 'repeat': 2},
            {'type': 'steady', 'power': 92, 'duration_sec': 240},
            {'type': 'steady', 'power': 55, 'duration_sec': 600},
            {'type': 'intervals', 'on_power': 95, 'off_power': 88, 'on_sec': 240, 'off_sec': 240, 'repeat': 2},
            {'type': 'steady', 'power': 92, 'duration_sec': 240},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 600}
        ]
    })
    
    profiles.append({
        'name': 'Standing Climb Repeats 5×2min @110%',
        'category': 'climbing',
        'subcategory': 'standing_repeats',
        'tags': ['climbing', 'standing', 'power'],
        'target_zone': 'VO2max',
        'interval_type': 'intervals',
        'interval_length': '2min',
        'duration_minutes': 40,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 230,
        'description': '5×2min standing climb repeats. High power, low cadence work.',
        'coach_notes': {'repeat_adjust': [-1, 2], 'power_adjust': [-5, 3], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 600},
            {'type': 'intervals', 'on_power': 110, 'off_power': 55, 'on_sec': 120, 'off_sec': 300, 'repeat': 5},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'Climb Sprint — 10min climb + hilltop sprint',
        'category': 'climbing',
        'subcategory': 'climb_sprint',
        'tags': ['climbing', 'sprint', 'hilltop'],
        'target_zone': 'SST',
        'interval_type': 'free_form',
        'interval_length': 'mixed',
        'duration_minutes': 45,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 220,
        'description': 'Climbing with hilltop sprint finish. Race-specific workout.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 720},
            {'type': 'steady', 'power': 90, 'duration_sec': 480},
            {'type': 'steady', 'power': 110, 'duration_sec': 90},
            {'type': 'steady', 'power': 160, 'duration_sec': 30},
            {'type': 'steady', 'power': 55, 'duration_sec': 420},
            {'type': 'steady', 'power': 90, 'duration_sec': 480},
            {'type': 'steady', 'power': 110, 'duration_sec': 90},
            {'type': 'steady', 'power': 160, 'duration_sec': 30},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'Sustained Climb 25min @88%',
        'category': 'climbing',
        'subcategory': 'sustained',
        'tags': ['climbing', 'sustained', 'long'],
        'target_zone': 'SST',
        'interval_type': 'steady',
        'interval_length': '25min',
        'duration_minutes': 45,
        'fatigue_impact': 'high',
        'difficulty': 'intermediate',
        'min_ftp': 210,
        'description': 'Single 25min sustained climb at sweet spot.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 10], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 600},
            {'type': 'steady', 'power': 88, 'duration_sec': 1500},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 600}
        ]
    })
    
    profiles.append({
        'name': 'Progressive Climb 30min 80→95%',
        'category': 'climbing',
        'subcategory': 'progressive',
        'tags': ['climbing', 'progressive', 'long'],
        'target_zone': 'SST',
        'interval_type': 'ramp',
        'interval_length': '30min',
        'duration_minutes': 50,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 220,
        'description': 'Progressive 30min climb from tempo to threshold.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 10], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 600},
            {'type': 'ramp', 'start_power': 80, 'end_power': 95, 'duration_sec': 1800},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 600}
        ]
    })

    
    # Sprint / Anaerobic (10)
    profiles.append({
        'name': 'Sprint Power 10×10s max',
        'category': 'sprint',
        'subcategory': 'neuromuscular',
        'tags': ['sprint', 'power', 'neuromuscular'],
        'target_zone': 'anaerobic',
        'interval_type': 'intervals',
        'interval_length': '10s',
        'duration_minutes': 30,
        'fatigue_impact': 'moderate',
        'difficulty': 'intermediate',
        'min_ftp': 200,
        'description': '10×10s maximal sprint efforts. Neuromuscular power development.',
        'coach_notes': {'repeat_adjust': [-2, 5], 'power_adjust': [0, 0], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 600},
            {'type': 'intervals', 'on_power': 200, 'off_power': 55, 'on_sec': 10, 'off_sec': 110, 'repeat': 10},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'Attack Repeats 6×1min @130%',
        'category': 'anaerobic',
        'subcategory': 'attacks',
        'tags': ['anaerobic', 'attacks', 'race'],
        'target_zone': 'anaerobic',
        'interval_type': 'intervals',
        'interval_length': '1min',
        'duration_minutes': 40,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 220,
        'description': '6×1min anaerobic attacks. Race-winning move practice.',
        'coach_notes': {'repeat_adjust': [-1, 2], 'power_adjust': [-10, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 720},
            {'type': 'intervals', 'on_power': 130, 'off_power': 55, 'on_sec': 60, 'off_sec': 300, 'repeat': 6},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'Sprint-Recover 8×20s max / 4min rest',
        'category': 'sprint',
        'subcategory': 'max_power',
        'tags': ['sprint', 'max_power', 'neuromuscular'],
        'target_zone': 'anaerobic',
        'interval_type': 'intervals',
        'interval_length': '20s',
        'duration_minutes': 40,
        'fatigue_impact': 'high',
        'difficulty': 'advanced',
        'min_ftp': 210,
        'description': '8×20s maximal sprints with full recovery. Peak power development.',
        'coach_notes': {'repeat_adjust': [-2, 2], 'power_adjust': [0, 0], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 600},
            {'type': 'intervals', 'on_power': 200, 'off_power': 55, 'on_sec': 20, 'off_sec': 240, 'repeat': 8},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'Neuromuscular Power 12×15s',
        'category': 'sprint',
        'subcategory': 'neuromuscular',
        'tags': ['sprint', 'neuromuscular', 'short'],
        'target_zone': 'anaerobic',
        'interval_type': 'intervals',
        'interval_length': '15s',
        'duration_minutes': 35,
        'fatigue_impact': 'moderate',
        'difficulty': 'intermediate',
        'min_ftp': 200,
        'description': '12×15s neuromuscular power sprints. Short, explosive efforts.',
        'coach_notes': {'repeat_adjust': [-3, 3], 'power_adjust': [0, 0], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 600},
            {'type': 'intervals', 'on_power': 200, 'off_power': 55, 'on_sec': 15, 'off_sec': 105, 'repeat': 12},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'Standing Start Sprints 6×30s',
        'category': 'sprint',
        'subcategory': 'standing_start',
        'tags': ['sprint', 'standing_start', 'acceleration'],
        'target_zone': 'anaerobic',
        'interval_type': 'intervals',
        'interval_length': '30s',
        'duration_minutes': 35,
        'fatigue_impact': 'high',
        'difficulty': 'advanced',
        'min_ftp': 210,
        'description': '6×30s standing start sprints. Acceleration and peak power.',
        'coach_notes': {'repeat_adjust': [-1, 2], 'power_adjust': [0, 0], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 600},
            {'type': 'intervals', 'on_power': 180, 'off_power': 55, 'on_sec': 30, 'off_sec': 270, 'repeat': 6},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'Tabata Classic 4min (8×20s/10s) ×2',
        'category': 'anaerobic',
        'subcategory': 'tabata',
        'tags': ['tabata', 'hiit', 'classic'],
        'target_zone': 'anaerobic',
        'interval_type': 'intervals',
        'interval_length': '20s',
        'duration_minutes': 30,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 220,
        'description': 'Classic Tabata protocol: 2 sets of 8×20s/10s. Extreme intensity.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-10, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 600},
            {'type': 'intervals', 'on_power': 150, 'off_power': 50, 'on_sec': 20, 'off_sec': 10, 'repeat': 8},
            {'type': 'steady', 'power': 55, 'duration_sec': 300},
            {'type': 'intervals', 'on_power': 150, 'off_power': 50, 'on_sec': 20, 'off_sec': 10, 'repeat': 8},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 300}
        ]
    })
    
    profiles.append({
        'name': 'AC Intervals 5×2min @125%',
        'category': 'anaerobic',
        'subcategory': 'anaerobic_capacity',
        'tags': ['anaerobic', 'ac', 'capacity'],
        'target_zone': 'anaerobic',
        'interval_type': 'intervals',
        'interval_length': '2min',
        'duration_minutes': 45,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 230,
        'description': '5×2min anaerobic capacity intervals. Build anaerobic endurance.',
        'coach_notes': {'repeat_adjust': [-1, 1], 'power_adjust': [-10, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 720},
            {'type': 'intervals', 'on_power': 125, 'off_power': 55, 'on_sec': 120, 'off_sec': 360, 'repeat': 5},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'Sprint Ladder 10s-20s-30s-20s-10s ×3',
        'category': 'sprint',
        'subcategory': 'ladder',
        'tags': ['sprint', 'ladder', 'varied'],
        'target_zone': 'anaerobic',
        'interval_type': 'intervals',
        'interval_length': 'mixed',
        'duration_minutes': 40,
        'fatigue_impact': 'high',
        'difficulty': 'advanced',
        'min_ftp': 210,
        'description': 'Sprint ladder workout. Varied sprint durations for complete development.',
        'coach_notes': {'repeat_adjust': [-1, 1], 'power_adjust': [0, 0], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 600},
            {'type': 'steady', 'power': 200, 'duration_sec': 10},
            {'type': 'steady', 'power': 55, 'duration_sec': 120},
            {'type': 'steady', 'power': 190, 'duration_sec': 20},
            {'type': 'steady', 'power': 55, 'duration_sec': 150},
            {'type': 'steady', 'power': 180, 'duration_sec': 30},
            {'type': 'steady', 'power': 55, 'duration_sec': 180},
            {'type': 'steady', 'power': 190, 'duration_sec': 20},
            {'type': 'steady', 'power': 55, 'duration_sec': 150},
            {'type': 'steady', 'power': 200, 'duration_sec': 10},
            {'type': 'steady', 'power': 55, 'duration_sec': 240},
            {'type': 'steady', 'power': 200, 'duration_sec': 10},
            {'type': 'steady', 'power': 55, 'duration_sec': 120},
            {'type': 'steady', 'power': 190, 'duration_sec': 20},
            {'type': 'steady', 'power': 55, 'duration_sec': 150},
            {'type': 'steady', 'power': 180, 'duration_sec': 30},
            {'type': 'steady', 'power': 55, 'duration_sec': 180},
            {'type': 'steady', 'power': 190, 'duration_sec': 20},
            {'type': 'steady', 'power': 55, 'duration_sec': 150},
            {'type': 'steady', 'power': 200, 'duration_sec': 10},
            {'type': 'steady', 'power': 55, 'duration_sec': 240},
            {'type': 'steady', 'power': 200, 'duration_sec': 10},
            {'type': 'steady', 'power': 55, 'duration_sec': 120},
            {'type': 'steady', 'power': 190, 'duration_sec': 20},
            {'type': 'steady', 'power': 55, 'duration_sec': 150},
            {'type': 'steady', 'power': 180, 'duration_sec': 30},
            {'type': 'steady', 'power': 55, 'duration_sec': 180},
            {'type': 'steady', 'power': 190, 'duration_sec': 20},
            {'type': 'steady', 'power': 55, 'duration_sec': 150},
            {'type': 'steady', 'power': 200, 'duration_sec': 10},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'Race Winning Move — 3×(3min@105% + 30s max)',
        'category': 'anaerobic',
        'subcategory': 'race_move',
        'tags': ['anaerobic', 'race', 'attack'],
        'target_zone': 'anaerobic',
        'interval_type': 'free_form',
        'interval_length': 'mixed',
        'duration_minutes': 45,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 230,
        'description': 'Race winning move practice: threshold surge + max attack.',
        'coach_notes': {'repeat_adjust': [-1, 1], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 720},
            {'type': 'steady', 'power': 105, 'duration_sec': 180},
            {'type': 'steady', 'power': 150, 'duration_sec': 30},
            {'type': 'steady', 'power': 55, 'duration_sec': 360},
            {'type': 'steady', 'power': 105, 'duration_sec': 180},
            {'type': 'steady', 'power': 150, 'duration_sec': 30},
            {'type': 'steady', 'power': 55, 'duration_sec': 360},
            {'type': 'steady', 'power': 105, 'duration_sec': 180},
            {'type': 'steady', 'power': 150, 'duration_sec': 30},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 540}
        ]
    })
    
    profiles.append({
        'name': 'Track Pursuit 4×4min @110%',
        'category': 'anaerobic',
        'subcategory': 'track',
        'tags': ['anaerobic', 'track', 'pursuit'],
        'target_zone': 'VO2max',
        'interval_type': 'intervals',
        'interval_length': '4min',
        'duration_minutes': 50,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 230,
        'description': 'Track pursuit intervals. 4×4min at VO2max power.',
        'coach_notes': {'repeat_adjust': [-1, 1], 'power_adjust': [-5, 3], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 900},
            {'type': 'intervals', 'on_power': 110, 'off_power': 55, 'on_sec': 240, 'off_sec': 360, 'repeat': 4},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 540}
        ]
    })
    
    # Endurance (12)
    profiles.append({
        'name': 'Z2 Steady 60min',
        'category': 'endurance',
        'tags': ['endurance', 'z2', 'base'],
        'target_zone': 'Z2',
        'interval_type': 'steady',
        'interval_length': '60min',
        'duration_minutes': 60,
        'fatigue_impact': 'low',
        'difficulty': 'beginner',
        'min_ftp': 150,
        'description': '60min zone 2 endurance. Aerobic base building.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [0, 0], 'cooldown_adjust': [0, 0]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 68, 'duration_sec': 600},
            {'type': 'steady', 'power': 68, 'duration_sec': 2700},
            {'type': 'cooldown', 'start_power': 68, 'end_power': 50, 'duration_sec': 300}
        ]
    })
    
    profiles.append({
        'name': 'Z2 Steady 90min',
        'category': 'endurance',
        'tags': ['endurance', 'z2', 'base'],
        'target_zone': 'Z2',
        'interval_type': 'steady',
        'interval_length': '90min',
        'duration_minutes': 90,
        'fatigue_impact': 'low',
        'difficulty': 'beginner',
        'min_ftp': 150,
        'description': '90min zone 2 endurance. Extended aerobic work.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [0, 0], 'cooldown_adjust': [0, 0]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 68, 'duration_sec': 600},
            {'type': 'steady', 'power': 68, 'duration_sec': 4500},
            {'type': 'cooldown', 'start_power': 68, 'end_power': 50, 'duration_sec': 300}
        ]
    })
    
    profiles.append({
        'name': 'Z2 Steady 120min',
        'category': 'endurance',
        'tags': ['endurance', 'z2', 'long'],
        'target_zone': 'Z2',
        'interval_type': 'steady',
        'interval_length': '120min',
        'duration_minutes': 120,
        'fatigue_impact': 'moderate',
        'difficulty': 'intermediate',
        'min_ftp': 180,
        'description': '2hr zone 2 endurance. Long aerobic session.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [0, 0], 'cooldown_adjust': [0, 0]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 68, 'duration_sec': 600},
            {'type': 'steady', 'power': 68, 'duration_sec': 6300},
            {'type': 'cooldown', 'start_power': 68, 'end_power': 50, 'duration_sec': 300}
        ]
    })
    
    profiles.append({
        'name': 'Z2 + Tempo Finish (60min: 45min Z2 + 15min Z3)',
        'category': 'endurance',
        'subcategory': 'combo',
        'tags': ['endurance', 'tempo', 'combo'],
        'target_zone': 'Z2',
        'interval_type': 'steady',
        'interval_length': 'mixed',
        'duration_minutes': 60,
        'fatigue_impact': 'moderate',
        'difficulty': 'intermediate',
        'min_ftp': 180,
        'description': '45min Z2 + 15min tempo finish. Progressive endurance.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [0, 0], 'cooldown_adjust': [-2, 3]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 68, 'duration_sec': 300},
            {'type': 'steady', 'power': 68, 'duration_sec': 2700},
            {'type': 'steady', 'power': 80, 'duration_sec': 900},
            {'type': 'cooldown', 'start_power': 70, 'end_power': 50, 'duration_sec': 300}
        ]
    })
    
    profiles.append({
        'name': 'Z2 + Threshold Finish (75min: 55min Z2 + 20min SST)',
        'category': 'endurance',
        'subcategory': 'combo',
        'tags': ['endurance', 'sweetspot', 'combo'],
        'target_zone': 'Z2',
        'interval_type': 'steady',
        'interval_length': 'mixed',
        'duration_minutes': 75,
        'fatigue_impact': 'moderate',
        'difficulty': 'intermediate',
        'min_ftp': 200,
        'description': '55min Z2 + 20min sweet spot. Endurance with quality finish.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [0, 0], 'cooldown_adjust': [-2, 3]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 68, 'duration_sec': 300},
            {'type': 'steady', 'power': 68, 'duration_sec': 3300},
            {'type': 'steady', 'power': 88, 'duration_sec': 1200},
            {'type': 'cooldown', 'start_power': 70, 'end_power': 50, 'duration_sec': 300}
        ]
    })
    
    profiles.append({
        'name': 'Z2 with Sprints 90min (every 15min sprint)',
        'category': 'endurance',
        'subcategory': 'sprints',
        'tags': ['endurance', 'sprints', 'neuromuscular'],
        'target_zone': 'Z2',
        'interval_type': 'free_form',
        'interval_length': 'mixed',
        'duration_minutes': 90,
        'fatigue_impact': 'moderate',
        'difficulty': 'intermediate',
        'min_ftp': 180,
        'description': '90min Z2 with 20s sprint every 15min. Endurance + neuromuscular.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [0, 0], 'cooldown_adjust': [0, 0]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 68, 'duration_sec': 300},
            {'type': 'steady', 'power': 68, 'duration_sec': 880},
            {'type': 'steady', 'power': 180, 'duration_sec': 20},
            {'type': 'steady', 'power': 68, 'duration_sec': 880},
            {'type': 'steady', 'power': 180, 'duration_sec': 20},
            {'type': 'steady', 'power': 68, 'duration_sec': 880},
            {'type': 'steady', 'power': 180, 'duration_sec': 20},
            {'type': 'steady', 'power': 68, 'duration_sec': 880},
            {'type': 'steady', 'power': 180, 'duration_sec': 20},
            {'type': 'steady', 'power': 68, 'duration_sec': 880},
            {'type': 'steady', 'power': 180, 'duration_sec': 20},
            {'type': 'steady', 'power': 68, 'duration_sec': 880},
            {'type': 'steady', 'power': 180, 'duration_sec': 20},
            {'type': 'cooldown', 'start_power': 68, 'end_power': 50, 'duration_sec': 300}
        ]
    })
    
    profiles.append({
        'name': 'Cafe Ride — Z2 with social surges',
        'category': 'endurance',
        'subcategory': 'social',
        'tags': ['endurance', 'social', 'varied'],
        'target_zone': 'Z2',
        'interval_type': 'free_form',
        'interval_length': 'mixed',
        'duration_minutes': 75,
        'fatigue_impact': 'moderate',
        'difficulty': 'intermediate',
        'min_ftp': 180,
        'description': 'Social cafe ride simulation with varied surges.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [0, 0], 'cooldown_adjust': [0, 0]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 68, 'duration_sec': 300},
            {'type': 'steady', 'power': 68, 'duration_sec': 900},
            {'type': 'steady', 'power': 95, 'duration_sec': 60},
            {'type': 'steady', 'power': 70, 'duration_sec': 720},
            {'type': 'steady', 'power': 85, 'duration_sec': 90},
            {'type': 'steady', 'power': 68, 'duration_sec': 900},
            {'type': 'steady', 'power': 100, 'duration_sec': 45},
            {'type': 'steady', 'power': 68, 'duration_sec': 900},
            {'type': 'steady', 'power': 90, 'duration_sec': 75},
            {'type': 'steady', 'power': 68, 'duration_sec': 510},
            {'type': 'cooldown', 'start_power': 68, 'end_power': 50, 'duration_sec': 300}
        ]
    })
    
    profiles.append({
        'name': 'Progressive Endurance 60min (Z2→Z3 gradual)',
        'category': 'endurance',
        'subcategory': 'progressive',
        'tags': ['endurance', 'progressive', 'ramp'],
        'target_zone': 'Z2',
        'interval_type': 'ramp',
        'interval_length': '60min',
        'duration_minutes': 60,
        'fatigue_impact': 'moderate',
        'difficulty': 'intermediate',
        'min_ftp': 180,
        'description': 'Progressive 60min endurance from Z2 to Z3.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [0, 0], 'cooldown_adjust': [0, 0]},
        'steps': [
            {'type': 'ramp', 'start_power': 65, 'end_power': 85, 'duration_sec': 3600}
        ]
    })
    
    profiles.append({
        'name': 'Fat Max 90min @65%',
        'category': 'endurance',
        'subcategory': 'fat_max',
        'tags': ['endurance', 'fat_burning', 'low_intensity'],
        'target_zone': 'Z2',
        'interval_type': 'steady',
        'interval_length': '90min',
        'duration_minutes': 90,
        'fatigue_impact': 'low',
        'difficulty': 'beginner',
        'min_ftp': 150,
        'description': '90min at fat max zone (65% FTP). Metabolic adaptation.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [0, 0], 'cooldown_adjust': [0, 0]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 65, 'duration_sec': 300},
            {'type': 'steady', 'power': 65, 'duration_sec': 4800},
            {'type': 'cooldown', 'start_power': 65, 'end_power': 50, 'duration_sec': 300}
        ]
    })
    
    profiles.append({
        'name': 'Long Endurance 3hr Z2',
        'category': 'endurance',
        'tags': ['endurance', 'long', 'z2'],
        'target_zone': 'Z2',
        'interval_type': 'steady',
        'interval_length': '180min',
        'duration_minutes': 180,
        'fatigue_impact': 'high',
        'difficulty': 'intermediate',
        'min_ftp': 200,
        'description': '3hr zone 2 endurance ride. Long aerobic base building.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [0, 0], 'cooldown_adjust': [0, 0]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 68, 'duration_sec': 600},
            {'type': 'steady', 'power': 68, 'duration_sec': 9900},
            {'type': 'cooldown', 'start_power': 68, 'end_power': 50, 'duration_sec': 300}
        ]
    })
    
    profiles.append({
        'name': 'Endurance + Cadence Drills (60min)',
        'category': 'endurance',
        'subcategory': 'drills',
        'tags': ['endurance', 'cadence', 'drills'],
        'target_zone': 'Z2',
        'interval_type': 'free_form',
        'interval_length': 'mixed',
        'duration_minutes': 60,
        'fatigue_impact': 'low',
        'difficulty': 'beginner',
        'min_ftp': 150,
        'description': '60min endurance with cadence variation drills.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [0, 0], 'cooldown_adjust': [0, 0]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 68, 'duration_sec': 300},
            {'type': 'steady', 'power': 68, 'duration_sec': 600},
            {'type': 'steady', 'power': 70, 'duration_sec': 180},
            {'type': 'steady', 'power': 68, 'duration_sec': 600},
            {'type': 'steady', 'power': 70, 'duration_sec': 180},
            {'type': 'steady', 'power': 68, 'duration_sec': 600},
            {'type': 'steady', 'power': 70, 'duration_sec': 180},
            {'type': 'steady', 'power': 68, 'duration_sec': 660},
            {'type': 'cooldown', 'start_power': 68, 'end_power': 50, 'duration_sec': 300}
        ]
    })
    
    profiles.append({
        'name': 'Z2 Negative Split 90min (first half easier)',
        'category': 'endurance',
        'subcategory': 'negative_split',
        'tags': ['endurance', 'negative_split', 'progressive'],
        'target_zone': 'Z2',
        'interval_type': 'steady',
        'interval_length': 'mixed',
        'duration_minutes': 90,
        'fatigue_impact': 'moderate',
        'difficulty': 'intermediate',
        'min_ftp': 180,
        'description': '90min negative split endurance. Build throughout ride.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [0, 0], 'cooldown_adjust': [0, 0]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 65, 'duration_sec': 300},
            {'type': 'steady', 'power': 65, 'duration_sec': 2400},
            {'type': 'steady', 'power': 72, 'duration_sec': 2400},
            {'type': 'cooldown', 'start_power': 72, 'end_power': 55, 'duration_sec': 300}
        ]
    })

    
    # Recovery (8)
    profiles.append({
        'name': 'Active Recovery 30min Z1',
        'category': 'recovery',
        'tags': ['recovery', 'z1', 'easy'],
        'target_zone': 'Z1',
        'interval_type': 'steady',
        'interval_length': '30min',
        'duration_minutes': 30,
        'fatigue_impact': 'low',
        'difficulty': 'beginner',
        'min_ftp': 120,
        'description': '30min easy recovery spin. Active recovery for tired legs.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [0, 5], 'warmup_adjust': [0, 0], 'cooldown_adjust': [0, 0]},
        'steps': [
            {'type': 'steady', 'power': 50, 'duration_sec': 1800}
        ]
    })
    
    profiles.append({
        'name': 'Active Recovery 45min Z1',
        'category': 'recovery',
        'tags': ['recovery', 'z1', 'easy'],
        'target_zone': 'Z1',
        'interval_type': 'steady',
        'interval_length': '45min',
        'duration_minutes': 45,
        'fatigue_impact': 'low',
        'difficulty': 'beginner',
        'min_ftp': 120,
        'description': '45min easy recovery spin. Extended active recovery.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [0, 5], 'warmup_adjust': [0, 0], 'cooldown_adjust': [0, 0]},
        'steps': [
            {'type': 'steady', 'power': 50, 'duration_sec': 2700}
        ]
    })
    
    profiles.append({
        'name': 'Recovery Spin 20min',
        'category': 'recovery',
        'tags': ['recovery', 'short', 'easy'],
        'target_zone': 'Z1',
        'interval_type': 'steady',
        'interval_length': '20min',
        'duration_minutes': 20,
        'fatigue_impact': 'low',
        'difficulty': 'beginner',
        'min_ftp': 100,
        'description': 'Short 20min recovery spin. Quick active recovery.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [0, 5], 'warmup_adjust': [0, 0], 'cooldown_adjust': [0, 0]},
        'steps': [
            {'type': 'steady', 'power': 48, 'duration_sec': 1200}
        ]
    })
    
    profiles.append({
        'name': 'Flush Ride 40min (progressive Z1)',
        'category': 'recovery',
        'subcategory': 'flush',
        'tags': ['recovery', 'flush', 'progressive'],
        'target_zone': 'Z1',
        'interval_type': 'ramp',
        'interval_length': '40min',
        'duration_minutes': 40,
        'fatigue_impact': 'low',
        'difficulty': 'beginner',
        'min_ftp': 120,
        'description': '40min progressive recovery ride. Gentle flush of fatigued muscles.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [0, 5], 'warmup_adjust': [0, 0], 'cooldown_adjust': [0, 0]},
        'steps': [
            {'type': 'ramp', 'start_power': 45, 'end_power': 55, 'duration_sec': 2400}
        ]
    })
    
    profiles.append({
        'name': 'Easy Spin + Openers 45min',
        'category': 'recovery',
        'subcategory': 'openers',
        'tags': ['recovery', 'openers', 'pre_race'],
        'target_zone': 'Z1',
        'interval_type': 'free_form',
        'interval_length': 'mixed',
        'duration_minutes': 45,
        'fatigue_impact': 'low',
        'difficulty': 'intermediate',
        'min_ftp': 150,
        'description': '45min easy spin with openers. Pre-race or rest day activation.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [0, 5], 'warmup_adjust': [0, 0], 'cooldown_adjust': [0, 0]},
        'steps': [
            {'type': 'steady', 'power': 50, 'duration_sec': 1800},
            {'type': 'steady', 'power': 90, 'duration_sec': 60},
            {'type': 'steady', 'power': 50, 'duration_sec': 300},
            {'type': 'steady', 'power': 95, 'duration_sec': 60},
            {'type': 'steady', 'power': 50, 'duration_sec': 300},
            {'type': 'steady', 'power': 100, 'duration_sec': 60},
            {'type': 'steady', 'power': 50, 'duration_sec': 120}
        ]
    })
    
    profiles.append({
        'name': 'Recovery with Leg Drills 30min',
        'category': 'recovery',
        'subcategory': 'drills',
        'tags': ['recovery', 'drills', 'skills'],
        'target_zone': 'Z1',
        'interval_type': 'free_form',
        'interval_length': 'mixed',
        'duration_minutes': 30,
        'fatigue_impact': 'low',
        'difficulty': 'beginner',
        'min_ftp': 120,
        'description': '30min recovery with single-leg and pedaling drills.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [0, 5], 'warmup_adjust': [0, 0], 'cooldown_adjust': [0, 0]},
        'steps': [
            {'type': 'steady', 'power': 50, 'duration_sec': 600},
            {'type': 'steady', 'power': 55, 'duration_sec': 120},
            {'type': 'steady', 'power': 50, 'duration_sec': 480},
            {'type': 'steady', 'power': 55, 'duration_sec': 120},
            {'type': 'steady', 'power': 50, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'Post-Race Recovery 35min',
        'category': 'recovery',
        'subcategory': 'post_race',
        'tags': ['recovery', 'post_race', 'easy'],
        'target_zone': 'Z1',
        'interval_type': 'steady',
        'interval_length': '35min',
        'duration_minutes': 35,
        'fatigue_impact': 'low',
        'difficulty': 'beginner',
        'min_ftp': 120,
        'description': '35min post-race recovery spin. Clear lactate and promote recovery.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [0, 5], 'warmup_adjust': [0, 0], 'cooldown_adjust': [0, 0]},
        'steps': [
            {'type': 'steady', 'power': 48, 'duration_sec': 2100}
        ]
    })
    
    profiles.append({
        'name': 'Gentle Endurance 50min @55-60%',
        'category': 'recovery',
        'subcategory': 'gentle',
        'tags': ['recovery', 'gentle', 'easy_endurance'],
        'target_zone': 'Z1',
        'interval_type': 'steady',
        'interval_length': '50min',
        'duration_minutes': 50,
        'fatigue_impact': 'low',
        'difficulty': 'beginner',
        'min_ftp': 150,
        'description': '50min gentle endurance. Easy aerobic stimulus without fatigue.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [0, 5], 'warmup_adjust': [0, 0], 'cooldown_adjust': [0, 0]},
        'steps': [
            {'type': 'steady', 'power': 58, 'duration_sec': 3000}
        ]
    })
    
    # Tempo (8)
    profiles.append({
        'name': 'Tempo Steady 30min @78%',
        'category': 'tempo',
        'tags': ['tempo', 'z3', 'steady'],
        'target_zone': 'Z3',
        'interval_type': 'steady',
        'interval_length': '30min',
        'duration_minutes': 50,
        'fatigue_impact': 'moderate',
        'difficulty': 'intermediate',
        'min_ftp': 180,
        'description': '30min steady tempo effort. Classic tempo workout.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 70, 'duration_sec': 600},
            {'type': 'steady', 'power': 78, 'duration_sec': 1800},
            {'type': 'cooldown', 'start_power': 65, 'end_power': 50, 'duration_sec': 600}
        ]
    })
    
    profiles.append({
        'name': 'Tempo Steady 45min @80%',
        'category': 'tempo',
        'tags': ['tempo', 'z3', 'extended'],
        'target_zone': 'Z3',
        'interval_type': 'steady',
        'interval_length': '45min',
        'duration_minutes': 65,
        'fatigue_impact': 'moderate',
        'difficulty': 'intermediate',
        'min_ftp': 200,
        'description': '45min extended tempo effort. Build aerobic capacity.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 70, 'duration_sec': 720},
            {'type': 'steady', 'power': 80, 'duration_sec': 2700},
            {'type': 'cooldown', 'start_power': 70, 'end_power': 50, 'duration_sec': 600}
        ]
    })
    
    profiles.append({
        'name': 'Tempo Intervals 3×15min',
        'category': 'tempo',
        'tags': ['tempo', 'intervals', 'z3'],
        'target_zone': 'Z3',
        'interval_type': 'intervals',
        'interval_length': '15min',
        'duration_minutes': 65,
        'fatigue_impact': 'moderate',
        'difficulty': 'intermediate',
        'min_ftp': 180,
        'description': '3×15min tempo intervals. Manageable tempo blocks.',
        'coach_notes': {'repeat_adjust': [-1, 1], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 70, 'duration_sec': 600},
            {'type': 'steady', 'power': 80, 'duration_sec': 900},
            {'type': 'steady', 'power': 55, 'duration_sec': 300},
            {'type': 'steady', 'power': 80, 'duration_sec': 900},
            {'type': 'steady', 'power': 55, 'duration_sec': 300},
            {'type': 'steady', 'power': 80, 'duration_sec': 900},
            {'type': 'cooldown', 'start_power': 65, 'end_power': 50, 'duration_sec': 600}
        ]
    })
    
    profiles.append({
        'name': 'Progressive Tempo 40min 75→88%',
        'category': 'tempo',
        'subcategory': 'progressive',
        'tags': ['tempo', 'progressive', 'ramp'],
        'target_zone': 'Z3',
        'interval_type': 'ramp',
        'interval_length': '40min',
        'duration_minutes': 60,
        'fatigue_impact': 'moderate',
        'difficulty': 'intermediate',
        'min_ftp': 200,
        'description': '40min progressive tempo from Z3 low to sweet spot.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 70, 'duration_sec': 600},
            {'type': 'ramp', 'start_power': 75, 'end_power': 88, 'duration_sec': 2400},
            {'type': 'cooldown', 'start_power': 70, 'end_power': 50, 'duration_sec': 600}
        ]
    })
    
    profiles.append({
        'name': 'Tempo + Surge 3×12min with 30s attacks',
        'category': 'tempo',
        'subcategory': 'surge',
        'tags': ['tempo', 'surges', 'race_specific'],
        'target_zone': 'Z3',
        'interval_type': 'free_form',
        'interval_length': '12min',
        'duration_minutes': 55,
        'fatigue_impact': 'high',
        'difficulty': 'advanced',
        'min_ftp': 210,
        'description': '3×12min tempo with 30s surges. Race-specific tempo work.',
        'coach_notes': {'repeat_adjust': [-1, 1], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 70, 'duration_sec': 600},
            {'type': 'steady', 'power': 80, 'duration_sec': 330},
            {'type': 'steady', 'power': 110, 'duration_sec': 30},
            {'type': 'steady', 'power': 80, 'duration_sec': 330},
            {'type': 'steady', 'power': 110, 'duration_sec': 30},
            {'type': 'steady', 'power': 80, 'duration_sec': 0},
            {'type': 'steady', 'power': 55, 'duration_sec': 300},
            {'type': 'steady', 'power': 80, 'duration_sec': 330},
            {'type': 'steady', 'power': 110, 'duration_sec': 30},
            {'type': 'steady', 'power': 80, 'duration_sec': 330},
            {'type': 'steady', 'power': 110, 'duration_sec': 30},
            {'type': 'steady', 'power': 80, 'duration_sec': 30},
            {'type': 'steady', 'power': 55, 'duration_sec': 300},
            {'type': 'steady', 'power': 80, 'duration_sec': 330},
            {'type': 'steady', 'power': 110, 'duration_sec': 30},
            {'type': 'steady', 'power': 80, 'duration_sec': 330},
            {'type': 'steady', 'power': 110, 'duration_sec': 30},
            {'type': 'steady', 'power': 80, 'duration_sec': 30},
            {'type': 'cooldown', 'start_power': 65, 'end_power': 50, 'duration_sec': 600}
        ]
    })
    
    profiles.append({
        'name': 'Tempo Climbing 3×10min @82%',
        'category': 'tempo',
        'subcategory': 'climbing',
        'tags': ['tempo', 'climbing', 'steady'],
        'target_zone': 'Z3',
        'interval_type': 'intervals',
        'interval_length': '10min',
        'duration_minutes': 50,
        'fatigue_impact': 'moderate',
        'difficulty': 'intermediate',
        'min_ftp': 180,
        'description': '3×10min tempo climbing intervals. Steady climbing power.',
        'coach_notes': {'repeat_adjust': [-1, 2], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 70, 'duration_sec': 600},
            {'type': 'steady', 'power': 82, 'duration_sec': 600},
            {'type': 'steady', 'power': 55, 'duration_sec': 240},
            {'type': 'steady', 'power': 82, 'duration_sec': 600},
            {'type': 'steady', 'power': 55, 'duration_sec': 240},
            {'type': 'steady', 'power': 82, 'duration_sec': 600},
            {'type': 'cooldown', 'start_power': 65, 'end_power': 50, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'Steady State Tempo 60min',
        'category': 'tempo',
        'subcategory': 'steady_state',
        'tags': ['tempo', 'steady_state', 'long'],
        'target_zone': 'Z3',
        'interval_type': 'steady',
        'interval_length': '60min',
        'duration_minutes': 80,
        'fatigue_impact': 'high',
        'difficulty': 'advanced',
        'min_ftp': 220,
        'description': '60min steady state tempo. Extended tempo effort.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 10], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 70, 'duration_sec': 720},
            {'type': 'steady', 'power': 80, 'duration_sec': 3600},
            {'type': 'cooldown', 'start_power': 70, 'end_power': 50, 'duration_sec': 600}
        ]
    })
    
    profiles.append({
        'name': 'Tempo Over/Under Light 4×8min',
        'category': 'tempo',
        'subcategory': 'over_under',
        'tags': ['tempo', 'over_under', 'varied'],
        'target_zone': 'Z3',
        'interval_type': 'over_under',
        'interval_length': '8min',
        'duration_minutes': 55,
        'fatigue_impact': 'moderate',
        'difficulty': 'intermediate',
        'min_ftp': 200,
        'description': '4×8min tempo over/under. Light power variations.',
        'coach_notes': {'repeat_adjust': [-1, 1], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 70, 'duration_sec': 600},
            {'type': 'intervals', 'on_power': 85, 'off_power': 78, 'on_sec': 120, 'off_sec': 120, 'repeat': 2},
            {'type': 'steady', 'power': 55, 'duration_sec': 240},
            {'type': 'intervals', 'on_power': 85, 'off_power': 78, 'on_sec': 120, 'off_sec': 120, 'repeat': 2},
            {'type': 'steady', 'power': 55, 'duration_sec': 240},
            {'type': 'intervals', 'on_power': 85, 'off_power': 78, 'on_sec': 120, 'off_sec': 120, 'repeat': 2},
            {'type': 'steady', 'power': 55, 'duration_sec': 240},
            {'type': 'intervals', 'on_power': 85, 'off_power': 78, 'on_sec': 120, 'off_sec': 120, 'repeat': 2},
            {'type': 'cooldown', 'start_power': 65, 'end_power': 50, 'duration_sec': 600}
        ]
    })
    
    # Mixed / Special (8)
    profiles.append({
        'name': 'Kitchen Sink — all zones touched',
        'category': 'mixed',
        'tags': ['mixed', 'varied', 'all_zones'],
        'target_zone': 'mixed',
        'interval_type': 'free_form',
        'interval_length': 'mixed',
        'duration_minutes': 60,
        'fatigue_impact': 'high',
        'difficulty': 'advanced',
        'min_ftp': 210,
        'description': 'Kitchen sink workout touching all training zones.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 70, 'duration_sec': 600},
            {'type': 'steady', 'power': 70, 'duration_sec': 300},
            {'type': 'steady', 'power': 80, 'duration_sec': 300},
            {'type': 'steady', 'power': 90, 'duration_sec': 300},
            {'type': 'steady', 'power': 100, 'duration_sec': 180},
            {'type': 'steady', 'power': 115, 'duration_sec': 120},
            {'type': 'steady', 'power': 130, 'duration_sec': 60},
            {'type': 'steady', 'power': 55, 'duration_sec': 300},
            {'type': 'steady', 'power': 90, 'duration_sec': 300},
            {'type': 'steady', 'power': 100, 'duration_sec': 240},
            {'type': 'steady', 'power': 115, 'duration_sec': 120},
            {'type': 'steady', 'power': 55, 'duration_sec': 300},
            {'type': 'steady', 'power': 180, 'duration_sec': 20},
            {'type': 'steady', 'power': 70, 'duration_sec': 280},
            {'type': 'cooldown', 'start_power': 65, 'end_power': 50, 'duration_sec': 480}
        ]
    })
    
    profiles.append({
        'name': 'FTP Test Protocol — 20min test',
        'category': 'mixed',
        'subcategory': 'test',
        'tags': ['test', 'ftp', 'assessment'],
        'target_zone': 'Z4',
        'interval_type': 'steady',
        'interval_length': '20min',
        'duration_minutes': 50,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 150,
        'description': 'FTP test protocol with 20min all-out effort. Use 95% of average power.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [0, 0], 'warmup_adjust': [0, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 1200},
            {'type': 'steady', 'power': 95, 'duration_sec': 300},
            {'type': 'steady', 'power': 55, 'duration_sec': 300},
            {'type': 'steady', 'power': 100, 'duration_sec': 1200},
            {'type': 'cooldown', 'start_power': 60, 'end_power': 40, 'duration_sec': 600}
        ]
    })
    
    profiles.append({
        'name': 'Ramp Test Protocol',
        'category': 'mixed',
        'subcategory': 'test',
        'tags': ['test', 'ramp', 'ftp'],
        'target_zone': 'mixed',
        'interval_type': 'ramp',
        'interval_length': '25min',
        'duration_minutes': 25,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 150,
        'description': 'Ramp test protocol: progressive power increase to failure.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [0, 0], 'warmup_adjust': [0, 0], 'cooldown_adjust': [0, 0]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 70, 'duration_sec': 300},
            {'type': 'ramp', 'start_power': 70, 'end_power': 160, 'duration_sec': 1200},
            {'type': 'cooldown', 'start_power': 50, 'end_power': 40, 'duration_sec': 300}
        ]
    })
    
    profiles.append({
        'name': 'Polarized Classic — Z2 + VO2max only',
        'category': 'mixed',
        'subcategory': 'polarized',
        'tags': ['polarized', 'z2', 'vo2max'],
        'target_zone': 'mixed',
        'interval_type': 'intervals',
        'interval_length': 'mixed',
        'duration_minutes': 60,
        'fatigue_impact': 'high',
        'difficulty': 'advanced',
        'min_ftp': 220,
        'description': 'Polarized training: Z2 base with VO2max intervals. No threshold work.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [0, 0], 'cooldown_adjust': [0, 0]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 68, 'duration_sec': 300},
            {'type': 'steady', 'power': 68, 'duration_sec': 900},
            {'type': 'intervals', 'on_power': 115, 'off_power': 68, 'on_sec': 180, 'off_sec': 300, 'repeat': 4},
            {'type': 'steady', 'power': 68, 'duration_sec': 600},
            {'type': 'cooldown', 'start_power': 68, 'end_power': 50, 'duration_sec': 300}
        ]
    })
    
    profiles.append({
        'name': 'Norwegian Method — 4×8min Z2/VO2',
        'category': 'mixed',
        'subcategory': 'norwegian',
        'tags': ['norwegian', 'polarized', 'vo2max'],
        'target_zone': 'mixed',
        'interval_type': 'over_under',
        'interval_length': '8min',
        'duration_minutes': 60,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 230,
        'description': 'Norwegian method: 4×8min alternating Z2 and VO2max.',
        'coach_notes': {'repeat_adjust': [-1, 1], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 70, 'duration_sec': 720},
            {'type': 'intervals', 'on_power': 115, 'off_power': 68, 'on_sec': 120, 'off_sec': 120, 'repeat': 2},
            {'type': 'steady', 'power': 68, 'duration_sec': 240},
            {'type': 'intervals', 'on_power': 115, 'off_power': 68, 'on_sec': 120, 'off_sec': 120, 'repeat': 2},
            {'type': 'steady', 'power': 68, 'duration_sec': 240},
            {'type': 'intervals', 'on_power': 115, 'off_power': 68, 'on_sec': 120, 'off_sec': 120, 'repeat': 2},
            {'type': 'steady', 'power': 68, 'duration_sec': 240},
            {'type': 'intervals', 'on_power': 115, 'off_power': 68, 'on_sec': 120, 'off_sec': 120, 'repeat': 2},
            {'type': 'cooldown', 'start_power': 65, 'end_power': 50, 'duration_sec': 600}
        ]
    })
    
    profiles.append({
        'name': 'Reverse Periodization — sprint first, endurance after',
        'category': 'mixed',
        'subcategory': 'reverse',
        'tags': ['mixed', 'sprint', 'endurance'],
        'target_zone': 'mixed',
        'interval_type': 'free_form',
        'interval_length': 'mixed',
        'duration_minutes': 60,
        'fatigue_impact': 'moderate',
        'difficulty': 'intermediate',
        'min_ftp': 200,
        'description': 'Reverse periodization: sprints when fresh, endurance after.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [0, 0]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 600},
            {'type': 'intervals', 'on_power': 180, 'off_power': 55, 'on_sec': 15, 'off_sec': 105, 'repeat': 6},
            {'type': 'steady', 'power': 68, 'duration_sec': 2100},
            {'type': 'cooldown', 'start_power': 68, 'end_power': 50, 'duration_sec': 300}
        ]
    })
    
    profiles.append({
        'name': 'Brick Workout — bike to run transition sim',
        'category': 'mixed',
        'subcategory': 'brick',
        'tags': ['brick', 'triathlon', 'transition'],
        'target_zone': 'SST',
        'interval_type': 'free_form',
        'interval_length': 'mixed',
        'duration_minutes': 45,
        'fatigue_impact': 'high',
        'difficulty': 'advanced',
        'min_ftp': 210,
        'description': 'Brick workout simulation: bike effort preparing for run transition.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [-2, 5], 'cooldown_adjust': [-5, 0]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 75, 'duration_sec': 600},
            {'type': 'steady', 'power': 88, 'duration_sec': 1200},
            {'type': 'steady', 'power': 92, 'duration_sec': 600},
            {'type': 'steady', 'power': 100, 'duration_sec': 180},
            {'type': 'steady', 'power': 75, 'duration_sec': 120}
        ]
    })
    
    profiles.append({
        'name': 'Fatigue Resistance — SST after Z2 base',
        'category': 'mixed',
        'subcategory': 'fatigue_resistance',
        'tags': ['fatigue_resistance', 'endurance', 'sweetspot'],
        'target_zone': 'SST',
        'interval_type': 'free_form',
        'interval_length': 'mixed',
        'duration_minutes': 90,
        'fatigue_impact': 'very_high',
        'difficulty': 'advanced',
        'min_ftp': 220,
        'description': 'Fatigue resistance: 60min Z2 + 2×15min SST. Quality under fatigue.',
        'coach_notes': {'repeat_adjust': [0, 0], 'power_adjust': [-5, 5], 'warmup_adjust': [0, 0], 'cooldown_adjust': [-2, 5]},
        'steps': [
            {'type': 'warmup', 'start_power': 50, 'end_power': 68, 'duration_sec': 300},
            {'type': 'steady', 'power': 68, 'duration_sec': 3600},
            {'type': 'steady', 'power': 90, 'duration_sec': 900},
            {'type': 'steady', 'power': 55, 'duration_sec': 300},
            {'type': 'steady', 'power': 90, 'duration_sec': 900},
            {'type': 'cooldown', 'start_power': 70, 'end_power': 50, 'duration_sec': 600}
        ]
    })
    
    return profiles


def main():
    """Main execution"""
    db_path = Path(__file__).parent.parent / 'data' / 'workout_profiles.db'
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Remove existing database to start fresh
    if db_path.exists():
        print(f"Removing existing database: {db_path}")
        db_path.unlink()
    
    # Create database and schema
    print(f"Creating database: {db_path}")
    conn = sqlite3.connect(db_path)
    create_schema(conn)
    
    # Insert profiles
    profiles = get_profiles()
    print(f"Inserting {len(profiles)} workout profiles...")
    
    for i, profile in enumerate(profiles, 1):
        print(f"  [{i:3d}/100] {profile['name']}")
        insert_profile(conn, profile)
    
    conn.close()
    print(f"\n✅ Database created successfully!")
    print(f"   Location: {db_path}")
    print(f"   Profiles: {len(profiles)}")
    
    # Show summary by category
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT category, COUNT(*) FROM workout_profiles GROUP BY category ORDER BY category')
    print("\n📊 Profiles by category:")
    for category, count in cursor.fetchall():
        print(f"   {category:20s}: {count:3d}")
    conn.close()


if __name__ == '__main__':
    main()
