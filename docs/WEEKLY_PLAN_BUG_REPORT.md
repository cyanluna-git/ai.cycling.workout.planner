# Weekly Plan Generation - Bug Report for Jules

## ✅ Status: FIXED (2026-01-10)

All critical bugs have been resolved. See [BUG_FIXES_APPLIED.md](BUG_FIXES_APPLIED.md) for details.

---

## 이전 상태 (Historical - Before Fix)

주간 워크아웃 계획 생성 기능 구현 중 백엔드 API에서 에러 발생.

## 관련 파일

- `api/routers/plans.py` - 주간 계획 API 엔드포인트
- `api/services/weekly_plan_service.py` - AI 기반 주간 계획 생성 서비스
- `api/main.py` - CORS 설정
- `frontend/src/components/WeeklyPlanCard.tsx` - UI 컴포넌트
- `supabase/weekly_planning_migration.sql` - DB 스키마

---

## 🐛 현재 발생하는 에러

### 1. ResponseValidationError (주요 문제)

```
fastapi.exceptions.ResponseValidationError: 1 validation error:
  {'type': 'model_attributes_type', 'loc': ('response',), 
   'msg': 'Input should be a valid dictionary or object to extract fields from', 
   'input': None}
```

**원인 분석:**
- `generate_weekly_plan()` 함수 (line 179)가 마지막에 `get_current_weekly_plan(user)` 호출
- `get_current_weekly_plan()`은 **현재 주** 계획을 조회 (`get_week_dates()` 사용)
- 하지만 `generate_weekly_plan()`은 **다음 주** 계획을 생성 (`get_next_week_dates()` 사용)
- 결과적으로 방금 생성한 계획을 찾지 못해 `None` 반환
- `response_model=WeeklyPlanResponse`는 `None`을 허용하지 않아 에러 발생

**✅ 수정 완료:**
- Added `week_start_date` parameter to `get_current_weekly_plan()`
- Changed return statement to: `return await get_current_weekly_plan(user, week_start_date=week_start.isoformat())`
- Now correctly queries the week that was just generated

### 2. Groq Quota Exceeded

```
Groq quota exceeded, trying next provider...
```

- Groq API quota 초과로 fallback 발생
- 다음 provider로 넘어가지만, LLM 응답이 제대로 처리되지 않는 경우 있음

### 3. google.generativeai 지원 종료 경고

```
FutureWarning: All support for the `google.generativeai` package has ended. 
Please switch to the `google.genai` package.
```

- `src/clients/llm.py:133`에서 deprecated 패키지 사용 중
- `google-generativeai` → `google-genai`로 마이그레이션 필요

---

## 📋 수정 사항

### ✅ 필수 수정 완료 (Critical - FIXED)

1. **`api/routers/plans.py` - generate_weekly_plan 함수** ✅
   - ✅ 생성 후 조회 시 올바른 week_start 사용
   - ✅ `get_current_weekly_plan(user)` → 방금 생성한 주의 계획 조회

2. **`api/routers/plans.py` - get_current_weekly_plan 함수** ✅
   - ✅ `week_start_date` 파라미터 추가하여 특정 주 조회 가능하게

3. **`src/config.py` - LLM API Key Loading** ✅
   - ✅ Removed `LLM_API_KEY` from required environment variables
   - ✅ Added fallback to provider-specific keys (GEMINI_API_KEY, etc.)
   - ✅ Added `LLM_PROVIDER` env var for configuration

### 권장 수정 (Recommended)

3. **LLM 응답 파싱 에러 핸들링**
   - `weekly_plan_service.py`에서 LLM 응답이 없거나 파싱 실패 시 더 robust한 처리

4. **`src/clients/llm.py`**
   - `google.generativeai` → `google.genai` 마이그레이션

---

## 테스트 방법

```bash
# 백엔드 시작
cd /Users/cyanluna-pro16/dev/ai.coach/ai.cycling.workout.planner
source .venv/bin/activate
python3 -m uvicorn api.main:app --reload --port 8005

# 프론트엔드 시작
cd frontend && npm run dev
```

대시보드에서 "🗓️ 주간 계획 생성" 버튼 클릭하여 테스트

---

## 구현 완료된 부분

- ✅ DB 스키마 (`weekly_plans`, `daily_workouts`, `job_queue` 테이블)
- ✅ API 엔드포인트 구조 (`/api/plans/*`)
- ✅ 프론트엔드 UI 컴포넌트 (`WeeklyPlanCard`)
- ✅ CORS 설정
- ✅ LLM 프롬프트 및 주간 계획 생성 서비스 기본 구조

---

## 코드 위치

주요 버그 위치:
- `api/routers/plans.py:282` - `return await get_current_weekly_plan(user)`
- `api/routers/plans.py:107-124` - `get_current_weekly_plan` 함수

Deprecated 코드:
- `src/clients/llm.py:133` - `import google.generativeai as genai`
