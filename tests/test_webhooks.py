"""Tests for Intervals.icu webhook receiver endpoint."""

import sys
import types
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

fake_supabase = types.ModuleType("supabase")
fake_supabase.create_client = lambda *args, **kwargs: None
fake_supabase.Client = object
sys.modules.setdefault("supabase", fake_supabase)

import api.routers.webhooks as webhooks_mod

SECRET = "test-secret-123"


def _make_app() -> FastAPI:
    """Create a minimal FastAPI app with only the webhook router."""
    app = FastAPI()
    app.include_router(webhooks_mod.router, prefix="/api")
    return app


def _webhook_payload(events: list | None = None) -> dict:
    """Build a webhook payload."""
    if events is None:
        events = [
            {
                "athlete_id": "i154786",
                "type": "ACTIVITY_UPLOADED",
                "timestamp": "2024-12-06T06:40:47.011+00:00",
            }
        ]
    return {"secret": SECRET, "events": events}


@pytest.fixture(autouse=True)
def _set_webhook_secret():
    """Ensure webhook secret is set for all tests (unless overridden)."""
    original = webhooks_mod.INTERVALS_WEBHOOK_SECRET
    webhooks_mod.INTERVALS_WEBHOOK_SECRET = SECRET
    yield
    webhooks_mod.INTERVALS_WEBHOOK_SECRET = original


@pytest.fixture
def client() -> TestClient:
    """Create a test client with webhook router."""
    return TestClient(_make_app())


