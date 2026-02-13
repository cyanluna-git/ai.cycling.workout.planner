-- Weekly Availability Migration
-- Adds weekly_availability column to user_settings

ALTER TABLE user_settings 
ADD COLUMN IF NOT EXISTS weekly_availability JSONB DEFAULT '{
  "0": "available",
  "1": "available", 
  "2": "available",
  "3": "available",
  "4": "available",
  "5": "available",
  "6": "available"
}'::jsonb;

COMMENT ON COLUMN user_settings.weekly_availability IS 
'요일별 운동 가능 여부 (0=Mon, 6=Sun): available | unavailable | rest';
