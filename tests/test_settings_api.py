"""Router tests for GET /api/settings bootstrap response."""

import sys
import types

from fastapi import FastAPI
from fastapi.testclient import TestClient

fake_supabase = types.ModuleType("supabase")
fake_supabase.create_client = lambda *args, **kwargs: None
fake_supabase.Client = object
sys.modules.setdefault("supabase", fake_supabase)

import api.routers.settings as settings_mod


class _FakeResult:
    def __init__(self, data):
        self.data = data


class _FakeTable:
    def __init__(self, data):
        self._data = data

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def maybe_single(self):
        return self

    def execute(self):
        return _FakeResult(self._data)


class _FakeSupabase:
    def __init__(self, table_data):
        self._table_data = table_data

    def table(self, name: str):
        return _FakeTable(self._table_data.get(name, {}))


def _make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(settings_mod.router, prefix="/api")
    app.dependency_overrides[settings_mod.get_current_user] = lambda: {
        "id": "user-123",
        "email": "rider@example.com",
    }
    return app


def _client_with_tables(monkeypatch, *, user_settings=None, user_api_keys=None) -> TestClient:
    fake_supabase = _FakeSupabase(
        {
            "user_settings": user_settings or {},
            "user_api_keys": user_api_keys or {},
        }
    )
    monkeypatch.setattr(settings_mod, "get_supabase_admin_client", lambda: fake_supabase)
    return TestClient(_make_app())


def test_get_settings_returns_oauth_connection_details(monkeypatch):
    client = _client_with_tables(
        monkeypatch,
        user_settings={"ftp": 255},
        user_api_keys={
            "intervals_access_token": "oauth-token",
            "intervals_oauth_athlete_id": "i154786",
        },
    )

    response = client.get("/api/settings")

    assert response.status_code == 200
    data = response.json()
    assert data["api_keys_configured"] is True
    assert data["intervals_connection"] == {
        "connected": True,
        "method": "oauth",
        "athlete_id": "i154786",
    }
    assert data["settings"]["ftp"] == 255


def test_get_settings_returns_legacy_api_key_connection_details(monkeypatch):
    client = _client_with_tables(
        monkeypatch,
        user_api_keys={
            "intervals_api_key": "legacy-key",
            "athlete_id": "legacy-42",
        },
    )

    response = client.get("/api/settings")

    assert response.status_code == 200
    data = response.json()
    assert data["api_keys_configured"] is True
    assert data["intervals_connection"] == {
        "connected": True,
        "method": "api_key",
        "athlete_id": "legacy-42",
    }


def test_get_settings_returns_disconnected_bootstrap_defaults(monkeypatch):
    client = _client_with_tables(
        monkeypatch,
        user_settings={},
        user_api_keys={},
    )

    response = client.get("/api/settings")

    assert response.status_code == 200
    data = response.json()
    assert data["api_keys_configured"] is False
    assert data["intervals_connection"] == {
        "connected": False,
        "method": "none",
        "athlete_id": None,
    }
    assert data["settings"]["ftp"] == 200
    assert data["settings"]["weekly_availability"]["0"] == "available"


def test_get_settings_prefers_oauth_when_both_credential_types_exist(monkeypatch):
    client = _client_with_tables(
        monkeypatch,
        user_api_keys={
            "intervals_access_token": "oauth-token",
            "intervals_oauth_athlete_id": "oauth-7",
            "intervals_api_key": "legacy-key",
            "athlete_id": "legacy-42",
        },
    )

    response = client.get("/api/settings")

    assert response.status_code == 200
    data = response.json()
    assert data["api_keys_configured"] is True
    assert data["intervals_connection"] == {
        "connected": True,
        "method": "oauth",
        "athlete_id": "oauth-7",
    }
