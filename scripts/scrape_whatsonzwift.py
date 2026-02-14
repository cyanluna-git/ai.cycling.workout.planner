#!/usr/bin/env python3
"""
WhatsonZwift.com Scraper
Scrapes workouts from whatsonzwift.com and imports them into the database
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


# Regex patterns - FIXED: removed double-escapes and added "hr" support
RAMP_RE = re.compile(
    r'(?:(?P<hours>\d+)hr )?(?:(?P<mins>\d+)min )?(?:(?P<secs>\d+)sec )?'
    r'(?:@ (?P<cadence>\d+)rpm, )?from (?P<low>\d+) to (?P<high>\d+)% FTP'
)

STEADY_RE = re.compile(
    r'(?:(?P<hours>\d+)hr )?(?:(?P<mins>\d+)min )?(?:(?P<secs>\d+)sec )?'
    r'@ (?:(?P<cadence>\d+)rpm, )?(?P<power>\d+)% FTP'
)

INTERVALS_RE = re.compile(
    r'(?P<reps>\d+)x (?:(?P<on_hours>\d+)hr )?(?:(?P<on_mins>\d+)min )?(?:(?P<on_secs>\d+)sec )?'
    r'@ (?:(?P<on_cadence>\d+)rpm, )?(?P<on_power>\d+)% FTP, ?'
    r'(?:(?P<off_hours>\d+)hr )?(?:(?P<off_mins>\d+)min )?(?:(?P<off_secs>\d+)sec )?'
    r'@ (?:(?P<off_cadence>\d+)rpm, )?(?P<off_power>\d+)% FTP'
)

FREE_RIDE_RE = re.compile(
    r'(?:(?P<hours>\d+)hr )?(?:(?P<mins>\d+)min )?(?:(?P<secs>\d+)sec )?free ride'
)


def calc_duration(hours, mins, secs):
    """Calculate duration in seconds from hours, mins, secs"""
    d = 0
    if secs:
        d += int(secs)
    if mins:
        d += int(mins) * 60
    if hours:
        d += int(hours) * 3600
    return d


def ramp(match, pos):
    label = {
        StepPosition.FIRST: "Warmup",
        StepPosition.LAST: "Cooldown"
    }.get(pos, "Ramp")
    duration = calc_duration(match.get("hours"), match.get("mins"), match.get("secs"))
    cadence = match.get("cadence")
    low_power = int(match["low"]) / 100.0
    high_power = int(match["high"]) / 100.0
    node = etree.Element(label)
    node.set("Duration", str(duration))
    node.set("PowerLow", str(low_power))
    node.set("PowerHigh", str(high_power))
    node.set("pace", str(0))
    if cadence:
        node.set("Cadence", str(cadence))
    return node


def steady(match, pos):
    duration = calc_duration(match.get("hours"), match.get("mins"), match.get("secs"))
    cadence = match.get("cadence")
    power = int(match["power"]) / 100.0
    node = E.SteadyState(Duration=str(duration), Power=str(power), pace=str(0))
    if cadence:
        node.set("Cadence", str(cadence))
    return node


def intervals(match, pos):
    on_duration = calc_duration(match.get("on_hours"), match.get("on_mins"), match.get("on_secs"))
    off_duration = calc_duration(match.get("off_hours"), match.get("off_mins"), match.get("off_secs"))
    reps = int(match["reps"])
    on_power = int(match["on_power"]) / 100.0
    off_power = int(match["off_power"]) / 100.0
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
    duration = calc_duration(match.get("hours"), match.get("mins"), match.get("secs"))
    return E.FreeRide(Duration=str(duration), FlatRoad=str(0))


BLOCKS = [
    (RAMP_RE, ramp),
    (STEADY_RE, steady),
    (INTERVALS_RE, intervals),
    (FREE_RIDE_RE, free_ride),
]


def parse_workout_step(step, pos):
    """Parse a single workout step div"""
    text = step.text_content().strip()
    for regex, func in BLOCKS:
        match = regex.match(text)
        if match:
            return func(match.groupdict(), pos)
    raise RuntimeError(f"Couldn't parse step: {text}")


def scrape_workout_page(url, delay=1.5):
    """Scrape a single workout page and return ZWO XML"""
    print(f"  Fetching {url}...", end=' ')
    time.sleep(delay)  # Respectful delay
    
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    tree = lhtml.fromstring(response.content)
    
    # Extract workout metadata - FIXED selectors
    # Title is in h1 with class "glyph-icon flaticon-bike"
    title_nodes = tree.xpath('//h1[contains(@class, "flaticon-bike")]/text()')
    
    # Description is in a <p> tag after the zone distribution
    desc_nodes = tree.xpath('//section//p[not(ancestor::div[contains(@class, "flex")])]/text()')
    
    if not title_nodes:
        print("❌ No title found")
        return None
    
    title = title_nodes[0].strip()
    # Clean up description - join multiple text nodes
    description = ' '.join([d.strip() for d in desc_nodes if d.strip()]) if desc_nodes else ''
    
    # Parse workout steps - FIXED: use div.textbar instead of div.workoutlist
    steps = tree.xpath('//div[contains(@class, "textbar")]')
    
    if not steps:
        print("❌ No workout steps found")
        return None
    
    # Build ZWO XML
    root = etree.Element("workout_file")
    
    author_node = etree.Element("author")
    author_node.text = "Zwift"
    root.append(author_node)
    
    name_node = etree.Element("name")
    name_node.text = title
    root.append(name_node)
    
    desc_node = etree.Element("description")
    desc_node.text = description
    root.append(desc_node)
    
    sport_node = etree.Element("sportType")
    sport_node.text = "bike"
    root.append(sport_node)
    
    root.append(etree.Element("tags"))
    
    workout = etree.Element("workout")
    
    for i, step_div in enumerate(steps):
        if i == 0:
            pos = StepPosition.FIRST
        elif i == len(steps) - 1:
            pos = StepPosition.LAST
        else:
            pos = StepPosition.MIDDLE
        try:
            workout.append(parse_workout_step(step_div, pos))
        except RuntimeError as e:
            print(f"⚠️  {e}")
            continue
    
    root.append(workout)
    etree.indent(root, space="  ")
    
    print("✅")
    return etree.tostring(root, pretty_print=True, encoding="unicode")


def scrape_collection_page(url, delay=1.5):
    """Scrape a workout collection page and return list of workout URLs"""
    print(f"Scraping collection: {url}")
    time.sleep(delay)
    
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    tree = lhtml.fromstring(response.content)
    
    # Find workout links
    workout_links = tree.xpath('//a[contains(@href, "/workouts/")]/@href')
    
    # Filter to unique full URLs
    base_url = "https://whatsonzwift.com"
    workout_urls = set()
    for link in workout_links:
        if link.startswith('/'):
            full_url = base_url + link
        else:
            full_url = link
        
        # Only include individual workout pages (3 parts: /workouts/collection/workout-name)
        parts = full_url.split('?')[0].split('#')[0].split('/')
        if parts.count('workouts') == 1 and len(parts) >= 5:
            workout_urls.add(full_url.split('?')[0].split('#')[0])
    
    return list(workout_urls)


def main():
    parser = argparse.ArgumentParser(description='Scrape Zwift workouts from whatsonzwift.com')
    parser.add_argument('--db', default='../data/workout_profiles.db', help='Database path')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between requests (seconds)')
    parser.add_argument('--limit', type=int, help='Limit number of workouts to import')
    parser.add_argument('--collection', help='Specific collection URL to scrape')
    parser.add_argument('--list-collections', action='store_true', help='List available collections')
    
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
        "https://whatsonzwift.com/workouts/climbing",
        "https://whatsonzwift.com/workouts/criterium-racing",
        "https://whatsonzwift.com/workouts/time-trial",
        "https://whatsonzwift.com/workouts/endurance",
        "https://whatsonzwift.com/workouts/recovery",
        "https://whatsonzwift.com/workouts/tempo",
        "https://whatsonzwift.com/workouts/sweetspot",
        "https://whatsonzwift.com/workouts/vo2max",
        "https://whatsonzwift.com/workouts/sprint",
        "https://whatsonzwift.com/workouts/one-of-a-kind",
        "https://whatsonzwift.com/workouts/gravel",
        "https://whatsonzwift.com/workouts/gravity-racing",
    ]
    
    if args.list_collections:
        print("Available collections:")
        for col in collections:
            print(f"  - {col}")
        return
    
    if args.collection:
        collections = [args.collection]
    
    # Scrape workouts
    imported_count = 0
    failed_count = 0
    skipped_count = 0
    
    for collection_url in collections:
        try:
            workout_urls = scrape_collection_page(collection_url, args.delay)
            print(f"Found {len(workout_urls)} workouts in collection\n")
            
            for i, workout_url in enumerate(workout_urls):
                if args.limit and imported_count >= args.limit:
                    print(f"\nReached limit of {args.limit} imports")
                    break
                
                try:
                    # Scrape workout and convert to ZWO
                    zwo_xml = scrape_workout_page(workout_url, args.delay)
                    if not zwo_xml:
                        skipped_count += 1
                        continue
                    
                    # Save to temp file and import
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.zwo', delete=False) as f:
                        f.write(zwo_xml)
                        temp_path = f.name
                    
                    try:
                        if import_zwo_to_db(temp_path, db_path):
                            imported_count += 1
                        else:
                            skipped_count += 1
                    finally:
                        Path(temp_path).unlink()
                    
                except Exception as e:
                    failed_count += 1
                    print(f"  ❌ Failed: {str(e)[:100]}")
                
        except Exception as e:
            print(f"❌ Failed to scrape collection {collection_url}: {e}")
    
    print(f"\n{'='*60}")
    print(f"✅ Imported: {imported_count}")
    print(f"⚠️  Skipped (duplicates): {skipped_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
