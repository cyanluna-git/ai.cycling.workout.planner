# api-conventions.md - API Design Rules

## REST API Standards

### URL Structure
- GET    /api/workouts — List user workouts
- POST   /api/workouts — Generate new workout
- GET    /api/fitness — Get Intervals.icu data
- GET    /api/settings — Get user settings
- PATCH  /api/settings — Update user settings

### Response Format

**Success (200/201):**
```json
{
  "data": { "workout": {...}, "zwo": "<xml>" },
  "meta": { "timestamp": "2025-02-11T12:00:00Z", "version": 1 }
}
```

**Error (4xx/5xx):**
```json
{
  "error": {
    "code": "LLM_ERROR",
    "message": "Failed to generate workout after 3 retries"
  }
}
```

### HTTP Status Codes
- 200 OK — Successful GET/PATCH
- 201 Created — Successful POST (workout generated)
- 400 Bad Request — Invalid input
- 401 Unauthorized — Invalid Supabase auth
- 503 Service Unavailable — All LLM retries exhausted

## LLM Response Validation
- Always parse + validate LLM JSON output
- Fallback to default if unparseable
- Log invalid responses for debugging

## Authentication
- **Method**: Supabase JWT tokens
- **Header**: Authorization: Bearer <token>
- **Session**: Extract user_id from token claims

## Rate Limiting
- Groq: 30 requests/minute
- Gemini: 60 requests/minute
- Implement request queuing for production
