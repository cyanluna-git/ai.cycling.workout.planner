# Fix: NaN Display in Workout Steps (Profile DB Intervals)

**Date**: 2026-02-14  
**Commit**: d1d7a08  
**Status**: ✅ Fixed, tested, and deployed

---

## Problem

When workouts from Profile DB contained `intervals` type steps (with `repeat`, `on_sec`, `off_sec`), the frontend displayed "NaNm" for some steps:

```
Main Set
- NaNm          ← BUG
- 5m 50% (126w)
- NaNm          ← BUG  
- 5m 50% (126w)
- NaNm          ← BUG
```

Additionally, power values were incorrectly calculated (e.g., 118% FTP → 47% FTP).

---

## Root Causes

### 1. Frontend: Accessing `duration` Before Repeat Check

**File**: `frontend/src/lib/format-workout-steps.ts`  
**Line**: 34 (before fix)

```typescript
function formatStepText(step: WorkoutStep, ftp: number): FormattedStep {
    const duration_min = Math.round(step.duration / 60);  // ← runs BEFORE repeat check
    
    // ... later (line 65)
    if (step.repeat && step.steps) { ... }
}
```

**Issue**: Repeat blocks don't have a `duration` property (their duration is calculated from nested steps). Accessing `step.duration` returns `undefined`, and `Math.round(undefined / 60)` = `NaN`.

### 2. Backend: Incorrect Power Conversion

**Files**: `api/routers/plans.py`, `src/services/workout_generator.py`

**Before**:
```python
on_s = {
    "power": {
        "value": round(step.get("on_power", 0) * 100 / ftp)  # ← WRONG
    }
}
```

**Issue**: Seed profiles store power as percentages (e.g., `on_power: 118` = 118% FTP). The conversion multiplied this by 100 and divided by FTP:
- Input: `on_power: 118`, `ftp: 250`
- Calculation: `118 * 100 / 250 = 47`
- Result: **47% FTP** (should be **118% FTP**)

This made VO2max intervals appear as easy endurance efforts.

---

## Solution

### Frontend Fix

**File**: `frontend/src/lib/format-workout-steps.ts`

**Change**: Move repeat block check to the **top** of `formatStepText()`, before any `step.duration` access:

```typescript
function formatStepText(step: WorkoutStep, ftp: number): FormattedStep {
    // Handle repeat blocks FIRST (they don't have duration)
    if (step.repeat && step.steps) {
        const nestedTexts = step.steps.map(s => formatStepText(s, ftp).text);
        const nestedStr = nestedTexts.join(' / ');
        // ... calculate color from max power
        return {
            text: `${step.repeat}x (${nestedStr})`,
            color
        };
    }

    const duration_min = Math.round(step.duration / 60);  // ← NOW safe
    // ... rest of function
}
```

### Backend Fix

**Files**: `api/routers/plans.py`, `src/services/workout_generator.py`

**Change**: Remove the incorrect `* 100 / ftp` multiplication. Seed profiles already store power as percentages:

```python
# BEFORE (WRONG)
round(step.get("on_power", 0) * 100 / ftp) if ftp else 0

# AFTER (CORRECT)
round(step.get("on_power", 0))
```

Applied to all power conversions:
- `start_power`, `end_power` (ramps)
- `power` (steady state)
- `on_power`, `off_power` (intervals)

**Fixed in both conversion paths**:
1. `WorkoutGenerator._convert_profile_steps_to_frontend_format()` (daily workout generation)
2. `plans.py` `get_current_weekly_plan()` (weekly plan retrieval)

---

## Validation

### Tests
```bash
python -m pytest tests/ -x -q
# Result: 162 passed, 1 skipped, 1 warning in 1.05s
```

### Profile 5 Test (VO2max 1min ×5)

**Seed Data**:
```python
{'type': 'intervals', 'on_power': 118, 'off_power': 55, 'on_sec': 60, 'off_sec': 240, 'repeat': 5}
```

**Converted Output** (FTP = 250w):
```json
{
  "repeat": 5,
  "steps": [
    {"duration": 60, "power": {"value": 118, "units": "%ftp"}},
    {"duration": 240, "power": {"value": 55, "units": "%ftp"}}
  ]
}
```

**Frontend Display**:
```
Main Set
- 5x (1m 118% (295w) / 4m 55% (138w))  ← CORRECT
```

**Power Validation**:
- Original: `on_power=118`, `off_power=55`
- Converted: `on=118`, `off=55`
- ✅ **Power values match!** (118% for VO2max is correct)
- ✅ **No NaN in output**

---

## Impact

### Before Fix
- ❌ Interval steps showed "NaNm" in workout display
- ❌ VO2max intervals at 118% FTP displayed as 47% FTP
- ❌ Power targets were 60% lower than intended
- ❌ Users would train at wrong intensities

### After Fix
- ✅ All workout steps display correctly with duration
- ✅ Power values are accurate (118% FTP stays as 118%)
- ✅ Interval blocks show as "5x (1m 118% / 4m 55%)"
- ✅ Watts calculated correctly (295w at 250w FTP)

---

## Files Changed

1. **frontend/src/lib/format-workout-steps.ts**
   - Moved repeat block check before duration access

2. **src/services/workout_generator.py**
   - Fixed power conversions in `_convert_profile_steps_to_frontend_format()`
   - Fixed power conversions in `_convert_profile_steps_to_text()`

3. **api/routers/plans.py**
   - Fixed power conversions in `get_current_weekly_plan()`

---

## Git

```bash
git add api/routers/plans.py frontend/src/lib/format-workout-steps.ts src/services/workout_generator.py
git commit -m "Fix NaN display in workout steps for interval workouts"
git push origin main
```

**Commit hash**: `d1d7a08`  
**Branch**: `main`  
**Pre-push checks**: ✅ Frontend build OK, ✅ Backend syntax OK

---

## Lessons Learned

1. **Always check data type assumptions**: The backend assumed power needed conversion, but seed data already stored percentages.

2. **Handle edge cases early**: Frontend should check for special cases (like repeat blocks) before accessing common properties.

3. **Trace data flow through the entire stack**: The bug existed in TWO backend conversion paths + frontend, requiring a comprehensive audit.

4. **Test with real data**: Profile ID 5 was the perfect test case because it uses intervals (118% on, 55% off, 5 repeats).

