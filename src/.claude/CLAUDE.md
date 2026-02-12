# Core Module (src/)

Python service layer for AI-powered workout generation and external integrations.

## Overview

Core workout logic, LLM client management, and external service clients (Groq/Gemini, Intervals.icu, Supabase).

## Key Modules

### Services
- **`services/workout_generator.py`** — "Omakase" pattern:
  - Select workout modules based on TSB
  - Assemble WARMUP → MAIN → COOLDOWN sequence
  - Handle LLM fallback chain (Groq → Gemini 2.0 → Gemini 1.5)
- **`services/weekly_plan_service.py`** — Weekly plan generation:
  - System/User prompt separation
  - TSB-based intensity auto-selection (TSB_INTENSITY_MAP)
  - Auto training style resolution based on TSB + focus
  - Style-specific template filtering (only selected style sent to LLM)
  - Athlete context: FTP, weight, W/kg, wellness, indoor/outdoor
  - Module validation (remove invalid keys) + order fix
  - used_modules collection for variety tracking
- **`services/zwo_converter.py`** — Convert internal format → Zwift XML
- **`services/prompts/`** — LLM prompt templates (structured, no injection)

### Clients
- **`clients/llm.py`** — LLM interface (Vercel AI Gateway)
  - Fallback strategy with retries
  - Response validation + parsing
  - Error handling
- **`clients/intervals.py`** — Intervals.icu API client
  - Fetch athlete fitness data (CTL/ATL/TSB)
  - Cache responses (5 min TTL)
- **`clients/supabase_client.py`** — Supabase client
  - Auth token management
  - User settings CRUD

### Data
- **`data/workout_modules/`** — Pre-validated JSON workout library
  - WARMUP: Spin-up (5-10 min)
  - MAIN: Hard efforts, sweet spot, endurance
  - COOLDOWN: Easy spin (3-5 min)

## Type System

```python
class WorkoutRequest(BaseModel):
    duration: int  # 15-180 min
    target_intensity: str  # easy, moderate, hard
    tsb: float  # -60 to +60 (Wellness)

class WorkoutResponse(BaseModel):
    modules: list[Module]
    zwo: str  # Zwift XML
    generated_at: datetime
```

## Commands

```bash
pytest tests/ -v                    # All tests
pytest tests/test_llm.py -v         # LLM tests
pytest tests/test_generator.py -v   # Generator tests
black . && isort . && mypy .        # Quality
```

## Environment

- `GROQ_API_KEY`, `GEMINI_API_KEY`: LLM keys
- `INTERVALS_API_KEY`: Intervals.icu auth
- `VERCEL_AI_GATEWAY_URL`: Gateway endpoint

## Parent Rules

Inherit from `@../../.claude/rules/`:
- code-style.md — Python conventions + LLM patterns
- testing.md — pytest fixtures, mock LLM calls
- api-conventions.md — Response format
- commit-workflow.md — Git conventions
- security.md — API key handling, prompt injection prevention
