# Workout Module Management Scripts

This directory contains utility scripts for managing workout modules and analyzing usage patterns.

## Scripts

### 1. Generate Module Variations

**Script:** `generate_module_variations.py`

Automatically creates multiple variations of warmup, cooldown, and rest modules to increase workout variety.

**Usage:**

```bash
# Generate all types of modules
python scripts/generate_module_variations.py --all

# Generate only specific types
python scripts/generate_module_variations.py --warmup
python scripts/generate_module_variations.py --cooldown
python scripts/generate_module_variations.py --rest

# Preview what would be created (dry run)
python scripts/generate_module_variations.py --all --dry-run
```

**Options:**
- `--all`: Generate all module types (warmup, cooldown, rest)
- `--warmup`: Generate only warmup modules
- `--cooldown`: Generate only cooldown modules
- `--rest`: Generate only rest modules
- `--dry-run`: Show what would be created without actually creating files

**What it generates:**

**Warmup modules (12 variations):**
- Progressive ramps: 5, 8, 12, 15, 20 minutes
- Stepped warmups: 10, 15, 20 minutes
- Warmup with openers: 12, 15 minutes
- Quick warmup: 5 minutes
- Race prep warmup: 25 minutes

**Cooldown modules (13 variations):**
- Fade out: 5, 8, 10, 12, 15, 20 minutes
- Stepped cooldowns: 10, 15, 20 minutes
- Active recovery cooldown: 12 minutes
- Quick cooldown: 5 minutes
- Extended flush: 25 minutes
- Two-stage cooldown: 15 minutes

**Rest modules (22 variations):**
- Easy rest: 1, 2, 3, 4, 5 minutes
- Active recovery: 2, 3, 4, 5 minutes
- Very easy rest: 2, 3, 4, 5, 8, 10 minutes
- Short rest: 30s, 45s, 60s, 90s
- Graduated rest: 5 minutes
- Flush rest: 3, 5 minutes

**Benefits:**
- Instant variety: Add 47 new modules in seconds
- Covers all durations: From 30s short rest to 25min extended warmups
- Multiple intensity levels: Easy, moderate, active recovery options
- Smart patterns: Based on cycling training best practices

---

### 2. Import Workouts from Intervals.icu

**Script:** `import_intervals_workouts.py`

Fetches workout events from your Intervals.icu calendar and converts them to JSON workout modules.

**Usage:**

```bash
# Import workouts from last 90 days (max 20 workouts)
python scripts/import_intervals_workouts.py

# Import from last 180 days, limit to 50 workouts
python scripts/import_intervals_workouts.py --days 180 --limit 50

# Specify custom output directory
python scripts/import_intervals_workouts.py --output custom/path/to/modules
```

**Options:**
- `--days N`: Number of days to look back (default: 90)
- `--limit N`: Maximum workouts to import (default: 20)
- `--output PATH`: Output directory (default: src/data/workout_modules/main)

**Requirements:**
- Intervals.icu API credentials configured in `.env`
- Existing workout events in your Intervals.icu calendar

**What it does:**
1. Fetches workout events from Intervals.icu
2. Extracts the main workout segments (excludes warmup/cooldown)
3. Converts to JSON module format
4. Saves as `.json` files in the main modules directory
5. Skips duplicates and AI-generated workouts

---

### 3. View Module Usage Statistics

**Script:** `view_module_stats.py`

Displays usage statistics showing which workout modules are selected by the AI most/least frequently.

**Usage:**

```bash
# View full report (all categories)
python scripts/view_module_stats.py

# View statistics for a specific category
python scripts/view_module_stats.py --category main

# Show top 20 modules
python scripts/view_module_stats.py --limit 20

# Export statistics to JSON
python scripts/view_module_stats.py --export stats.json
```

**Options:**
- `--category TYPE`: Filter by category (warmup/main/rest/cooldown)
- `--limit N`: Number of top modules to show (default: 10)
- `--export FILE`: Export statistics to JSON file

**Output Example:**

```
============================================================
WORKOUT MODULE USAGE REPORT
============================================================

Total Selections: 45
Unique Modules Used: 23

Category Totals:
  Warmup           45
  Main             78
  Rest             33
  Cooldown         45

Top 10 Most Used Modules (Overall):
   1. ramp_standard                   45 times
   2. sst_10min                       12 times
   3. threshold_2x8                   10 times
   4. vo2_3x3                          8 times
   5. rest_short                       7 times
   ...
```

---

## Usage Statistics System

