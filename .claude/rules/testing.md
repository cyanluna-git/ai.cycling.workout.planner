# testing.md - Testing Conventions

## Backend Testing (pytest + FastAPI)

### Test Structure
- tests/unit/ — Unit tests (no external deps)
- tests/integration/ — Integration tests (with Supabase/LLM)
- tests/fixtures/ — Shared pytest fixtures

### pytest Configuration
- **Runner**: pytest
- **Async mode**: asyncio_mode = "auto"
- **Coverage**: 80% minimum
- **Command**: pytest tests/ -v --tb=short --cov=src --cov=api

### Test Naming
- test_module_scenario_expected() — descriptive

### Mocking External Services
```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.fixture
def mock_llm():
    with patch("src.clients.llm.call_llm", new_callable=AsyncMock) as mock:
        mock.return_value = {"workout": ".."}
        yield mock
```

### LLM Testing
- Mock Groq/Gemini calls (don"t call real APIs in tests)
- Test fallback chain logic
- Validate output parsing

## Frontend Testing (Vitest + React Testing Library)

### Unit Tests
```tsx
import { render, screen } from "@testing-library/react";

describe("WorkoutCard", () => {
  it("renders workout duration", () => {
    render(<WorkoutCard workout={mockWorkout} />);
    expect(screen.getByText(/60 min/)).toBeInTheDocument();
  });
});
```

## Coverage Requirements
- api/: 80%+
- src/services/: 85%+
- src/clients/: 90%+ (critical)
