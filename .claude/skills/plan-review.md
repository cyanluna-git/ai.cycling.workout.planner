# plan-review

주간 플랜을 분석하고 품질을 평가합니다.

## Usage

```bash
/plan-review [--week YYYY-MM-DD] [--detailed]
```

## Arguments

- `--week` - 분석할 주의 시작일 (Monday, default: current week)
- `--detailed` - 상세 분석 포함

## What it does

1. **플랜 구조 분석**
   - Training style 일관성 확인
   - TSS 분포 평가
   - 휴식일 적절성 검토

2. **모듈 사용 분석**
   - 각 워크아웃의 모듈 구조 검증
   - Training style과의 일치도 평가

3. **진행 상황 추적**
   - 계획 대비 실제 완료율
   - TSS 달성률

4. **개선 제안**
   - 과도한 부하 경고
   - 회복 필요성 평가

## Examples

### Basic Review
```bash
/plan-review
```

Output:
```
📅 Weekly Plan Review (2026-01-13 to 2026-01-19)

🎯 Training Style: Polarized (80/20)
📊 Total Planned TSS: 485
📈 Daily Distribution:
   Mon: Rest (0 TSS)
   Tue: Endurance - 65 TSS ✅
   Wed: VO2max - 75 TSS ✅
   Thu: Endurance - 60 TSS ✅
   Fri: Rest (0 TSS)
   Sat: Long Z2 - 145 TSS ⚠️  (Very High)
   Sun: Long Z2 - 140 TSS ⚠️  (Very High)

✅ Structure Quality:
   - Rest days: 2 (Optimal)
   - Long rides: 2 (Good for Polarized)
   - High intensity: 1 (Perfect for 80/20)
   - Zone 2 volume: 410 min (82% - Excellent!)

⚠️  Potential Issues:
   1. Weekend back-to-back long rides might be too demanding
   2. Consider moving one long ride to weekday

💡 Recommendations:
   - Great polarized structure!
   - Ensure adequate nutrition for weekend rides
   - Monitor recovery after Saturday's ride
```

### Detailed Analysis
```bash
/plan-review --detailed
```

Output:
```
📅 Detailed Weekly Plan Analysis

🔍 Daily Breakdown:

━━━ Monday (Rest) ━━━
Status: Planned
Type: Rest
✅ Strategic rest day before Tuesday's endurance ride

━━━ Tuesday (Endurance) ━━━
Name: Base Building Zone 2
Duration: 90 min | TSS: 65
Modules:
  1. ramp_standard (WARMUP) ✅
  2. endurance_60min (MAIN) ✅
  3. endurance_20min (MAIN) ✅
  4. flush_and_fade (COOLDOWN) ✅

Structure: ✅ Perfect
Intensity: 68% FTP (Zone 2) ✅
Style Match: Polarized ✅

━━━ Wednesday (VO2max) ━━━
Name: High Intensity Intervals
Duration: 60 min | TSS: 75
Modules:
  1. progressive_ramp_15min (WARMUP) ✅
  2. vo2max_4x4 (MAIN) ✅
  3. rest_5min (REST) ✅
  4. vo2max_3x3 (MAIN) ✅
  5. flush_and_fade (COOLDOWN) ✅

Structure: ✅ Perfect
Intensity: 115% FTP (VO2max) ✅
Style Match: Polarized ✅
Recovery: 5 min rest between sets ✅

━━━ Saturday (Long Z2) ━━━
Name: Weekend Long Ride
Duration: 150 min | TSS: 145
Modules:
  1. ramp_standard (WARMUP) ✅
  2. endurance_60min (MAIN) ✅
  3. endurance_60min (MAIN) ✅
  4. endurance_20min (MAIN) ✅
  5. flush_and_fade (COOLDOWN) ✅

Structure: ✅ Perfect
Intensity: 70% FTP (Zone 2) ✅
Style Match: Polarized ✅
⚠️  Warning: 150 min is demanding, ensure:
   - Adequate fueling (60-90g carbs/hr)
   - Hydration strategy
   - Previous endurance base

📊 Weekly Statistics:

Training Distribution:
  Zone 1-2 (Easy): 380 min (83%) ✅
  Zone 3-4 (Tempo/SS): 0 min (0%) ✅
  Zone 5-6 (Hard): 45 min (17%) ⚠️  (Slightly high, aim for <15%)

TSS Progression:
  Week -2: 445 TSS
  Week -1: 465 TSS
  This week: 485 TSS (+4.3%)
  ✅ Progressive load within safe range

Recovery Metrics:
  Current TSB: +2 (Fresh)
  Projected TSB: -8 (Optimal training range)
  ✅ Good balance

🎯 Training Effectiveness Score: 8.5/10

Strengths:
  ✅ Excellent polarized structure
  ✅ Good recovery distribution
  ✅ Progressive load management
  ✅ Long rides match training style

Areas for Improvement:
  ⚠️  High intensity slightly above 20% target
  💡 Consider reducing VO2max intervals by 5-10 min

🏆 Overall Assessment: Excellent Plan
This plan follows polarized principles well with proper
recovery and progressive loading. Monitor fatigue levels
and adjust if needed.
```

