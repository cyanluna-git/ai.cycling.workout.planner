#!/usr/bin/env python3
"""
WhatsonZwift.com Scraper V2
Scrapes workouts from collection pages (workouts are embedded)
"""

import re
import time
import sqlite3
import argparse
import tempfile
from pathlib import Path
from enum import Enum
import xml.etree.ElementTree as ET

import requests
from lxml import html as lhtml, etree
from lxml.builder import E

# Import the existing importer
import sys
sys.path.insert(0, str(Path(__file__).parent))
from import_zwo import import_zwo_to_db


class StepPosition(Enum):
    FIRST = 0
    MIDDLE = 1
    LAST = 2


# Regex patterns from wozzwo
RAMP_RE = re.compile(
    r'(?:(?P<mins>\\d+)min )?(?:(?P<secs>\\d+)sec )?'
    r'(?:@ (?P<cadence>\\d+)rpm, )?from (?P<low>\\d+) to (?P<high>\\d+)% FTP'
)

STEADY_RE = re.compile(
    r'(?:(?P<mins>\\d+)min )?(?:(?P<secs>\\d+)sec )?'
    r'@ (?:(?P<cadence>\\d+)rpm, )?(?P<power>\\d+)% FTP'
)

INTERVALS_RE = re.compile(
    r'(?P<reps>\\d+)x (?:(?P<on_mins>\\d+)min )?(?:(?P<on_secs>\\d+)sec )?'
    r'@ (?:(?P<on_cadence>\\d+)rpm, )?(?P<on_power>\\d+)% FTP,'
    r'(?:(?P<off_mins>\\d+)min )?(?:(?P<off_secs>\\d+)sec )?'
    r'@ (?:(?P<off_cadence>\\d+)rpm, )?(?P<off_power>\\d+)% FTP'
)

FREE_RIDE_RE = re.compile(
    r'(?:(?P<mins>\\d+)min )?(?:(?P<secs>\\d+)sec )?free ride'
)


def calc_duration(mins, secs):
    d = 0
    if secs:
        d += int(secs)
    if mins:
        d += int(mins) * 60
    return d


def ramp(match, pos):
    label = {
        StepPosition.FIRST: "Warmup",
        StepPosition.LAST: "Cooldown"
    }.get(pos, "Ramp")
    duration = calc_duration(match["mins"], match["secs"])
    cadence = match.get("cadence")
    low_power = match["low"] / 100.0
    high_power = match["high"] / 100.0
    node = etree.Element(label)
    node.set("Duration", str(duration))
    node.set("PowerLow", str(low_power))
    node.set("PowerHigh", str(high_power))
    node.set("pace", str(0))
    if cadence:
        node.set("Cadence", str(cadence))
    return node


def steady(match, pos):
    duration = calc_duration(match["mins"], match["secs"])
    cadence = match.get("cadence")
    power = match["power"] / 100.0
    node = E.SteadyState(Duration=str(duration), Power=str(power), pace=str(0))
    if cadence:
        node.set("Cadence", str(cadence))
    return node


def intervals(match, pos):
    on_duration = calc_duration(match["on_mins"], match["on_secs"])
    off_duration = calc_duration(match["off_mins"], match["off_secs"])
    reps = match["reps"]
    on_power = match["on_power"] / 100.0
    off_power = match["off_power"] / 100.0
    on_cadence = match.get("on_cadence")
    off_cadence = match.get("off_cadence")
    node = E.IntervalsT(
        Repeat=str(reps),
        OnDuration=str(on_duration),
        OffDuration=str(off_duration),
        OnPower=str(on_power),
        OffPower=str(off_power),
        pace=str(0),
    )
    if on_cadence and off_cadence:
        node.set("Cadence", str(on_cadence))
        node.set("CadenceResting", str(off_cadence))
    return node


def free_ride(match, pos):
    duration = calc_duration(match["mins"], match["secs"])
    return E.FreeRide(Duration=str(duration), FlatRoad=str(0))


BLOCKS = [
    (RAMP_RE, ramp),
    (STEADY_RE, steady),
    (INTERVALS_RE, intervals),
    (FREE_RIDE_RE, free_ride),
]


def parse_workout_step(step_text, pos):
    """Parse a single workout step from text"""
    for regex, func in BLOCKS:
        match = regex.match(step_text.strip())
        if match:
            match_int = {
                k: int(v) if v else None for k, v in match.groupdict().items()
            }
            return func(match_int, pos)
    return None


