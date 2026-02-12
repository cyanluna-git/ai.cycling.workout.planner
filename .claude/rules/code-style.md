# code-style.md - Coding Standards

## Python (Backend / FastAPI)

### Style & Formatting
- **Line length**: 100 characters (Black configured)
- **Formatter**: Black v24+
- **Import order**: isort (Black profile)
- **Target version**: Python 3.11+

### Type Annotations
- **Required**: All function signatures must have type hints
- **Strict mypy**: disallow_untyped_defs = true

### Naming Conventions
- **Classes**: PascalCase (e.g., WorkoutGenerator, LLMClient)
- **Functions/methods**: snake_case (e.g., generate_workout, select_module)
- **Constants**: UPPER_SNAKE_CASE
- **Private attributes**: Leading underscore

### Async/Await
- Use async def for I/O-bound operations
- Never block event loop
- Await all coroutines

### LLM Integration
- All LLM calls through `src/clients/llm.py`
- Implement fallback chain (Groq → Gemini 2.0 → Gemini 1.5)
- Validate LLM output before using
- Log LLM responses for debugging

## TypeScript / React (Frontend)

### Component Patterns
- **Functional components only** (no class components)
- **Custom hooks** for shared logic (useDashboard, useFitness)
- **Memoization**: React.memo() for expensive renders

### File Structure
- src/pages/ — Route pages
- src/components/ — Reusable UI components
- src/hooks/ — Custom React hooks
- src/lib/ — API client (axios/fetch)
- src/types/ — TypeScript interfaces
- src/contexts/ — Context providers

### Premium UI
- Glassmorphism, vibrant colors, smooth transitions
- Responsive design (mobile-first)
- Dark mode support via Tailwind

## YAML Configuration

- **Indentation**: 2 spaces
- **Strings with special chars**: Double quotes
