# W/kg 기반 난이도 필터링 & LLM 프롬프트 영문화

> **Created**: 2026-02-15 (Sat) 23:49 KST
> **Updated**: 2026-02-15 (Sat) 23:55 KST
> **Commits**: `195ae2f`, `e3bad8f`
> **Files Changed**: 3 files, +64/-14 lines
> **Branch**: main

---

## Overview

두 가지 개선 작업:
1. 단건 워크아웃 생성 시 LLM이 한글로 응답하던 문제를 영문 base로 전환
2. 워크아웃 프로필 후보 필터링에 W/kg 기반 난이도 제한 추가 (TSB + W/kg 이중 필터)

---

## Problem

### 1. 한글 워크아웃 이름 생성

워크아웃 생성 시 workout_name, coaching 메시지가 한글로 출력됨.

**원인**: `workout_generator.py`의 프롬프트에서 명시적으로 한국어 응답을 요청

```python
# workout_generator.py:334
Respond with JSON only (in Korean):
...
**Coaching Guidelines (한국어로 작성):**
```

DB(`workout_profiles.db`)에는 한글 데이터가 없음 (158개 프로필 전부 영문). LLM이 프롬프트 지시에 따라 `workout_name`과 `coaching` 필드를 한글로 생성하던 것.

### 2. W/kg 미반영 난이도 필터링

프로필 후보 필터링이 TSB만 기반으로 난이도를 결정. W/kg가 낮은 선수(< 3.0)에게도 advanced 난이도 프로필이 후보에 포함되어 부적절한 워크아웃이 추천될 수 있음.

```python
# Before: TSB만으로 결정
max_difficulty = get_max_difficulty_from_tsb(tsb)
```

---

## Changes Made

### 1. LLM 프롬프트 영문화 (`195ae2f`)

**File**: `src/services/workout_generator.py` (+13/-13)

프롬프트의 언어 지시와 placeholder를 전부 영문으로 전환:

```python
# Before
Respond with JSON only (in Korean):
  "workout_name": "<descriptive workout name>",
  "coaching": {
    "selection_reason": "<TSB 기반 피로도 분석 및 선택 이유 설명>",
    "focus_points": ["<집중 포인트 1>", "<집중 포인트 2>"],
    "warnings": ["<주의사항 1>", "<주의사항 2 if any>"],
    "motivation": "<경쾌하고 격려적인 메시지>"
  }

**Coaching Guidelines (한국어로 작성):**
1. TSB 음수 (-10 이하) → 어제 부하, 피로 누적 상태, 회복 운동 권장
2. TSB 양수 (+5 이상) → 컸디션 좋음, 고강도 가능, 자신감 부여

# After
Respond with JSON only (in English):
  "workout_name": "<descriptive workout name in English>",
  "coaching": {
    "selection_reason": "<TSB-based fatigue analysis and selection rationale>",
    "focus_points": ["<focus point 1>", "<focus point 2>"],
    "warnings": ["<warning 1>", "<warning 2 if any>"],
    "motivation": "<short encouraging message>"
  }

**Coaching Guidelines (in English):**
1. Negative TSB (below -10): high fatigue from recent load, recommend recovery
2. Positive TSB (above +5): good form, high intensity possible, build confidence
```

### 2. W/kg 기반 난이도 필터링 (`e3bad8f`)

**Files**: `api/services/workout_profile_service.py` (+50/-1), `api/services/weekly_plan_service.py` (+2)

#### 2.1 `get_max_difficulty_from_wkg()` 함수 추가

```python
def get_max_difficulty_from_wkg(ftp: Optional[float], weight: Optional[float]) -> str:
    if ftp is None or weight is None or weight <= 0:
        return "advanced"  # No limit if unknown

    wpkg = ftp / weight
    if wpkg < 3.0:
        return "beginner"       # < 3.0 W/kg
    elif wpkg < 3.5:
        return "intermediate"   # 3.0-3.5 W/kg
    else:
        return "advanced"       # >= 3.5 W/kg
```

