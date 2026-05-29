"""Tests for the request-logging persistence decision.

Regression guard: a misconfigured Intervals.icu webhook secret once flooded
``api_request_logs`` with ~870k rows (1.2 GB) of 403 responses. The webhook
path and expected auth-failure statuses must never be persisted.
"""

import sys
import types

# Stub supabase so importing the middleware module does not require the package.
fake_supabase = types.ModuleType("supabase")
fake_supabase.create_client = lambda *args, **kwargs: None
fake_supabase.Client = object
sys.modules.setdefault("supabase", fake_supabase)

from api.middleware import body_for_log, should_persist_log


def test_success_responses_are_not_logged() -> None:
    assert should_persist_log("/api/fitness", 200) is False
    assert should_persist_log("/api/workout/today", 201) is False


def test_webhook_path_is_never_logged() -> None:
    # The flood source: legit Intervals.icu webhooks rejected with 403.
    assert should_persist_log("/api/webhooks/intervals", 403) is False
    # Even server errors on the webhook path are skipped (fire-and-forget).
    assert should_persist_log("/api/webhooks/intervals", 500) is False


def test_expected_auth_failures_are_not_logged() -> None:
    assert should_persist_log("/api/settings", 401) is False
    assert should_persist_log("/api/plans/today", 403) is False


def test_server_errors_are_logged() -> None:
    assert should_persist_log("/api/weekly-calendar", 500) is True
    assert should_persist_log("/api/plans/weekly/generate", 502) is True


def test_other_client_errors_are_logged() -> None:
    assert should_persist_log("/api/plans/weekly/generate", 400) is True
    assert should_persist_log("/api/plans/weekly/xyz", 404) is True


def test_request_body_kept_only_for_server_errors() -> None:
    body = {"duration": 60}
    # 5xx: keep the body for debugging.
    assert body_for_log(body, 500) == body
    assert body_for_log(body, 502) == body
    # 4xx: drop the body to save space.
    assert body_for_log(body, 400) is None
    assert body_for_log(body, 404) is None
