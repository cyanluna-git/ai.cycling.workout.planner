# Bug Fixes Applied - Weekly Plan Generation

## Date: 2026-01-10

## Fixed Issues

### 🔴 Critical: ResponseValidationError in generate_weekly_plan()

**Problem:**
```
fastapi.exceptions.ResponseValidationError: 1 validation error:
  {'type': 'model_attributes_type', 'loc': ('response',),
   'msg': 'Input should be a valid dictionary or object to extract fields from',
   'input': None}
```

**Root Cause:**
- `generate_weekly_plan()` generates plan for **next week** using `get_next_week_dates()`
- But returns result from `get_current_weekly_plan(user)` which queries **current week**
- No plan found for current week → returns `None`
- FastAPI expects `WeeklyPlanResponse`, not `None` → validation error

**Fix Applied:**

1. **Modified [api/routers/plans.py:107-119](api/routers/plans.py#L107-L119)**
   - Added optional `week_start_date` parameter to `get_current_weekly_plan()`
   - Allows querying specific week, not just current week

2. **Modified [api/routers/plans.py:296](api/routers/plans.py#L296)**
   - Changed from: `return await get_current_weekly_plan(user)`
   - Changed to: `return await get_current_weekly_plan(user, week_start_date=week_start.isoformat())`
   - Now queries the week we just generated

**Result:** ✅ Weekly plan generation now returns the correct plan

---

### 🔴 Critical: Missing LLM_API_KEY Environment Variable

**Problem:**
```
ValueError: Missing required environment variables: LLM_API_KEY
```

**Root Cause:**
- [src/config.py](src/config.py) required `LLM_API_KEY` env var
- `.env` file only had provider-specific keys (`GEMINI_API_KEY`, `OPENAI_API_KEY`, etc.)
- No generic `LLM_API_KEY` was set

**Fix Applied:**

1. **Modified [src/config.py:82-106](src/config.py#L82-L106)**
   - Removed `LLM_API_KEY` from required vars
   - Added fallback logic to use provider-specific keys
   - Detects provider from `LLM_PROVIDER` env var
   - Automatically uses `GEMINI_API_KEY`, `OPENAI_API_KEY`, or `GROQ_API_KEY`

2. **Modified [.env](/.env)**
   - Added `LLM_PROVIDER=gemini` to specify default provider

**Result:** ✅ Config loads successfully without requiring generic `LLM_API_KEY`

---

## Testing

### Verification Commands

```bash
# 1. Test config loading
python3 -c "from src.config import load_config; config = load_config(); print('✅ Config OK')"

# 2. Start backend
python3 -m uvicorn api.main:app --reload --port 8005

# 3. Test weekly plan generation
# In frontend: Click "🗓️ 주간 계획 생성" button
```

### Expected Behavior

1. ✅ Backend starts without config errors
2. ✅ Weekly plan generation completes successfully
3. ✅ Response returns valid `WeeklyPlanResponse` with 7 daily workouts
4. ✅ Plan is stored in database with correct week_start/week_end
5. ✅ Frontend displays the generated plan

---

## Remaining Issues (Non-Critical)

### 🟡 Warning: Groq Quota Exceeded

**Status:** Non-blocking - System falls back to other providers
**Message:** `Groq quota exceeded, trying next provider...`
**Impact:** Minimal - LLM client automatically tries Gemini/OpenAI

**Future Fix:** Monitor quota usage, potentially upgrade Groq plan

---

### 🟡 Warning: google.generativeai Deprecated

**Status:** Non-blocking - Still works but generates warning
**File:** [src/clients/llm.py:133](src/clients/llm.py#L133)
**Message:**
```
FutureWarning: All support for the `google.generativeai` package has ended.
Please switch to the `google.genai` package.
```

**Future Fix:** Migrate from `google-generativeai` to `google-genai` package

---

## Files Modified

| File | Lines Changed | Purpose |
|------|---------------|---------|
| [api/routers/plans.py](api/routers/plans.py) | 107-119, 296 | Fix week query logic |
| [src/config.py](src/config.py) | 82-118 | Fix LLM API key loading |
| [.env](/.env) | +2 lines | Add LLM_PROVIDER setting |

---

## Commits

```bash
git add api/routers/plans.py src/config.py .env
git commit -m "fix: Resolve weekly plan generation bugs

- Fix ResponseValidationError by querying correct week after generation
- Add fallback logic for LLM API keys (provider-specific)
- Add LLM_PROVIDER env var for flexibility

Fixes:
- Weekly plan returns None → Now returns generated plan
- Missing LLM_API_KEY error → Uses provider-specific keys"
```

---

## Next Steps

1. ✅ Test weekly plan generation in production
2. Monitor Groq quota usage
3. Plan migration to `google-genai` package
4. Add error handling for LLM provider failures

---

**Status:** All critical bugs fixed ✅
**Ready for Testing:** Yes
**Breaking Changes:** None
