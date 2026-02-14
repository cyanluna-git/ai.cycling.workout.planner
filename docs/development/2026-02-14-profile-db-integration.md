# Profile DB 전체 통합 및 프로덕션 배포

> **Created**: 2026-02-14 (Fri) 10:40 KST
> **Updated**: 2026-02-14 (Fri) 14:25 KST
> **Commits**: `48b9167` → `059d869` (6 commits)
> **Files Changed**: 5 files, +487/-41 lines

## 📋 Overview

Workout Profile DB 시스템을 일일/주간 워크아웃 생성에 완전 통합하고 프로덕션 배포까지 완료한 작업.
기존 모듈 조합 방식(136개 모듈 → LLM이 warmup+main+cooldown 조립)에서 프로필 선택 방식(100개 완성 프로필 → LLM이 profile_id 선택)으로 전환.

## 🎯 Problem

1. **일일 워크아웃이 모듈 방식만 사용** — Profile DB 인프라는 구축됐으나 `workout_generator.py`는 미전환
2. **Cloud Build 배포 실패** — `cloudbuild.yaml`에서 쉘 변수 `$COMMIT_DATE`가 Cloud Build substitution으로 해석됨
3. **프론트엔드 NaN 버그** — Profile DB steps 형식과 프론트엔드 WorkoutStep 형식 불일치
4. **주간 플랜 미연동** — `profile_id` 기반 steps 렌더링 미구현
5. **Supabase 컬럼 누락** — `daily_workouts` 테이블에 `profile_id`, `customization` 컬럼 없음
6. **다양성 부족** — LLM이 동일 조건에서 매번 같은 프로필만 선택

## 🔧 Changes Made

### 1. 일일 워크아웃 Profile DB 전환 (`c931579`)
**File**: `src/services/workout_generator.py` (+338 lines)

- `_select_profile_with_llm()` 메서드 추가
  - `WorkoutProfileService.get_candidates()` → TSB/스타일/시간 기반 필터링
  - LLM에게 후보 목록 제공 → `profile_id` + `customization` 반환
  - TSB < -20: beginner only, TSB < -10: intermediate, else: advanced
- `_convert_profile_steps_to_text()` 메서드 추가
  - watts → %FTP 변환, Intervals.icu 텍스트 포맷
- `generate_enhanced()` 수정
  - Profile DB 우선 시도 → 실패 시 모듈 조합 fallback

### 2. Cloud Build 수정 (`71c2e94`)
**File**: `cloudbuild.yaml` (+2/-2)

- `$COMMIT_DATE` → `$$COMMIT_DATE` 이스케이프
- Cloud Build는 yaml 내 `$변수`를 substitution으로 해석하므로 쉘 변수는 `$$`로 이스케이프 필요
- **이 버그로 이전 4개 빌드가 전부 FAILURE**

### 3. NaN 버그 수정 (`c095173`)
**File**: `src/services/workout_generator.py` (+108/-13)

- `_convert_profile_steps_to_frontend_format()` 메서드 추가
- 백엔드 steps: `{type, start_power, end_power, duration_sec, power}` 
- 프론트엔드 WorkoutStep: `{duration, power: {value/start/end, units}, warmup, cooldown, ramp, repeat, steps}`
- warmup, cooldown, intervals, ramp, steady 모든 타입 변환 지원

### 4. 주간 플랜 Profile DB 연동 (`ea79be1`)
**File**: `api/routers/plans.py` (+57/-14)

- 워크아웃 조회 시 `profile_id`가 있으면 Profile DB에서 steps 변환
- `planned_modules` (레거시) fallback 유지
- 프론트엔드 WorkoutStep 형식으로 변환 후 `planned_steps`에 설정

### 5. Supabase 스키마 업데이트 (수동)
```sql
ALTER TABLE daily_workouts ADD COLUMN IF NOT EXISTS profile_id integer DEFAULT NULL;
ALTER TABLE daily_workouts ADD COLUMN IF NOT EXISTS customization jsonb DEFAULT NULL;
```

