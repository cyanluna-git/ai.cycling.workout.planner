# Zwift Workout Import Summary

**Date**: 2026-02-14  
**Task**: Mass Import Zwift Workouts to Profile DB

## Results

### Phase 1: GitHub ZWO Files ✅ COMPLETED

**Source**: https://github.com/bdcheung/zwift_workouts  
**Files Found**: 78 .zwo files  
**Successfully Imported**: 26 workouts  
**Duplicates Skipped**: 34  
**Failed (malformed XML)**: 24  

### Database Growth

- **Before**: 100 profiles (all custom)
- **After**: 126 profiles (100 custom + 26 zwift)
- **Growth**: +26% increase

### Category Distribution (Final)

| Category   | Count |
|------------|-------|
| Threshold  | 27    |
| Mixed      | 14    |
| Endurance  | 12    |
| VO2max     | 12    |
| Sweetspot  | 11    |
| Climbing   | 10    |
| Race Sim   | 10    |
| Recovery   | 9     |
| Sprint     | 8     |
| Tempo      | 8     |
| Anaerobic  | 5     |

## Code Changes

### 1. Fixed `import_zwo.py`

**Issue**: Script couldn't handle float values in Duration/OnDuration/OffDuration/Repeat attributes  
**Fix**: Wrapped `elem.get()` calls with `float()` before converting to `int()`  
**Pattern**: `int(elem.get('Duration', '600'))` → `int(float(elem.get('Duration', '600')))`  

### 2. Added Error Handling

Added try-except blocks in batch import loop to:  
- Continue on malformed XML files  
- Log failed imports with error messages  
- Report success/failure counts  

### 3. Created Scraper Scripts

**Files**:  
- `scripts/scrape_whatsonzwift.py` (v1 - URL-based approach)
- `scripts/scrape_whatsonzwift_v2.py` (v2 - collection page parsing)

Both scripts include:
- Respectful rate limiting (1.5-2s delays)
- Wozzwo-style regex parsing
- ZWO XML generation
- Direct database import integration

## Phase 2: whatsonzwift.com ⚠️ INCOMPLETE

**Status**: Infrastructure created but not fully functional  
**Reason**: HTML structure more complex than expected

### Challenges

1. Workout data is embedded in collection pages (not individual URLs)
2. XPath selectors need refinement for panel structure
3. ~3,100 workouts available but require careful parsing to avoid breaking ToS

### Next Steps (Future Work)

1. **Debug HTML Structure**:  
   - Inspect actual DOM using browser dev tools
   - Update XPath selectors in scraper v2
   - Test with `lxml.etree` debug output

2. **Alternative Approach**:  
   - Check if whatsonzwift.com has an API
   - Look for data files/JSON endpoints
   - Use browser automation (Playwright/Selenium) if needed

3. **Respect ToS**:  
   - Contact whatsonzwift.com for permission
   - Implement stricter rate limiting (3-5s delays)
   - Cache results to avoid re-scraping

## Sample Imported Workouts

```
[101] Plus30                    | mixed      | 61min | TSS: 93.7
[102] ZeCanon Intervals         | mixed      | 39min | TSS: 58.2
[103] FasCat                    | mixed      | 42min | TSS: 63.7
[106] Sufferfest - Violator     | threshold  | 67min | TSS: 113.2
[107] Sufferfest - The Rookie   | threshold  | 54min | TSS: 90.2
```

## Files Modified/Created

- **Modified**: `scripts/import_zwo.py` (float handling + error handling)
- **Created**: `scripts/scrape_whatsonzwift.py`
- **Created**: `scripts/scrape_whatsonzwift_v2.py`
- **Updated**: `data/workout_profiles.db` (+26 profiles)

## Recommendations

1. **Use the existing 126 profiles** — good variety across all categories
2. **GitHub repo is a reliable source** — clean ZWO files, easy to import
3. **For more growth**, focus on:
   - Finding more GitHub repos with .zwo files
   - TrainingPeaks workout library
   - Zwift's official legacy workout ZIP file (mentioned on forums)
   - User-contributed custom workout sites

## Commands for Future Reference

```bash
# Import single .zwo file
python3 scripts/import_zwo.py <file.zwo>

# Import directory of .zwo files
python3 scripts/import_zwo.py /path/to/zwo/files/

# Check database stats
python3 -c "import sqlite3; conn = sqlite3.connect('data/workout_profiles.db'); print(f'Total: {conn.execute(\"SELECT COUNT(*) FROM workout_profiles\").fetchone()[0]}'); conn.close()"
```

---

**Conclusion**: Phase 1 successfully completed with 26% database growth. Phase 2 infrastructure in place for future expansion once HTML parsing is refined.
