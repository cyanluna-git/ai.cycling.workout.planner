-- Weekly TSS Target & Achievement System Migration
-- Run this in Supabase SQL Editor
-- Date: 2026-02-12

-- ============================================
-- 1. user_settings: weekly_tss_target
-- ============================================
ALTER TABLE user_settings 
ADD COLUMN IF NOT EXISTS weekly_tss_target INTEGER DEFAULT NULL;

COMMENT ON COLUMN user_settings.weekly_tss_target IS 'Manual weekly TSS target (200-800). NULL = auto-calculate from CTL';

-- ============================================
-- 2. weekly_plans: TSS target & achievement
-- ============================================
ALTER TABLE weekly_plans 
ADD COLUMN IF NOT EXISTS weekly_tss_target INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS total_actual_tss INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS achievement_status VARCHAR(20) DEFAULT NULL;

COMMENT ON COLUMN weekly_plans.weekly_tss_target IS 'TSS target for this week (200-800)';
COMMENT ON COLUMN weekly_plans.total_actual_tss IS 'Actual TSS achieved (sum of completed workouts)';
COMMENT ON COLUMN weekly_plans.achievement_status IS 'exceeded|achieved|partial|missed|in_progress';

-- ============================================
-- 3. Verify
-- ============================================
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'user_settings' AND column_name = 'weekly_tss_target';

SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'weekly_plans' AND column_name IN ('weekly_tss_target', 'total_actual_tss', 'achievement_status');