class TestWebhookEndpoint:
    """Tests for POST /api/webhooks/intervals."""

    @patch("api.routers.webhooks.get_user_id_by_athlete_id", new_callable=AsyncMock)
    @patch("api.routers.webhooks.clear_user_cache")
    def test_webhook_valid_activity_uploaded(
        self, mock_clear, mock_lookup, client
    ):
        """Valid ACTIVITY_UPLOADED event clears full user cache."""
        mock_lookup.return_value = "user-uuid-123"

        response = client.post(
            "/api/webhooks/intervals",
            json=_webhook_payload(),
        )

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        mock_lookup.assert_called_once_with("i154786")
        # ACTIVITY_UPLOADED clears entire cache (keys=None)
        mock_clear.assert_called_once_with("user-uuid-123", keys=None)

    @patch("api.routers.webhooks.get_user_id_by_athlete_id", new_callable=AsyncMock)
    @patch("api.routers.webhooks.clear_user_cache")
    def test_webhook_valid_activity_analyzed(
        self, mock_clear, mock_lookup, client
    ):
        """Valid ACTIVITY_ANALYZED event clears full user cache."""
        mock_lookup.return_value = "user-uuid-123"

        response = client.post(
            "/api/webhooks/intervals",
            json=_webhook_payload(
                events=[{"athlete_id": "i154786", "type": "ACTIVITY_ANALYZED"}]
            ),
        )

        assert response.status_code == 200
        mock_clear.assert_called_once_with("user-uuid-123", keys=None)

    @patch("api.routers.webhooks.get_user_id_by_athlete_id", new_callable=AsyncMock)
    @patch("api.routers.webhooks.clear_user_cache")
    def test_webhook_valid_wellness_updated(
        self, mock_clear, mock_lookup, client
    ):
        """WELLNESS_UPDATED clears only wellness-related cache keys."""
        mock_lookup.return_value = "user-uuid-456"

        response = client.post(
            "/api/webhooks/intervals",
            json=_webhook_payload(
                events=[{"athlete_id": "i999", "type": "WELLNESS_UPDATED"}]
            ),
        )

        assert response.status_code == 200
        mock_clear.assert_called_once_with(
            "user-uuid-456",
            keys=["fitness:complete", "fitness:wellness"],
        )

    @patch("api.routers.webhooks.get_user_id_by_athlete_id", new_callable=AsyncMock)
    @patch("api.routers.webhooks.clear_user_cache")
    def test_webhook_valid_calendar_updated(
        self, mock_clear, mock_lookup, client
    ):
        """CALENDAR_UPDATED clears only calendar cache key."""
        mock_lookup.return_value = "user-uuid-789"

        response = client.post(
            "/api/webhooks/intervals",
            json=_webhook_payload(
                events=[{"athlete_id": "i111", "type": "CALENDAR_UPDATED"}]
            ),
        )

        assert response.status_code == 200
        mock_clear.assert_called_once_with(
            "user-uuid-789",
            keys=["calendar"],
        )

    def test_webhook_invalid_secret(self, client):
        """Wrong Authorization header returns 403."""
        response = client.post(
            "/api/webhooks/intervals",
            json={**_webhook_payload(), "secret": "wrong-secret"},
        )

        assert response.status_code == 403

    def test_webhook_missing_secret_field(self, client):
        """Missing secret field returns 200 because payload parsing fails."""
        response = client.post(
            "/api/webhooks/intervals",
            json={"events": _webhook_payload()["events"]},
        )

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    @patch("api.routers.webhooks.get_user_id_by_athlete_id", new_callable=AsyncMock)
    @patch("api.routers.webhooks.clear_user_cache")
    def test_webhook_unknown_athlete(
        self, mock_clear, mock_lookup, client
    ):
        """Unknown athlete_id is silently ignored, returns 200."""
        mock_lookup.return_value = None

        response = client.post(
            "/api/webhooks/intervals",
            json=_webhook_payload(
                events=[{"athlete_id": "i000000", "type": "ACTIVITY_UPLOADED"}]
            ),
        )

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        mock_clear.assert_not_called()

    @patch("api.routers.webhooks.get_user_id_by_athlete_id", new_callable=AsyncMock)
    @patch("api.routers.webhooks.clear_user_cache")
    def test_webhook_unknown_event_type(
        self, mock_clear, mock_lookup, client
    ):
        """Unsupported event type is ignored, returns 200."""
        response = client.post(
            "/api/webhooks/intervals",
            json=_webhook_payload(
                events=[{"athlete_id": "i154786", "type": "SOME_FUTURE_EVENT"}]
            ),
        )

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        mock_lookup.assert_not_called()
        mock_clear.assert_not_called()

    def test_webhook_malformed_payload(self, client):
        """Malformed JSON returns 200 to prevent Intervals.icu retries."""
        response = client.post(
            "/api/webhooks/intervals",
            content=b"not-json{{{",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_webhook_missing_secret_env(self):
        """If INTERVALS_WEBHOOK_SECRET is not set, returns 503."""
        webhooks_mod.INTERVALS_WEBHOOK_SECRET = None
        test_client = TestClient(_make_app())

        response = test_client.post(
            "/api/webhooks/intervals",
            json=_webhook_payload(),
        )

        assert response.status_code == 503

    @patch("api.routers.webhooks.get_user_id_by_athlete_id", new_callable=AsyncMock)
    @patch("api.routers.webhooks.clear_user_cache")
    def test_webhook_multiple_events(
        self, mock_clear, mock_lookup, client
    ):
        """Multiple events in a single payload are all processed."""
        mock_lookup.return_value = "user-uuid-multi"

        response = client.post(
            "/api/webhooks/intervals",
            json=_webhook_payload(
                events=[
                    {"athlete_id": "i100", "type": "ACTIVITY_UPLOADED"},
                    {"athlete_id": "i100", "type": "WELLNESS_UPDATED"},
                    {"athlete_id": "i100", "type": "CALENDAR_UPDATED"},
                ]
            ),
        )

        assert response.status_code == 200
        assert mock_clear.call_count == 3

    def test_webhook_missing_events_field(self, client):
        """Payload without events field returns 200 (parse error handled)."""
        response = client.post(
            "/api/webhooks/intervals",
            json={"secret": SECRET, "other_field": "value"},
        )

        # Pydantic validation fails → caught as parse error → 200
        assert response.status_code == 200
