# Workout Step Format Unification

> **Created**: 2026-02-15 (Sat) 12:30 KST
> **Updated**: 2026-02-15 (Sat) 14:32 KST
> **Branch**: `refactor/unify-workout-format` → merged to `main`
> **Commits**: `38b7883`, `949515c`, `871e95b`

## Overview

Workout step 데이터가 3가지 다른 포맷으로 존재하여 변환 함수가 난립하던 문제를 해결. DB에서 프론트엔드/Intervals.icu까지 **단일 nested format**으로 통일.

## Problem

### Before: 3개의 변환 경로

```
Profile DB (flat format)
  ├─ profile_to_frontend_steps()  → Frontend (nested)
  ├─ profile_to_steps()           → Legacy format
  └─ profile_to_intervals_steps() → Intervals.icu (watts)
```

각 변환 함수가 ~100줄씩, 총 ~300줄의 중복 코드. 버그 수정 시 3곳 모두 수정 필요. 실제로 power 단위 불일치(`%FTP` vs `watts`) 버그가 반복 발생.

### Old flat format (DB에 저장되던 형식)
```json
{
  "type": "intervals",
  "repeat": 4,
  "on_sec": 240,
  "on_power": 118,
  "off_sec": 120,
  "off_power": 55
}
```

### New canonical nested format (통일된 형식)
```json
{
  "repeat": 4,
  "steps": [
    {"duration": 240, "power": {"value": 118, "units": "%ftp"}},
    {"duration": 120, "power": {"value": 55, "units": "%ftp"}}
  ]
}
```

## Solution

### After: 단일 변환 경로

```
Profile DB (nested %FTP format)
  ├─ Frontend: 직접 사용 (변환 불필요!)
  └─ Intervals.icu/ZWO: convert_power_to_watts(steps, ftp)
```

## Changes Made

### Phase 1: DB Migration (`38b7883`)

**`scripts/migrate_db_format.py`** (신규, 154줄)
- 158개 프로필의 steps를 flat → nested 형식으로 일괄 마이그레이션
- 자동 백업 생성 (`workout_profiles.db.backup_YYYYMMDD_HHMMSS`)
- 타입별 변환 로직:
  - `warmup/cooldown` → ramp power (`start`/`end`) + flag
  - `intervals` → `repeat` + nested `steps[]`
  - `ramp` → ramp power
  - `steady` → single `value` power

**`api/services/power_converter.py`** (신규, 36줄)
- 단일 재귀 함수 `convert_power_to_watts(steps, ftp)`
- `%ftp` → `watts` 변환 (value, start, end 모두 처리)
- nested repeat 블록 재귀 처리

**`api/routers/plans.py`** (수정)
- `profile_to_frontend_steps()` 호출 제거
- DB에서 읽은 nested steps를 프론트엔드에 직접 전달
- Intervals.icu 등록 시 `convert_power_to_watts()` 사용

### Phase 2: Docker Build Fix (`949515c`)

**`Dockerfile.backend`** (수정)
- Docker 빌드 시 `scripts/migrate_db_format.py` 실행 추가
- seed script 이후 migration 실행으로 빌드된 이미지도 nested format 보장

### Phase 3: Double Conversion Fix (`871e95b`)

**`api/routers/plans.py`** (수정)
- Intervals.icu 등록 시 이중 변환 버그 수정
- `profile_to_intervals_steps()` (이미 watts 변환) 후 `convert_power_to_watts()` 재적용되던 문제 제거

## Code Examples

### Before: 변환 함수 호출
```python
# plans.py - 프론트엔드용
frontend_steps = profile_service.profile_to_frontend_steps(profile_steps, ftp)

# plans.py - Intervals.icu용  
intervals_steps = profile_service.profile_to_intervals_steps(profile_steps, ftp)
```

### After: 직접 사용 + 단일 변환
```python
# plans.py - 프론트엔드용: DB 데이터 직접 사용
steps = profile_data["steps"]  # 이미 nested %FTP format

# plans.py - Intervals.icu용: 단일 변환
from api.services.power_converter import convert_power_to_watts
watts_steps = convert_power_to_watts(steps, ftp)
```

### convert_power_to_watts (핵심 유틸리티)
```python
def convert_power_to_watts(steps, ftp):
    steps_copy = copy.deepcopy(steps)
    for step in steps_copy:
        if "repeat" in step and "steps" in step:
            step["steps"] = convert_power_to_watts(step["steps"], ftp)
        if "power" in step:
            power = step["power"]
            if power.get("units") == "%ftp":
                if "value" in power:
                    power["value"] = int(power["value"] * ftp / 100)
                if "start" in power:
                    power["start"] = int(power["start"] * ftp / 100)
                if "end" in power:
                    power["end"] = int(power["end"] * ftp / 100)
                power["units"] = "watts"
    return steps_copy
```

## Impact

| Metric | Before | After |
|--------|--------|-------|
| 변환 함수 수 | 3개 (~300줄) | 1개 (36줄) |
| 버그 수정 시 수정 지점 | 3곳 | 1곳 |
| 프론트엔드 변환 | 필요 | 불필요 |
| DB format | flat (type-dependent) | nested (일관) |
| 프로필 수 | 158개 마이그레이션 완료 | - |

## Remaining Work

- [ ] `apply_customization()` 함수 nested format 대응 업데이트
- [ ] Old conversion 함수 3개 완전 삭제 (`profile_to_frontend_steps`, `profile_to_steps`, `profile_to_intervals_steps`)
- [ ] 전체 테스트 스위트 실행 (162+ tests)
- [ ] `node_modules/` `.gitignore` 추가 (85MB 제거)

## Lessons Learned

1. **Format 통일은 빨리 할수록 좋다** — 변환 함수가 늘어날수록 버그 표면적 증가
2. **Migration script + backup은 필수** — 158개 프로필 일괄 변환 시 롤백 가능성 확보
3. **Docker build에 migration 포함** — CI/CD 파이프라인에서도 format 일관성 보장
4. **이중 변환 주의** — 기존 함수와 새 함수가 공존할 때 watts→watts 이중 변환 발생 가능