### 6. 다양성 개선 (`059d869`)
**Files**: `src/services/workout_generator.py`, `api/services/weekly_plan_service.py`

- `random.shuffle(candidates)` — 매 호출마다 후보 순서 랜덤화
- `Variety seed: {random_number}` — LLM에게 다양한 선택 유도
- 프롬프트에 "Do NOT always pick the same profile" 명시

## 📊 Architecture

```
일일 워크아웃 생성 Flow:
  generate_enhanced()
    → _select_profile_with_llm()
      → WorkoutProfileService.get_candidates() [SQLite]
      → random.shuffle(candidates)
      → format_candidates_for_prompt()
      → LLM: profile_id + customization 선택
    → get_profile_by_id() → apply_customization()
    → profile_to_steps(ftp) → watts 변환
    → _convert_profile_steps_to_frontend_format() → WorkoutStep[]
    → _convert_profile_steps_to_text() → Intervals.icu 텍스트
    → GeneratedWorkout 반환
    [fallback → 기존 모듈 조합]

주간 플랜 조회 Flow:
  get_weekly_plan()
    → daily_workouts에서 profile_id 확인
    → profile_id 있으면 → Profile DB에서 steps 변환
    → profile_id 없으면 → planned_modules → convert_structure_to_steps()
```

## ✅ Verification

- **Unit Tests**: 162 passed, 1 skipped
- **E2E Profile DB 후보 검색**: 8개 시나리오 모두 적절한 후보 반환
  - Fresh (TSB +15): VO2max, Threshold, Anaerobic 10개
  - Tired (TSB -15): Endurance, Recovery 8개
  - Very tired (TSB -25): Recovery only 6개
- **프로덕션 일일 워크아웃**: 차트 + 텍스트 정상 표시 (NaN 해결)
- **프로덕션 주간 플랜**: 7일 프로필 기반 생성 확인 (Z2 Steady, VO2max, Endurance 등)
- **Cloud Build**: SUCCESS (git_commit 정상 표시)

## 🔑 Key Decisions

| 결정 | 근거 |
|------|------|
| Profile DB 우선 + 모듈 fallback | 하위 호환성 유지, Profile DB 없는 환경에서도 동작 |
| Frontend 변환을 백엔드에서 수행 | 프론트엔드 변경 최소화, API 계약 유지 |
| 후보 셔플로 다양성 확보 | LLM temperature 조절보다 효과적 |
| `$$` 이스케이프 | Cloud Build의 substitution 해석 규칙 |
| Supabase 컬럼 수동 추가 | 마이그레이션 시스템 미구축 (향후 개선 필요) |

## 📝 Lessons Learned

1. **서브에이전트 검증 필수**: 서브에이전트가 "완료"라고 해도 실제 코드와 다를 수 있음
2. **Cloud Build `$` 이스케이프**: 쉘 변수는 반드시 `$$`로 이스케이프
3. **프론트엔드-백엔드 데이터 형식 일치**: 새 데이터 소스 추가 시 프론트엔드가 기대하는 형식 확인 필수
4. **DB 스키마 변경 관리**: 마이그레이션 스크립트로 관리해야 함 (수동 추가는 실수 유발)
5. **LLM 다양성**: 동일 프롬프트 → 동일 결과 경향. 후보 셔플 + 시드가 효과적

## 🏗️ Infrastructure Setup (bonus)

- **gcloud CLI**: `/tmp/google-cloud-sdk/` (ARM64), 인증 완료 (`pjy8412@gmail.com`)
- **Supabase CLI**: `/tmp/supabase` v2.75.0
- 이제 RPi에서 직접 Cloud Build 로그 확인 및 트리거 가능

## ⏭️ Next Steps

- [ ] Supabase CLI 프로젝트 링크 (직접 SQL 실행)
- [ ] DB 마이그레이션 관리 체계 구축
- [ ] ZWO 파일 import로 프로필 확장 (현재 100개 → 200+)
- [ ] SWR 적용 나머지 페이지 (SettingsPage, WeeklyPlanCard)
- [ ] LLM 프로필 선택 품질 모니터링 (어떤 프로필이 자주 선택되는지)
