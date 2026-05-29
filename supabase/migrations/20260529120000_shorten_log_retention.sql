-- Shorten api_request_logs retention from 30 to 14 days.
-- cron.schedule upserts by job name, so this replaces the previous schedule
-- registered in 20260405044201_add_log_cleanup_cron.sql.
SELECT cron.schedule(
  'cleanup-api-request-logs',
  '0 3 * * 0',
  $$DELETE FROM public.api_request_logs WHERE created_at < NOW() - INTERVAL '14 days'$$
);
