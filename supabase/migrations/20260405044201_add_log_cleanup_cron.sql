-- Enable pg_cron extension (no-op if already enabled)
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Auto-cleanup api_request_logs: keep 30 days, run every Sunday at 03:00 UTC
SELECT cron.schedule(
  'cleanup-api-request-logs',
  '0 3 * * 0',
  $$DELETE FROM public.api_request_logs WHERE created_at < NOW() - INTERVAL '30 days'$$
);

-- Auto-cleanup audit_logs: keep 90 days, run every Sunday at 03:05 UTC
SELECT cron.schedule(
  'cleanup-audit-logs',
  '5 3 * * 0',
  $$DELETE FROM public.audit_logs WHERE created_at < NOW() - INTERVAL '90 days'$$
);
