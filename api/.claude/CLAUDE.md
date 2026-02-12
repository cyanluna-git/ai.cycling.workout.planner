# API Module

FastAPI REST endpoints and API-level business logic.

## Overview

HTTP layer for frontend + external integrations. Routes requests through service layer (src/) to LLM and external APIs.

## Key Components

### Routers (api/routers/)
- **`workout.py`** — POST /api/workouts — Generate workout
- **`fitness.py`** — GET /api/fitness — Sync Intervals.icu data
- **`plans.py`** — CRUD saved workout plans
- **`settings.py`** — GET/PATCH user settings
- **`admin.py`** — LLM model management, logs (admin only)

### Services (api/services/)
- **`caching.py`** — Redis cache (optional) for fitness data
- **`llm_selector.py`** — Choose Groq vs Gemini based on load
- **`error_handler.py`** — Normalize errors, fallback strategy

## Request/Response Flow

```
POST /api/workouts
  → Validate (Pydantic)
  → Check auth (Supabase JWT)
  → Fetch athlete data (Intervals.icu)
  → Call WorkoutGenerator (src/)
    → LLM select modules (Groq → Gemini)
  → Convert to ZWO
  → Save to Supabase
  → Return {workout, zwo}
```

## Dependency Injection

```python
@router.post("/workouts")
async def generate_workout(
    request: WorkoutRequest,
    current_user = Depends(get_current_user),
    llm = Depends(get_llm_client),
):
    # Handler logic
```

## Error Handling

- LLM timeouts → Retry fallback chain
- Intervals.icu unavailable → Use cached data
- Invalid TSB →  400 Bad Request
- Auth failure →  401 Unauthorized

## Commands

```bash
uvicorn api.main:app --reload --port 8005  # Dev
pytest tests/api/ -v                       # API tests
```

## Environment

Same as root + Supabase config.

## Parent Rules

Inherit from `@../../.claude/rules/`:
- code-style.md — FastAPI patterns
- testing.md — pytest fixtures
- api-conventions.md — REST design, response format
- commit-workflow.md — Git conventions
- security.md — Auth validation, error handling