def create_zwo_xml(name, description, step_texts):
    """Create ZWO XML from workout data"""
    root = etree.Element("workout_file")
    
    author_node = etree.Element("author")
    author_node.text = "Zwift"
    root.append(author_node)
    
    name_node = etree.Element("name")
    name_node.text = name
    root.append(name_node)
    
    desc_node = etree.Element("description")
    desc_node.text = description
    root.append(desc_node)
    
    sport_node = etree.Element("sportType")
    sport_node.text = "bike"
    root.append(sport_node)
    
    root.append(etree.Element("tags"))
    
    workout = etree.Element("workout")
    
    for i, step_text in enumerate(step_texts):
        if i == 0:
            pos = StepPosition.FIRST
        elif i == len(step_texts) - 1:
            pos = StepPosition.LAST
        else:
            pos = StepPosition.MIDDLE
        
        step = parse_workout_step(step_text, pos)
        if step is not None:
            workout.append(step)
    
    if len(workout) == 0:
        return None
    
    root.append(workout)
    etree.indent(root, space="  ")
    
    return etree.tostring(root, pretty_print=True, encoding="unicode")


def scrape_collection_page(url, delay=1.5):
    """Scrape a workout collection page and extract all workouts"""
    print(f"Scraping collection: {url}")
    time.sleep(delay)
    
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    tree = lhtml.fromstring(response.content)
    
    workouts = []
    
    # Find all workout blocks
    # Each workout has a title and workout steps listed as text
    workout_sections = tree.xpath('//div[contains(@class, "panel")]')
    
    for section in workout_sections:
        # Try to extract workout name
        name_nodes = section.xpath('.//h3/text()')
        if not name_nodes:
            continue
        
        name = name_nodes[0].strip()
        if not name or name in ['Workouts', 'Week']:
            continue
        
        # Extract description
        desc_nodes = section.xpath('.//p[contains(@class, "description")]/text()')
        description = desc_nodes[0].strip() if desc_nodes else ''
        
        # Extract workout steps (lines with FTP %)
        step_nodes = section.xpath('.//div[contains(@class, "workoutlist")]//text()')
        step_texts = [s.strip() for s in step_nodes if s.strip() and ('FTP' in s or 'free ride' in s)]
        
        if step_texts:
            workouts.append({
                'name': name,
                'description': description,
                'steps': step_texts
            })
    
    return workouts


def main():
    parser = argparse.ArgumentParser(description='Scrape Zwift workouts from whatsonzwift.com')
    parser.add_argument('--db', default='../data/workout_profiles.db', help='Database path')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between requests (seconds)')
    parser.add_argument('--limit', type=int, help='Limit number of workouts to import')
    parser.add_argument('--collection', help='Specific collection URL to scrape')
    
    args = parser.parse_args()
    
    # Resolve database path
    script_dir = Path(__file__).parent
    db_path = (script_dir / args.db).resolve()
    
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return
    
    # Popular collections to scrape
    collections = [
        "https://whatsonzwift.com/workouts/build-me-up",
        "https://whatsonzwift.com/workouts/ftp-builder",
        "https://whatsonzwift.com/workouts/active-offseason",
    ]
    
    if args.collection:
        collections = [args.collection]
    
    # Scrape workouts
    imported_count = 0
    failed_count = 0
    skipped_count = 0
    
    for collection_url in collections:
        try:
            workouts = scrape_collection_page(collection_url, args.delay)
            print(f"Found {len(workouts)} workouts in collection\n")
            
            for workout in workouts:
                if args.limit and imported_count >= args.limit:
                    print(f"\nReached limit of {args.limit} imports")
                    break
                
                try:
                    print(f"Processing: {workout['name'][:50]}...", end=' ')
                    
                    # Create ZWO XML
                    zwo_xml = create_zwo_xml(
                        workout['name'],
                        workout['description'],
                        workout['steps']
                    )
                    
                    if not zwo_xml:
                        print("⚠️  No valid steps")
                        skipped_count += 1
                        continue
                    
                    # Save to temp file and import
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.zwo', delete=False) as f:
                        f.write(zwo_xml)
                        temp_path = f.name
                    
                    try:
                        if import_zwo_to_db(temp_path, db_path):
                            imported_count += 1
                            print("✅")
                        else:
                            skipped_count += 1
                            print("⚠️  Duplicate")
                    finally:
                        Path(temp_path).unlink()
                    
                except Exception as e:
                    failed_count += 1
                    print(f"❌ {str(e)[:50]}")
        
        except Exception as e:
            print(f"❌ Failed to scrape collection {collection_url}: {e}")
    
    print(f"\n{'='*60}")
    print(f"✅ Imported: {imported_count}")
    print(f"⚠️  Skipped (duplicates/invalid): {skipped_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
