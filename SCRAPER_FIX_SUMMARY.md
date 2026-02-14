# WhatsonZwift.com Scraper - Fix & Import Summary

**Date**: 2026-02-14
**Status**: ✅ COMPLETED

## Critical Bugs Fixed

### 1. Double-Escaped Regex Patterns
**Problem**: All regex patterns had double-escaped backslashes (`\\\\d+` instead of `\\d+`)
**Impact**: Patterns would never match actual workout text
**Fix**: Removed double-escapes in all patterns (RAMP_RE, STEADY_RE, INTERVALS_RE, FREE_RIDE_RE)

### 2. Missing "hr" Duration Support
**Problem**: Regex only handled "min" and "sec", not "hr" (e.g., "1hr 30min")
**Impact**: Workouts with hour-based durations would fail to parse
**Fix**: Added `(?P<hours>\\d+)hr )?` to all duration patterns and updated calc_duration()

### 3. Incorrect XPath Selectors
**Problem**: Selectors didn't match actual HTML structure
- Title: Expected `h4.flaticon-bike`, actual is `h1.flaticon-bike`
- Steps: Expected `div.workoutlist > div`, actual is `div.textbar`
- Description: Needed better extraction from section/p tags
**Fix**: Updated all XPath selectors to match current HTML

## Testing & Validation

### Regex Pattern Tests
✅ `10min from 70 to 75% FTP` → RAMP matched
✅ `1hr 30min @ 95rpm, 73% FTP` → STEADY matched  
✅ `4x 4min @ 100rpm, 105% FTP, 4min @ 85rpm, 75% FTP` → INTERVALS matched
✅ `10min from 75 to 70% FTP` → RAMP matched

### Scraper Test Run
- Collection: active-offseason (limit 3)
- Result: 3 workouts successfully imported
- ZWO XML: Validated and correct
- Database: Profiles inserted correctly (IDs 127-129)

### Full Import Results
- **Previous profiles**: 126
- **Newly imported**: 32
- **Total profiles**: 158
- **Collections processed**: 15 (expanded from 8)

### Category Distribution (Final)
```
threshold      : 32
vo2max         : 31
mixed          : 19
endurance      : 13
sweetspot      : 12
climbing       : 10
race_sim       : 10
recovery       :  9
sprint         :  9
tempo          :  8
anaerobic      :  5
```

## Files Changed

### Modified
- `scripts/scrape_whatsonzwift.py` (committed to main branch)
  * Fixed regex patterns
  * Added hr duration support
  * Updated XPath selectors
  * Expanded workout collections (8 → 15)
  * Improved collection URL filtering

### Not Committed (Intentional)
- `data/workout_profiles.db` (excluded in .gitignore)
  * Contains 158 workout profiles
  * 32 new imports from whatsonzwift.com
  * Database should be backed up separately

## Git Status

```
Commit: 881dfa2
Branch: main
Status: Ahead of origin/main by 2 commits
Message: "Fix whatsonzwift.com scraper: regex patterns, XPath selectors, and hr duration support"
```

## Sample Imported Workouts

| ID  | Name                      | Category   | Duration | TSS   |
|-----|---------------------------|------------|----------|-------|
| 158 | Thew                      | mixed      | 60min    | 84.0  |
| 157 | Uphill Battle             | vo2max     | 60min    | 78.1  |
| 156 | Devedeset                 | vo2max     | 60min    | 62.3  |
| 155 | #8                        | vo2max     | 60min    | 65.8  |
| 154 | Alpha                     | vo2max     | 30min    | 30.2  |
| 153 | Tenacity                  | vo2max     | 120min   | 150.7 |
| 152 | Melange                   | vo2max     | 90min    | 93.3  |
| 151 | Ham Sandwich              | vo2max     | 62min    | 84.9  |
| 150 | SST (Short)               | threshold  | 50min    | 65.8  |
| 149 | Serrated                  | vo2max     | 90min    | 123.7 |

## Workout Collections (15 Total)

1. build-me-up
2. ftp-builder
3. active-offseason
4. climbing
5. criterium-racing
6. time-trial
7. endurance
8. recovery
9. tempo
10. sweetspot
11. vo2max
12. sprint
13. one-of-a-kind
14. gravel
15. gravity-racing

## Recommendations

1. **Database Backup**: Create regular backups of `data/workout_profiles.db`
2. **Full Scrape**: Run periodic full scrapes to capture new Zwift workouts
3. **Monitoring**: Check for HTML structure changes on whatsonzwift.com
4. **Delay**: Keep 2-second delay between requests to be respectful
5. **Testing**: Before major scrapes, test with `--limit 5` on one collection

## Usage Examples

```bash
# Test with limit
cd scripts
source ../.venv/bin/activate
python3 scrape_whatsonzwift.py --collection https://whatsonzwift.com/workouts/ftp-builder --limit 5

# List collections
python3 scrape_whatsonzwift.py --list-collections

# Full scrape with custom delay
python3 scrape_whatsonzwift.py --delay 2.5

# Single collection, no limit
python3 scrape_whatsonzwift.py --collection https://whatsonzwift.com/workouts/climbing
```

---

**Task completed successfully** ✅
