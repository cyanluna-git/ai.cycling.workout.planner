# Frontend Module

React 19 + TypeScript SPA for AI Cycling Coach workout planning and visualization.

## Overview

Vite-based React 19 application (port 3101) with premium UI for workout generation, athlete fitness visualization, and integration with Intervals.icu.

## Tech Stack

- **Framework**: React 19 + TypeScript 5
- **Bundler**: Vite 7 (ESM)
- **Styling**: Tailwind CSS 4 + Shadcn UI
- **State**: React Query (server), Zustand (client)
- **Visualization**: Recharts (fitness metrics)
- **HTTP**: Axios with Supabase auth interceptor
- **Testing**: Vitest + React Testing Library

## Key Modules

- `src/pages/` — Route pages:
  - Dashboard — Fitness metrics + workout history
  - Settings — User preferences, Intervals.icu auth
  - Admin — LLM model management, logs
- `src/components/` — Reusable UI:
  - FitnessCard — CTL/ATL/TSB display
  - WorkoutForm — Generation form
  - WorkoutPreview — ZWO rendering
- `src/hooks/` — Custom hooks:
  - `useDashboard()` — Fitness + workouts
  - `useFitness()` — Intervals.icu sync
- `src/lib/api.ts` — Axios client with Supabase auth
- `src/types/` — TypeScript interfaces

## Commands

```bash
pnpm dev                # Dev server (port 3101)
pnpm build              # Production build
pnpm lint               # ESLint
pnpm test               # Vitest
```

## Environment

- `VITE_SUPABASE_URL`: Supabase project URL
- `VITE_SUPABASE_KEY`: Supabase anon key
- `VITE_API_URL`: Backend API (http://localhost:8005)

## UI Patterns

- **Glassmorphism**: Blurred backgrounds, semi-transparent cards
- **Vibrant colors**: Gradients (cyan → purple)
- **Smooth transitions**: 300-500ms animations
- **Responsive**: Mobile-first, dark mode via Tailwind

## Parent Rules

Inherit from `@../../.claude/rules/`:
- code-style.md — React/TypeScript + UI patterns
- testing.md — Vitest + RTL patterns
- api-conventions.md — API client design
- commit-workflow.md — Git conventions
- security.md — Auth tokens, sensitive data handling