### Progress Tracking
```bash
/plan-review --week 2026-01-06
```

Output:
```
📅 Plan Review & Progress (2026-01-06 to 2026-01-12)

Status: Completed ✅

📊 Completion Rate:
   Workouts Completed: 5/5 (100%)
   TSS Achieved: 468/480 (97.5%)

📈 Daily Progress:
   Mon: Rest ✅
   Tue: Endurance - Planned: 60, Actual: 62 ✅
   Wed: VO2max - Planned: 75, Actual: 71 ⚠️  (Slightly under)
   Thu: Endurance - Planned: 55, Actual: 58 ✅
   Fri: Rest ✅
   Sat: Long Z2 - Planned: 140, Actual: 145 ✅
   Sun: Long Z2 - Planned: 150, Actual: 142 ⚠️  (Cut short)

💡 Insights:
   - Excellent adherence overall
   - Sunday ride cut by 8 min (fatigue?)
   - Consider reducing Saturday TSS next week

🎯 Recommendations for Next Week:
   1. Maintain current load or reduce by 5%
   2. Ensure full recovery before next VO2max session
   3. Monitor Sunday ride completion
```

## Implementation

```python
from dataclasses import dataclass
from typing import List

@dataclass
class WorkoutQuality:
    has_warmup: bool
    has_cooldown: bool
    structure_valid: bool
    style_match: bool
    duration_appropriate: bool
    tss_appropriate: bool

async def review_weekly_plan(week_start: date, detailed: bool = False):
    # Get plan
    plan = await get_weekly_plan(week_start)

    # Analyze structure
    analysis = {
        'total_tss': sum(w.estimated_tss for w in plan.daily_plans),
        'rest_days': len([w for w in plan.daily_plans if w.workout_type == 'Rest']),
        'high_intensity': len([w for w in plan.daily_plans if w.workout_type in ['VO2max', 'Threshold']]),
        'long_rides': len([w for w in plan.daily_plans if w.duration_minutes >= 120]),
    }

    # Evaluate quality
    quality_scores = []
    for workout in plan.daily_plans:
        if workout.workout_type != 'Rest':
            quality = evaluate_workout_quality(
                workout,
                plan.training_style
            )
            quality_scores.append(quality)

    # Generate recommendations
    recommendations = generate_recommendations(
        plan,
        analysis,
        quality_scores
    )

    return format_report(plan, analysis, recommendations, detailed)

def evaluate_workout_quality(workout, training_style) -> WorkoutQuality:
    """Evaluate individual workout quality."""
    modules = workout.selected_modules

    return WorkoutQuality(
        has_warmup=any(m in WARMUP_MODULES for m in modules),
        has_cooldown=any(m in COOLDOWN_MODULES for m in modules),
        structure_valid=validate_module_order(modules),
        style_match=matches_training_style(workout, training_style),
        duration_appropriate=check_duration(workout),
        tss_appropriate=check_tss(workout),
    )
```

## Related

- [workout-gen](#workout-gen) - Generate workouts
- [cache-check](#cache-check) - Verify cache
