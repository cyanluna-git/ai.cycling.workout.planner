import asyncio
import sys
import types

fake_supabase = types.ModuleType("supabase")
fake_supabase.create_client = lambda *args, **kwargs: None
fake_supabase.Client = object
sys.modules.setdefault("supabase", fake_supabase)

from api.services.user_api_service import get_user_profile, get_user_settings


class _Query:
    def __init__(self, data):
        self._data = data

    def select(self, _fields):
        return self

    def eq(self, _key, _value):
        return self

    def maybe_single(self):
        return self

    def execute(self):
        return types.SimpleNamespace(data=self._data)


class _SupabaseStub:
    def __init__(self, data):
        self._data = data

    def table(self, _name):
        return _Query(self._data)


def test_get_user_settings_returns_extended_training_fields(monkeypatch):
    monkeypatch.setattr(
        "api.services.user_api_service.get_supabase_admin_client",
        lambda: _SupabaseStub(
            {
                "ftp": 245,
                "max_hr": 188,
                "lthr": 168,
                "training_goal": "Build fitness",
                "exclude_barcode_workouts": True,
                "training_style": "threshold",
                "training_focus": "recovery",
                "preferred_duration": 75,
            }
        ),
    )

    settings = asyncio.run(get_user_settings("user-1"))

    assert settings.training_style == "threshold"
    assert settings.training_focus == "recovery"
    assert settings.preferred_duration == 75


def test_get_user_profile_maps_training_style_and_focus(monkeypatch):
    monkeypatch.setattr(
        "api.services.user_api_service.get_supabase_admin_client",
        lambda: _SupabaseStub(
            {
                "ftp": 252,
                "max_hr": 190,
                "lthr": 171,
                "training_goal": "Build fitness",
                "exclude_barcode_workouts": False,
                "training_style": "polarized",
                "training_focus": "build",
                "preferred_duration": 60,
            }
        ),
    )

    profile = asyncio.run(get_user_profile("user-1"))

    assert profile.training_style == "polarized"
    assert profile.training_focus == "build"
    assert profile.ftp == 252
