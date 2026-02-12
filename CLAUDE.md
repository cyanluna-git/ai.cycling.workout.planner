# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working with this repository.

## Project Overview

AI Cycling Coach — Personalized workout generation platform integrating with Intervals.icu. LLM-powered (Groq/Gemini) workout selection based on athlete fitness metrics (CTL/ATL/TSB) and wellness data. Generates ZWO (Zwift) workout files.

## Repository Structure

- `frontend/` — React 19 + TypeScript 5 + Vite 7
- `src/` — Core Python workout logic (services, data, clients)
- `api/` — FastAPI endpoints (routers, services)
- `tests/` — pytest test suite
- `supabase/` — Database migrations
- `run.py` — Dev launcher (backend 8005 + frontend 3005)
- `.claude/rules/` — Shared coding conventions

## Tech Stack & Key Dependencies

**Frontend**: React 19, TypeScript, Vite, Tailwind CSS 4, Shadcn UI, React Query, Recharts  
**Backend**: FastAPI, Python 3.11+, Pydantic, Supabase (PostgreSQL + Auth)
- **LLM**: Groq (llama-3.3-70b) → Gemini 2.0 Flash (fallback) via Vercel AI Gateway
- **External**: Intervals.icu API, Supabase client

## Architecture

```
Browser → React (port 3005, Vite)
       → FastAPI (port 8005, Supabase auth)
       → Intervals.icu (athlete data)
       → LLM via Vercel AI Gateway
       → Supabase (user settings)
```

**System design** ("Omakase" pattern):
1. **Library**: Pre-validated workout modules in `src/data/` (WARMUP → MAIN → COOLDOWN)
2. **AI Selector**: LLM picks optimal module combo based on TSB + duration
3. **Assembler**: Converts to ZWO format (Zwift XML) for Intervals.icu

**Key modules:**
- **Backend**: `api/routers/` (workout, fitness, plans), `api/services/` (caching, LLM fallback)
- **Core**: `src/services/` (workout_generator, zwo_converter), `src/clients/` (llm, intervals, supabase)
- **Data**: `src/data/` (workout module JSON library)
- **Frontend**: `pages/` (Dashboard, Settings), `components/` (FitnessCard, WorkoutForm), `hooks/` (useDashboard)

## Commands

### Development
```bash
python run.py              # Backend (8005) + Frontend (3005)
python run.py backend      # Backend only
python run.py frontend     # Frontend only
python run.py --docker     # Docker Compose
```

### Frontend
```bash
cd frontend
pnpm dev && pnpm build && pnpm lint
```

### Testing
```bash
pytest tests/ -v           # All tests
pytest tests/test_validator.py -v  # Single file
```

## Environment Setup

Backend `.env`:
- `SUPABASE_URL`, `SUPABASE_KEY`
- `GROQ_API_KEY`
- `GEMINI_API_KEY`
- `INTERVALS_API_KEY`
- `VERCEL_AI_GATEWAY_URL`

Frontend `.env`:
- `VITE_SUPABASE_URL`, `VITE_SUPABASE_KEY`

## API Documentation

Backend running → http://localhost:8005/docs (Swagger)

## Deployment

- **Frontend**: Vercel (auto-deploy from main)
- **Backend**: Google Cloud Run (asia-northeast3)

## Imports

See `.claude/rules/`:
- code-style.md — Python/TypeScript conventions
- testing.md — pytest/React Testing patterns
- api-conventions.md — REST API standards
- commit-workflow.md — Git conventions
- security.md — API keys, LLM safety
