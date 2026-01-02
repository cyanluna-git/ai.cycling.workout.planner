-- Admin Dashboard Schema Migration
-- Execute this in Supabase SQL Editor

-- ============================================
-- 1. API Request Logs Table
-- ============================================

CREATE TABLE IF NOT EXISTS api_request_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  method TEXT NOT NULL,
  path TEXT NOT NULL,
  status_code INTEGER,
  response_time_ms INTEGER,
  ip_address TEXT,
  user_agent TEXT,
  request_body JSONB,
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_api_logs_created_at ON api_request_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_api_logs_user_id ON api_request_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_api_logs_path ON api_request_logs(path);
CREATE INDEX IF NOT EXISTS idx_api_logs_status_code ON api_request_logs(status_code);

-- ============================================
-- 2. Add is_admin Column to user_settings
-- ============================================

ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;

-- ============================================
-- 3. Admin Statistics View (optional helper)
-- ============================================

-- Daily workout generation stats
CREATE OR REPLACE VIEW admin_daily_stats AS
SELECT 
  DATE(created_at) as date,
  COUNT(*) as total_api_calls,
  COUNT(DISTINCT user_id) as unique_users,
  SUM(CASE WHEN path LIKE '%/workout%' AND method = 'POST' THEN 1 ELSE 0 END) as workout_generations,
  AVG(response_time_ms) as avg_response_time
FROM api_request_logs
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- ============================================
-- 4. RLS Policies for api_request_logs
-- ============================================

-- Enable RLS
ALTER TABLE api_request_logs ENABLE ROW LEVEL SECURITY;

-- Service role can do everything (for backend logging)
CREATE POLICY "Service role full access" ON api_request_logs
  FOR ALL USING (auth.role() = 'service_role');

-- Admins can view all logs
CREATE POLICY "Admins can view all logs" ON api_request_logs
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM user_settings 
      WHERE user_id = auth.uid() AND is_admin = TRUE
    )
  );
