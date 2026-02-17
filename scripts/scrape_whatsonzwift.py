#!/usr/bin/env python3
"""
WhatsonZwift.com Scraper
Scrapes cycling workouts from whatsonzwift.com and imports them into the DB.

Strategy: text-based extraction — scan all text nodes for "% FTP" / "free ride"
patterns, then validate with regex.  No reliance on fragile CSS class selectors.
"""

import re
import sys
import time
import sqlite3
import argparse
import tempfile
from pathlib import Path
from enum import Enum

import requests
from lxml import html as lhtml, etree
from lxml.builder import E

# ---------------------------------------------------------------------------
# Import helper
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent))
from import_zwo import import_zwo_to_db  # noqa: E402

BASE_URL = "https://whatsonzwift.com"
WORKOUTS_INDEX = f"{BASE_URL}/workouts/"

# Collections that are NOT cycling (skip these)
SKIP_SLUGS = {
    # Running
    "running", "run", "5k-training", "10k-training", "half-marathon",
    "marathon", "return-to-running", "3run-13-1", "3run-13-1-lite",
    "5k-recordbreaker", "5k-recordbreaker-lite", "cyclist-to-10k",
    "la-marathon-phase1", "la-marathon-phase2",
    "zwift-101-running", "zwift-201-running-5k",
    "zwift-academy-run-2020", "zwift-academy-run-2021", "zwift-academy-run-2023",
    "the-running-channel", "saucony-endorphin-series-2021",
    # Multisport / Triathlon
    "multisport", "triathlon", "multisport-mixer",
    "the-norseman", "olympic-tri-prep-plan", "team-sonic-triathlete",
    "zwift-academy-tri-2019", "zwift-academy-tri-2020",
    "zwift-academy-tri-2021", "zwift-academy-tri-2022",
    "tri247com-pro-workouts",
}


# ---------------------------------------------------------------------------
# Step position (for warmup / cooldown detection)
# ---------------------------------------------------------------------------
class StepPosition(Enum):
    FIRST = 0
    MIDDLE = 1
    LAST = 2


# ---------------------------------------------------------------------------
# Regex patterns (proven working from v1, with "hr" + "target X% FTP" support)
# ---------------------------------------------------------------------------
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
    r'@ (?:(?P<on_cadence>\d+)rpm, )?(?P<on_power>\d+)% FTP,\s*'
    r'(?:(?P<off_hours>\d+)hr )?(?:(?P<off_mins>\d+)min )?(?:(?P<off_secs>\d+)sec )?'
    r'@ (?:(?P<off_cadence>\d+)rpm, )?(?P<off_power>\d+)% FTP'
)

