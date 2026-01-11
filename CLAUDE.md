# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Cycling Coach is a personalized workout generation platform that integrates with Intervals.icu. It uses LLMs (Groq, Gemini) to select optimal workout modules based on athlete fitness metrics (CTL/ATL/TSB) and wellness data.

**Deployment**: Frontend (Vercel) + Backend (Google Cloud Run, region: `asia-northeast3`)

## Tech Stack

- **Frontend**: React 19 + TypeScript + Vite 7, Tailwind CSS 4 + Shadcn UI, React Query, Recharts
- **Backend**: FastAPI (Python 3.11+), Supabase (PostgreSQL + Auth)
- **LLM**: Groq (primary) → Gemini 2.0/1.5 Flash (fallback) via Vercel AI Gateway
- **External API**: Intervals.icu (athlete data sync)

## Commands

### Development
```bash
python run.py              # Backend (8005) + Frontend (3005)
python run.py backend      # Backend only
python run.py frontend     # Frontend only
python run.py --docker     # Docker Compose
```

### Frontend (from /frontend)
```bash
pnpm dev                   # Dev server
pnpm build                 # TypeScript + Vite build
pnpm lint                  # ESLint
```

### Testing
```bash
pytest tests/ -v           # Run all tests
pytest tests/test_validator.py -v  # Single test file
```

## Architecture

### "Omakase" Workout System
The AI doesn't create workouts from scratch. Instead:
1. **Library**: Pre-validated modules in `src/data/` (WARMUP → MAIN → COOLDOWN)
2. **AI Selector**: LLM analyzes TSB/duration and picks optimal module combination
3. **Assembler**: Converts selection to ZWO format (Zwift XML) for Intervals.icu

### Data Flow
```
Frontend → FastAPI → Supabase (auth/settings)
                  → Intervals.icu (fitness data)
                  → LLM via Vercel AI Gateway
                  ← ZWO XML + structured steps
```

### LLM Fallback Chain
```
Groq (llama-3.3-70b-versatile)
  └→ Gemini 2.0 Flash
       └→ Gemini 1.5 Flash
```

## Key Directories

- `/api/routers/` - FastAPI endpoints (workout, fitness, plans, settings, admin)
- `/api/services/` - API-level business logic (caching, model selection)
- `/src/services/` - Core workout logic (workout_generator.py, zwo_converter.py)
- `/src/clients/` - External service clients (llm.py, intervals.py, supabase_client.py)
- `/src/data/` - Workout module library (JSON)
- `/frontend/src/pages/` - React pages (Dashboard, Settings, Admin)
- `/frontend/src/components/` - UI components (FitnessCard, WorkoutForm, etc.)
- `/frontend/src/lib/api.ts` - All API calls
- `/frontend/src/hooks/useDashboard.ts` - Dashboard state management

## Configuration

- **Frontend path alias**: `@/` → `./src/`
- **Environment**: All secrets in `.env` (never hardcode)
- **CORS**: Configured for Vercel preview deployments + localhost

## Development Rules

1. **UI Aesthetics**: Premium, modern design (glassmorphism, vibrant colors, smooth transitions)
2. **LLM calls**: Must go through Vercel AI Gateway with fallback strategy
3. **Data integrity**: Prioritize consistency between Intervals.icu and Supabase
4. **Code style**: Python follows PEP8, TypeScript follows ESLint/Prettier

## Production URLs

- Frontend: https://ai-cycling-workout-planner.vercel.app
- Backend: https://cycling-coach-backend-25085100592.asia-northeast3.run.app
- API Docs: Backend URL + `/docs`
