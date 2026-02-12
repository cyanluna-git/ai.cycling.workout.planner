# security.md - Security Guidelines

## Environment Variables

### Sensitive Data (Never commit)
- GROQ_API_KEY
- GEMINI_API_KEY
- INTERVALS_API_KEY
- SUPABASE_KEY
- VERCEL_AI_GATEWAY_URL

Use `.env` (gitignored) for development.

## API Key Security

### Key Management
- Rotate API keys every 90 days
- Store in environment variables only
- Never log API keys or responses
- Revoke immediately if exposed

### LLM API Keys
- Groq: Use API key directly (no secrets rotation needed)
- Gemini: Use API key for fallback
- Vercel AI Gateway: Routes calls securely

## Authentication & Authorization

### Supabase Auth
- JWT tokens expire after 1 hour
- Refresh tokens valid 30 days
- User UUID in token claims
- Client-side: Store tokens in secure localStorage

### Role-Based Access
- Users can only access own workouts/settings
- Admin endpoints protected

## Input Validation

### Data Validation
- All input validated with Pydantic models
- Duration: 15-180 minutes
- TSB range: -60 to +60
- File uploads: JSON schema validation

### LLM Prompt Injection Prevention
- Never interpolate user input directly in prompts
- Use structured prompts with {{placeholders}}
- Validate parsed JSON output
- Sanitize athlete names in prompts

## External API Security

### Intervals.icu Integration
- Rate limit: 1 request per second
- Store auth token securely (in Supabase)
- Validate responses before caching

## Logging & Monitoring

### What NOT to Log
- API keys, tokens, secrets
- Athlete personal data (names, ages)
- LLM API responses (prompts + completions)
- Request/response bodies containing tokens

### What to Log
- Workout generation requests (metrics only)
- LLM fallback events
- API errors (without sensitive data)
- Rate limiting events

### Log Levels
- DEBUG: Structured data (no secrets)
- INFO: Important events
- WARNING: Recoverable errors
- ERROR: Errors (app continues)
- CRITICAL: System failures