FREE_RIDE_RE = re.compile(
    r'(?:(?P<hours>\d+)hr )?(?:(?P<mins>\d+)min )?(?:(?P<secs>\d+)sec )?'
    r'(?:free ride|target \d+% FTP free ride)',
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Duration helper
# ---------------------------------------------------------------------------
def calc_duration(hours, mins, secs):
    """Calculate duration in seconds from optional h/m/s strings."""
    d = 0
    if secs:
        d += int(secs)
    if mins:
        d += int(mins) * 60
    if hours:
        d += int(hours) * 3600
    return d


# ---------------------------------------------------------------------------
# ZWO node builders
# ---------------------------------------------------------------------------
def build_ramp(m, pos):
    label = {StepPosition.FIRST: "Warmup", StepPosition.LAST: "Cooldown"}.get(pos, "Ramp")
    duration = calc_duration(m.get("hours"), m.get("mins"), m.get("secs"))
    node = etree.Element(label)
    node.set("Duration", str(duration))
    node.set("PowerLow", str(int(m["low"]) / 100.0))
    node.set("PowerHigh", str(int(m["high"]) / 100.0))
    node.set("pace", "0")
    if m.get("cadence"):
        node.set("Cadence", str(m["cadence"]))
    return node


def build_steady(m, pos):
    duration = calc_duration(m.get("hours"), m.get("mins"), m.get("secs"))
    node = E.SteadyState(
        Duration=str(duration), Power=str(int(m["power"]) / 100.0), pace="0"
    )
    if m.get("cadence"):
        node.set("Cadence", str(m["cadence"]))
    return node


def build_intervals(m, pos):
    on_dur = calc_duration(m.get("on_hours"), m.get("on_mins"), m.get("on_secs"))
    off_dur = calc_duration(m.get("off_hours"), m.get("off_mins"), m.get("off_secs"))
    node = E.IntervalsT(
        Repeat=str(int(m["reps"])),
        OnDuration=str(on_dur),
        OffDuration=str(off_dur),
        OnPower=str(int(m["on_power"]) / 100.0),
        OffPower=str(int(m["off_power"]) / 100.0),
        pace="0",
    )
    if m.get("on_cadence") and m.get("off_cadence"):
        node.set("Cadence", str(m["on_cadence"]))
        node.set("CadenceResting", str(m["off_cadence"]))
    return node


def build_free_ride(m, pos):
    duration = calc_duration(m.get("hours"), m.get("mins"), m.get("secs"))
    return E.FreeRide(Duration=str(duration), FlatRoad="0")


BLOCKS = [
    (INTERVALS_RE, build_intervals),   # must precede STEADY (both have "% FTP")
    (RAMP_RE, build_ramp),
    (STEADY_RE, build_steady),
    (FREE_RIDE_RE, build_free_ride),
]


def parse_step_text(text, pos):
    """Try each regex against *text*; return an lxml Element or None."""
    text = text.strip()
    for regex, func in BLOCKS:
        match = regex.match(text)
        if match:
            return func(match.groupdict(), pos)
    return None


# ---------------------------------------------------------------------------
# ZWO XML generation
# ---------------------------------------------------------------------------
def create_zwo_xml(name, description, step_texts):
    """Build a ZWO XML string from workout metadata + step text lines."""
    root = etree.Element("workout_file")

    for tag_name, value in [("author", "Zwift"), ("name", name),
                            ("description", description or ""),
                            ("sportType", "bike")]:
        el = etree.SubElement(root, tag_name)
        el.text = value

    etree.SubElement(root, "tags")
    workout_el = etree.SubElement(root, "workout")

    for i, text in enumerate(step_texts):
        if i == 0:
            pos = StepPosition.FIRST
        elif i == len(step_texts) - 1:
            pos = StepPosition.LAST
        else:
            pos = StepPosition.MIDDLE
        node = parse_step_text(text, pos)
        if node is not None:
            workout_el.append(node)

    if len(workout_el) == 0:
        return None

    etree.indent(root, space="  ")
    return etree.tostring(root, pretty_print=True, encoding="unicode")


# ---------------------------------------------------------------------------
# HTTP helper with retry
# ---------------------------------------------------------------------------
def fetch(url, delay=2.0, retries=3, verbose=False):
    """GET *url* with polite delay and retry on 429 / 5xx."""
    time.sleep(delay)
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, timeout=30, headers={
                "User-Agent": "ai-cycling-coach-scraper/1.0 (educational project)"
            })
            if resp.status_code == 429 or resp.status_code >= 500:
                wait = delay * (2 ** attempt)
                if verbose:
                    print(f"  Retry {attempt}/{retries} ({resp.status_code}), "
                          f"waiting {wait:.0f}s...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            if attempt == retries:
                raise
            if verbose:
                print(f"  Retry {attempt}/{retries}: {exc}")
            time.sleep(delay * (2 ** attempt))
    return None  # unreachable


# ---------------------------------------------------------------------------
# Collection discovery
# ---------------------------------------------------------------------------
def discover_collections(delay=2.0, verbose=False):
    """Fetch /workouts/ and return list of (slug, url) for cycling collections."""
    if verbose:
        print(f"Discovering collections from {WORKOUTS_INDEX} ...")
    resp = fetch(WORKOUTS_INDEX, delay=delay, verbose=verbose)
    tree = lhtml.fromstring(resp.content)

    links = tree.xpath('//a[contains(@href, "/workouts/")]/@href')
    seen = set()
    collections = []
    for href in links:
        # Normalise to absolute
        if href.startswith("/"):
            href = BASE_URL + href
        # Strip trailing slash & query
        href = href.split("?")[0].split("#")[0].rstrip("/")
        # Must be exactly /workouts/<slug>  (2-segment path after domain)
        parts = href.replace(BASE_URL, "").strip("/").split("/")
        if len(parts) != 2 or parts[0] != "workouts":
            continue
        slug = parts[1]
        if slug in seen or slug in SKIP_SLUGS:
            continue
        seen.add(slug)
        collections.append((slug, href))

    collections.sort(key=lambda x: x[0])
    return collections


# ---------------------------------------------------------------------------
# Workout extraction from a single workout page
# ---------------------------------------------------------------------------
def extract_step_texts(tree):
    """Extract workout step texts from a page.

    Primary: use div.textbar elements (each contains one step as text_content).
    Fallback: scan all text nodes for '% FTP' / 'free ride' patterns.
    """
    # --- Primary: div.textbar (whatsonzwift standard layout) ---
    textbars = tree.xpath('//div[contains(@class, "textbar")]')
    if textbars:
        steps = []
        seen = set()
        for tb in textbars:
            text = tb.text_content().strip()
            # Normalise whitespace (spans + br tags can leave gaps)
            text = re.sub(r'\s+', ' ', text)
            if text and text not in seen and ("% FTP" in text or "free ride" in text.lower()):
                seen.add(text)
                steps.append(text)
        if steps:
            return steps

    # --- Fallback: scan all text nodes ---
    candidates = []
    for node in tree.iter():
        if node.text:
            for line in node.text.splitlines():
                line = line.strip()
                if line and ("% FTP" in line or "free ride" in line.lower()):
                    candidates.append(line)
        if node.tail:
            for line in node.tail.splitlines():
                line = line.strip()
                if line and ("% FTP" in line or "free ride" in line.lower()):
                    candidates.append(line)

    # De-duplicate while preserving order
    seen = set()
    unique = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    return unique


def scrape_workout_page(url, delay=2.0, verbose=False):
    """Scrape a single workout page → (name, description, step_texts) or None."""
    resp = fetch(url, delay=delay, verbose=verbose)
    tree = lhtml.fromstring(resp.content)

    # Title: try several selectors
    title = None
    for xpath in [
        '//h1[contains(@class, "flaticon-bike")]/text()',
        '//h1/text()',
        '//title/text()',
    ]:
        nodes = tree.xpath(xpath)
        if nodes:
            title = nodes[0].strip()
            if title:
                break
    if not title:
        return None

    # Clean title coming from <title>
    if " | " in title:
        title = title.split(" | ")[0].strip()

    # Description
    desc_nodes = tree.xpath('//meta[@name="description"]/@content')
    description = desc_nodes[0].strip() if desc_nodes else ""

    step_texts = extract_step_texts(tree)
    if not step_texts:
        return None

    return title, description, step_texts


# ---------------------------------------------------------------------------
# Collection → workout URLs
# ---------------------------------------------------------------------------
def scrape_collection_urls(collection_url, delay=2.0, verbose=False):
    """Return list of individual workout page URLs from a collection page."""
    resp = fetch(collection_url, delay=delay, verbose=verbose)
    tree = lhtml.fromstring(resp.content)

    links = tree.xpath('//a[contains(@href, "/workouts/")]/@href')
    collection_slug = collection_url.rstrip("/").split("/")[-1]

    urls = []
    seen = set()
    for href in links:
        if href.startswith("/"):
            href = BASE_URL + href
        href = href.split("?")[0].split("#")[0].rstrip("/")
        parts = href.replace(BASE_URL, "").strip("/").split("/")
        # Individual workout: /workouts/<collection>/<workout-slug>
        if len(parts) == 3 and parts[0] == "workouts" and parts[1] == collection_slug:
            if href not in seen:
                seen.add(href)
                urls.append(href)
    return urls


# ---------------------------------------------------------------------------
# Resume helper
# ---------------------------------------------------------------------------
def get_imported_source_urls(db_path):
    """Return set of source_url values already in the DB."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT source_url FROM workout_profiles WHERE source_url IS NOT NULL")
    urls = {row[0] for row in cursor.fetchall()}
    conn.close()
    return urls


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------
def run_scraper(args):
    script_dir = Path(__file__).parent
    db_path = (script_dir / args.db).resolve()

    if not args.dry_run and not db_path.exists():
        print(f"Database not found: {db_path}")
        print("Run seed_profiles.py first to create the database.")
        return

    # --- List collections ---
    if args.list_collections:
        collections = discover_collections(delay=args.delay, verbose=args.verbose)
        print(f"Found {len(collections)} cycling collections:\n")
        for slug, url in collections:
            print(f"  {slug:<35s} {url}")
        return

    # --- Determine which collections to scrape ---
    if args.collection:
        slug = args.collection.strip("/").split("/")[-1]
        url = f"{BASE_URL}/workouts/{slug}"
        collections = [(slug, url)]
    else:
        collections = discover_collections(delay=args.delay, verbose=args.verbose)
        print(f"Discovered {len(collections)} cycling collections.\n")

    # --- Resume: load already-imported URLs ---
    imported_urls = set()
    if not args.no_resume and not args.dry_run:
        imported_urls = get_imported_source_urls(db_path)
        if imported_urls:
            print(f"Resume mode: {len(imported_urls)} workouts already imported.\n")

    # --- Scrape ---
    total_imported = 0
    total_skipped = 0
    total_failed = 0
    total_resume_skipped = 0

    for col_slug, col_url in collections:
        print(f"\n{'='*60}")
        print(f"Collection: {col_slug}")
        print(f"{'='*60}")

        try:
            workout_urls = scrape_collection_urls(col_url, delay=args.delay, verbose=args.verbose)
        except Exception as exc:
            print(f"  Failed to fetch collection: {exc}")
            total_failed += 1
            continue

        print(f"  Found {len(workout_urls)} workouts")

        for workout_url in workout_urls:
            if args.limit and total_imported >= args.limit:
                print(f"\nReached import limit ({args.limit}).")
                _print_summary(total_imported, total_skipped, total_failed, total_resume_skipped)
                return

            # Resume check
            if workout_url in imported_urls:
                total_resume_skipped += 1
                if args.verbose:
                    print(f"  [skip] {workout_url}")
                continue

            print(f"  Scraping: {workout_url} ... ", end="", flush=True)

            try:
                result = scrape_workout_page(workout_url, delay=args.delay, verbose=args.verbose)
            except Exception as exc:
                print(f"FAIL ({exc})")
                total_failed += 1
                continue

            if result is None:
                print("no steps found")
                total_skipped += 1
                continue

            raw_title, description, step_texts = result

            # Use URL slug for unique naming (avoids "Day 1" collisions across weeks)
            url_slug = workout_url.rstrip("/").split("/")[-1]
            workout_label = url_slug.replace("-", " ").title()
            prefixed_name = f"{col_slug.replace('-', ' ').title()} - {workout_label}"

            if args.verbose:
                print(f"OK ({len(step_texts)} steps)")
                for st in step_texts:
                    print(f"    {st}")
            else:
                print(f"OK ({len(step_texts)} steps)")

            # Build ZWO
            zwo_xml = create_zwo_xml(prefixed_name, description, step_texts)
            if not zwo_xml:
                print(f"    No valid ZWO steps generated")
                total_skipped += 1
                continue

            if args.dry_run:
                print(f"    [dry-run] Would import: {prefixed_name}")
                total_imported += 1
                continue

            # Write temp file and import
            with tempfile.NamedTemporaryFile(mode="w", suffix=".zwo", delete=False) as f:
                f.write(zwo_xml)
                temp_path = f.name

            try:
                ok = import_zwo_to_db(
                    temp_path, db_path,
                    source="whatsonzwift",
                    source_url=workout_url,
                )
                if ok:
                    total_imported += 1
                else:
                    total_skipped += 1
            except Exception as exc:
                print(f"    Import error: {exc}")
                total_failed += 1
            finally:
                Path(temp_path).unlink(missing_ok=True)

    _print_summary(total_imported, total_skipped, total_failed, total_resume_skipped)


def _print_summary(imported, skipped, failed, resume_skipped):
    print(f"\n{'='*60}")
    print(f"  Imported:        {imported}")
    print(f"  Skipped (dup):   {skipped}")
    print(f"  Skipped (resume):{resume_skipped}")
    print(f"  Failed:          {failed}")
    print(f"{'='*60}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Scrape cycling workouts from whatsonzwift.com"
    )
    parser.add_argument("--db", default="../data/workout_profiles.db",
                        help="Path to SQLite database (default: ../data/workout_profiles.db)")
    parser.add_argument("--list-collections", action="store_true",
                        help="List all cycling collections and exit")
    parser.add_argument("--collection",
                        help="Scrape a specific collection only (slug or full URL)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Scrape but do not write to DB")
    parser.add_argument("--limit", type=int, default=0,
                        help="Max number of workouts to import (0 = unlimited)")
    parser.add_argument("--delay", type=float, default=2.0,
                        help="Seconds between HTTP requests (default: 2.0)")
    parser.add_argument("--no-resume", action="store_true",
                        help="Ignore already-imported workouts and re-scrape")
    parser.add_argument("--verbose", action="store_true",
                        help="Print detailed output")
    args = parser.parse_args()
    run_scraper(args)


if __name__ == "__main__":
    main()
