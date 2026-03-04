-- Add OAuth columns to user_api_keys for Intervals.icu OAuth 2.0 integration
ALTER TABLE user_api_keys
  ADD COLUMN IF NOT EXISTS intervals_access_token TEXT,
  ADD COLUMN IF NOT EXISTS intervals_oauth_athlete_id TEXT,
  ADD COLUMN IF NOT EXISTS oauth_state TEXT,
  ADD COLUMN IF NOT EXISTS oauth_state_created_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS intervals_refresh_token TEXT;
