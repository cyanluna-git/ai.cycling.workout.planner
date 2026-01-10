# workout-gen

워크아웃 생성 및 테스트를 위한 통합 스킬입니다.

## Usage

```bash
/workout-gen [--style STYLE] [--duration MINUTES] [--test-upload]
```

## Arguments

- `--style` - Training style (polarized, sweetspot, threshold, etc.)
- `--duration` - Workout duration in minutes (default: 60)
- `--test-upload` - Generate and upload to Intervals.icu
- `--validate-modules` - Validate module structure

## What it does

1. **워크아웃 생성**
   - AI를 사용한 워크아웃 생성
   - 모듈 구조 검증
   - TSS 계산 확인

2. **구조 검증**
   - WARMUP → MAIN → COOLDOWN 순서 확인
   - 모듈 존재 여부 확인
   - 중복 모듈 체크

3. **업로드 테스트** (--test-upload 옵션)
   - Intervals.icu로 업로드
   - 캐시 무효화 확인
   - 업로드된 워크아웃 확인

## Examples

### Basic Generation
```bash
/workout-gen --style sweetspot --duration 75
```

Output:
```
🏋️ Generating Workout...

✅ Generated: Sweet Spot Foundation Builder
   Type: SweetSpot
   Duration: 75 minutes
   TSS: 82

📋 Modules:
   1. progressive_ramp_15min (WARMUP)
   2. sst_2x20 (MAIN)
   3. rest_5min (REST)
   4. sst_2x15 (MAIN)
   5. flush_and_fade (COOLDOWN)

✅ Structure Validation:
   - Warmup at start ✅
   - Main segments in middle ✅
   - Cooldown at end ✅
   - No module conflicts ✅

💡 Workout Details:
   - Avg Power: 88% FTP
   - Work Time: 55 min
   - Rest Time: 20 min
```

### With Upload Test
```bash
/workout-gen --style threshold --test-upload
```

Output:
```
🏋️ Generating Workout...

✅ Generated: Threshold Builder
   Type: Threshold
   TSS: 95

📤 Uploading to Intervals.icu...
   ✅ Uploaded successfully (ID: 12345)

🔍 Checking Cache Invalidation...
   ✅ calendar cache cleared
   ✅ fitness:complete cache cleared
   ✅ fitness:training cache cleared
   ✅ fitness:wellness cache cleared

📊 Verification:
   ✅ Workout appears in calendar
   ✅ TSS matches (95)
   ✅ Duration matches (60 min)

🎉 All checks passed!
```

### Module Validation
```bash
/workout-gen --validate-modules
```

Output:
```
🔍 Validating Workout Modules...

📦 Total Modules: 87
   - WARMUP: 8
   - MAIN: 62
   - REST: 7
   - COOLDOWN: 10

✅ Module Checks:
   - All modules have valid structure ✅
   - No duplicate module keys ✅
   - All blocks have required fields ✅

⚠️  Warnings:
   - 'progressive_warmup_20min' → Use 'progressive_warmup_15min' (fallback exists)
   - 'standard_warmup' → Use 'ramp_standard' (fallback exists)

💡 Recommendations:
   1. Remove unused modules: ['old_interval_3x8']
   2. Add missing REST modules for Norwegian style
   3. Consider adding more LONG modules (>60min)

📊 Module Usage Statistics (Last 30 days):
   Top 5 Most Used:
   1. ramp_standard (156 times)
   2. flush_and_fade (148 times)
   3. sst_2x20 (89 times)
   4. endurance_60min (76 times)
   5. vo2max_4x4 (62 times)

   Least Used:
   - barcode_test_ramp_2 (0 times) ⚠️
   - recovery_spin_90min (1 time)
```

## Implementation

```python
from src.services.workout_generator import WorkoutGenerator
from src.services.workout_modules import (
    WARMUP_MODULES,
    MAIN_SEGMENTS,
    REST_SEGMENTS,
    COOLDOWN_MODULES
)

async def generate_and_test(
    style: str,
    duration: int = 60,
    test_upload: bool = False
):
    # Generate workout
    generator = WorkoutGenerator(llm_client, user_profile, duration)
    workout = generator.generate_enhanced(
        training_metrics,
        wellness_metrics,
        date.today(),
        style=style,
        duration=duration
    )

    # Validate structure
    validate_module_order(workout.selected_modules)
    validate_module_existence(workout.selected_modules)

    # Test upload if requested
    if test_upload:
        await upload_and_verify(workout)

    return workout

def validate_module_order(modules: list[str]):
    """Validate WARMUP → MAIN → COOLDOWN order."""
    warmup_indices = [
        i for i, m in enumerate(modules)
        if m in WARMUP_MODULES
    ]
    cooldown_indices = [
        i for i, m in enumerate(modules)
        if m in COOLDOWN_MODULES
    ]

    # Warmup should be first
    if warmup_indices and warmup_indices[0] != 0:
        raise ValidationError(
            f"Warmup module at position {warmup_indices[0]}, "
            "should be at 0"
        )

    # Cooldown should be last
    if cooldown_indices:
        expected = len(modules) - len(cooldown_indices)
        if cooldown_indices[0] != expected:
            raise ValidationError(
                f"Cooldown module at position {cooldown_indices[0]}, "
                f"should be at {expected}"
            )
```

## Related

- [api-test](#api-test) - Test API endpoints
- [cache-check](#cache-check) - Verify cache implementation