#### 2.2 이중 필터링 적용

TSB 기반 난이도와 W/kg 기반 난이도 중 **더 낮은 것**을 적용:

```python
max_difficulty_tsb = get_max_difficulty_from_tsb(tsb)
max_difficulty_wkg = get_max_difficulty_from_wkg(ftp, weight)

difficulty_order = {"beginner": 0, "intermediate": 1, "advanced": 2}
max_difficulty = min(
    max_difficulty_tsb,
    max_difficulty_wkg,
    key=lambda x: difficulty_order[x]
)
```

예시:
| TSB | W/kg | TSB 난이도 | W/kg 난이도 | 최종 |
|-----|------|-----------|------------|------|
| +15 | 4.0 | advanced | advanced | advanced |
| +15 | 2.8 | advanced | beginner | **beginner** |
| -15 | 4.0 | beginner | advanced | **beginner** |
| +5 | 3.2 | intermediate | intermediate | intermediate |

#### 2.3 주간 플랜 연동

```python
# weekly_plan_service.py — get_profile_candidates_for_llm() 호출에 FTP/weight 전달
profile_candidates_text, candidates = get_profile_candidates_for_llm(
    ...
    ftp=ftp,       # W/kg 필터링용
    weight=weight,
)
```

#### 2.4 버그 수정 (2건)

1. **인덴트 오류**: `query_profiles()` 메서드의 `ftp`, `weight` 파라미터가 클래스 레벨 인덴트로 되어있던 문제 수정
2. **None 포맷 에러**: `wpkg`가 `None`일 때 `f"{wpkg:.2f}"` 포맷팅에서 `TypeError` 발생 → 조건부 포맷으로 수정

```python
# Before (TypeError when wpkg is None)
f"W/kg={wpkg:.2f}({max_difficulty_wkg})"

# After
f"W/kg={f'{wpkg:.2f}' if wpkg else 'N/A'}({max_difficulty_wkg})"
```

---

## Architecture

### 프로필 후보 필터링 흐름 (변경 후)

```
워크아웃 생성 요청
  → get_profile_candidates_for_llm(tsb, style, duration, ftp, weight)
    → get_max_difficulty_from_tsb(tsb)     → "beginner" | "intermediate" | "advanced"
    → get_max_difficulty_from_wkg(ftp, wt) → "beginner" | "intermediate" | "advanced"
    → min(tsb_difficulty, wkg_difficulty)   → 최종 max_difficulty
    → WorkoutProfileService.query_profiles(difficulty_max=max_difficulty, ...)
    → LLM에게 필터된 후보만 전달
```

---

## Verification

| 항목 | 결과 |
|------|------|
| Python syntax check | OK (both files) |
| pytest (162 tests) | **162 passed**, 1 skipped |
| Frontend build (tsc + vite) | OK |
| Backend syntax check | OK |
| git push (pre-push hooks) | OK |

---

## Key Decisions

| 결정 | 근거 |
|------|------|
| 영문 base로 전환 | DB 데이터가 전부 영문, 프론트엔드 i18n으로 다국어 처리하는 것이 적절 |
| W/kg 임계값 3.0/3.5 | 일반적 사이클리스트 분류 기준 (Cat 4/3 경계) |
| FTP/weight 미제공 시 advanced | 기존 동작과 하위 호환 유지, 정보 없으면 제한하지 않음 |
| TSB와 W/kg 중 더 낮은 것 적용 | 안전 우선 — 둘 중 하나라도 낮으면 난이도 제한 |

---

## Next Steps

- [ ] 프로덕션 테스트 — 영문 워크아웃 이름/코칭 메시지 확인
- [ ] W/kg 3.0 미만 선수로 프로필 후보 필터링 검증
- [ ] 프론트엔드 i18n 적용 여부 검토 (coaching 메시지 다국어 지원)
- [ ] `query_profiles()`에 추가된 `ftp`/`weight` 파라미터 실제 활용 여부 확인
