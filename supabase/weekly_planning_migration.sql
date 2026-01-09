-- Weekly Workout Planning System Migration
-- Run this in Supabase SQL Editor

-- ============================================
-- 1. Extend user_settings table
-- ============================================

-- Add new columns for weekly planning
ALTER TABLE user_settings 
ADD COLUMN IF NOT EXISTS training_style VARCHAR(50) DEFAULT 'auto',
ADD COLUMN IF NOT EXISTS preferred_duration INTEGER DEFAULT 60,
ADD COLUMN IF NOT EXISTS weekly_plan_enabled BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS weekly_plan_day INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS exclude_barcode_workouts BOOLEAN DEFAULT false;

COMMENT ON COLUMN user_settings.training_style IS 'Training philosophy: auto, polarized, norwegian, sweetspot, threshold, endurance';
COMMENT ON COLUMN user_settings.preferred_duration IS 'Preferred workout duration in minutes';
COMMENT ON COLUMN user_settings.weekly_plan_enabled IS 'Enable automatic weekly workout plan generation';
COMMENT ON COLUMN user_settings.weekly_plan_day IS 'Day to generate weekly plan (0=Sunday, 1=Monday, ...)';


-- ============================================
-- 2. Create weekly_plans table
-- ============================================

CREATE TABLE IF NOT EXISTS weekly_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    week_start DATE NOT NULL,  -- Monday of the week
    week_end DATE NOT NULL,    -- Sunday of the week
    status VARCHAR(20) DEFAULT 'active',  -- active, completed, cancelled
    total_planned_tss INTEGER,
    training_style VARCHAR(50),  -- Style used for this plan
    generation_prompt TEXT,      -- Store the prompt used for debugging
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, week_start)
);

CREATE INDEX IF NOT EXISTS idx_weekly_plans_user_week ON weekly_plans(user_id, week_start);
CREATE INDEX IF NOT EXISTS idx_weekly_plans_status ON weekly_plans(status);

COMMENT ON TABLE weekly_plans IS 'Weekly workout plans generated automatically or manually';


-- ============================================
-- 3. Create daily_workouts table
-- ============================================

CREATE TABLE IF NOT EXISTS daily_workouts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id UUID REFERENCES weekly_plans(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    workout_date DATE NOT NULL,
    
    -- Planned workout (generated on Sunday)
    planned_name VARCHAR(255),
    planned_type VARCHAR(50),  -- Endurance, Threshold, VO2max, Recovery, Rest
    planned_duration INTEGER,
    planned_tss INTEGER,
    planned_description TEXT,
    planned_steps JSONB,
    planned_modules JSONB,     -- Module keys used
    planned_rationale TEXT,    -- AI's reasoning
    planned_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Actual workout (if regenerated based on condition)
    actual_name VARCHAR(255),
    actual_type VARCHAR(50),
    actual_duration INTEGER,
    actual_tss INTEGER,
    actual_description TEXT,
    actual_steps JSONB,
    actual_modules JSONB,
    actual_generated_at TIMESTAMPTZ,
    regeneration_reason TEXT,  -- Why was it regenerated
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'planned',  -- planned, regenerated, completed, skipped
    intervals_event_id INTEGER,            -- Intervals.icu event ID when uploaded
    completed_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, workout_date)
);

CREATE INDEX IF NOT EXISTS idx_daily_workouts_user_date ON daily_workouts(user_id, workout_date);
CREATE INDEX IF NOT EXISTS idx_daily_workouts_plan ON daily_workouts(plan_id);
CREATE INDEX IF NOT EXISTS idx_daily_workouts_status ON daily_workouts(status);

COMMENT ON TABLE daily_workouts IS 'Individual daily workouts within weekly plans';


-- ============================================
-- 4. Create job_queue table
-- ============================================

CREATE TABLE IF NOT EXISTS job_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_type VARCHAR(50) NOT NULL,  -- weekly_plan_generation, workout_sync, etc.
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, processing, completed, failed
    priority INTEGER DEFAULT 0,     -- Higher = process first
    payload JSONB,                  -- Additional job data
    scheduled_at TIMESTAMPTZ NOT NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_job_queue_status_scheduled ON job_queue(status, scheduled_at);
CREATE INDEX IF NOT EXISTS idx_job_queue_user ON job_queue(user_id);

COMMENT ON TABLE job_queue IS 'Background job queue for async processing';


-- ============================================
-- 5. Enable Row Level Security
-- ============================================

ALTER TABLE weekly_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_workouts ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_queue ENABLE ROW LEVEL SECURITY;


-- ============================================
-- 6. RLS Policies for weekly_plans
-- ============================================

CREATE POLICY "Users can view own weekly plans" ON weekly_plans
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own weekly plans" ON weekly_plans
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own weekly plans" ON weekly_plans
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own weekly plans" ON weekly_plans
    FOR DELETE USING (auth.uid() = user_id);


-- ============================================
-- 7. RLS Policies for daily_workouts
-- ============================================

CREATE POLICY "Users can view own daily workouts" ON daily_workouts
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own daily workouts" ON daily_workouts
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own daily workouts" ON daily_workouts
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own daily workouts" ON daily_workouts
    FOR DELETE USING (auth.uid() = user_id);


-- ============================================
-- 8. Service role policies for job_queue
-- ============================================

-- job_queue is only accessed by service role (backend), not users directly
CREATE POLICY "Service role full access to job_queue" ON job_queue
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');


-- ============================================
-- 9. Helper functions
-- ============================================

-- Get current week's Monday date
CREATE OR REPLACE FUNCTION get_week_start(check_date DATE DEFAULT CURRENT_DATE)
RETURNS DATE AS $$
BEGIN
    -- ISO week starts on Monday
    RETURN check_date - EXTRACT(ISODOW FROM check_date)::INTEGER + 1;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Get current week's Sunday date  
CREATE OR REPLACE FUNCTION get_week_end(check_date DATE DEFAULT CURRENT_DATE)
RETURNS DATE AS $$
BEGIN
    RETURN get_week_start(check_date) + 6;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to new tables
DROP TRIGGER IF EXISTS update_weekly_plans_updated_at ON weekly_plans;
CREATE TRIGGER update_weekly_plans_updated_at
    BEFORE UPDATE ON weekly_plans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_daily_workouts_updated_at ON daily_workouts;
CREATE TRIGGER update_daily_workouts_updated_at
    BEFORE UPDATE ON daily_workouts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ============================================
-- 10. Migration complete confirmation
-- ============================================

DO $$
BEGIN
    RAISE NOTICE 'Weekly Planning Migration completed successfully!';
    RAISE NOTICE 'Tables created: weekly_plans, daily_workouts, job_queue';
    RAISE NOTICE 'Columns added to user_settings: training_style, preferred_duration, weekly_plan_enabled, weekly_plan_day';
END $$;