### How it works

Every time a workout is generated, the system automatically:

1. Records which modules were selected
2. Tracks the category (warmup/main/rest/cooldown)
3. Updates usage counts and last-used timestamps
4. Saves statistics to `data/module_usage_stats.json`

### Statistics File

**Location:** `data/module_usage_stats.json`

**Structure:**
```json
{
  "total_selections": 45,
  "modules": {
    "sst_10min": {
      "count": 12,
      "last_used": "2026-01-09T15:30:00"
    },
    ...
  },
  "by_category": {
    "main": {
      "sst_10min": 12,
      "threshold_2x8": 10,
      ...
    },
    ...
  },
  "last_updated": "2026-01-09T15:30:00"
}
```

### Benefits

- **Identify patterns**: See which modules the AI prefers
- **Ensure variety**: Find underused modules that should be selected more
- **Debug AI selection**: Understand if certain modules are never chosen
- **Optimize library**: Remove unused modules or add similar variations of popular ones

---

## Workflow: Adding More Workout Variety

### Step 1: Import from Intervals.icu

```bash
# Import your favorite workouts from Intervals.icu
python scripts/import_intervals_workouts.py --days 180 --limit 30
```

### Step 2: Generate workouts as normal

Use the main application to generate workouts. The system automatically tracks module usage.

### Step 3: Review statistics

```bash
# See which main modules are used most
python scripts/view_module_stats.py --category main

# Check if any modules are never used
python scripts/view_module_stats.py --export stats.json
```

### Step 4: Adjust your library

Based on the statistics:
- **High usage modules**: Create similar variations
- **Never used modules**: Investigate why (wrong duration? too intense?)
- **Balanced usage**: Your library has good variety!

---

## Tips

### Creating Manual Modules

You can manually create workout modules by adding JSON files to:
- `src/data/workout_modules/warmup/`
- `src/data/workout_modules/main/`
- `src/data/workout_modules/rest/`
- `src/data/workout_modules/cooldown/`

**Example module** (`src/data/workout_modules/main/custom_workout.json`):

```json
{
  "name": "Custom SST 2x10",
  "duration_minutes": 25,
  "type": "SweetSpot",
  "structure": [
    {
      "type": "steady",
      "power": 90,
      "duration_minutes": 10
    },
    {
      "type": "steady",
      "power": 50,
      "duration_minutes": 5
    },
    {
      "type": "steady",
      "power": 90,
      "duration_minutes": 10
    }
  ]
}
```

### Module Naming

- Use descriptive names: `threshold_3x8`, `vo2_short_5x2`, `endurance_20min`
- Use underscores, not spaces
- Keep filename under 50 characters
- Be consistent with naming patterns

### Testing New Modules

After adding modules:
1. Generate a workout
2. Check if new modules appear in statistics
3. If not appearing, check:
   - File is in correct directory
   - JSON syntax is valid
   - Module type/duration matches what AI looks for

---

## Troubleshooting

### Import script fails

**Error:** `Failed to load config`
- **Fix:** Ensure `.env` file has `INTERVALS_API_KEY` and `INTERVALS_ATHLETE_ID`

**Error:** `Failed to fetch workouts`
- **Fix:** Check API credentials, network connection, and Intervals.icu service status

### Statistics not updating

**Error:** Module selections not being recorded
- **Fix:** Check that `data/` directory is writable
- **Fix:** Look for errors in application logs

### Statistics file corrupted

**Error:** `Failed to load usage stats`
- **Fix:** Delete `data/module_usage_stats.json` and it will be recreated

---

## Advanced Usage

### Reset statistics

```bash
rm data/module_usage_stats.json
```

Statistics will be rebuilt from scratch as workouts are generated.

### Programmatic access

```python
from src.services.module_usage_tracker import get_tracker

tracker = get_tracker()

# Get stats for a module
stats = tracker.get_module_stats("sst_10min")
print(f"Used {stats['count']} times")

# Get least used modules (for variety)
least_used = tracker.get_least_used_modules(
    available_modules=["sst_10min", "threshold_2x8", "vo2_3x3"],
    category="main",
    limit=5
)
```

---

## Future Enhancements

Potential additions:
- Weight module selection toward least-used modules for variety
- Track module selection by TSB/form (e.g., which modules used when fresh vs fatigued)
- Import from TrainerRoad, Zwift, or other platforms
- Auto-generate variations of popular modules
- Suggest new module combinations based on patterns

---

For questions or issues, please refer to the main project documentation.
