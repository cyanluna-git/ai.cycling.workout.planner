"""API services package.

Keep package import side effects minimal so service submodules can be imported
independently in tests without forcing the full Supabase stack to import.
"""

from importlib import import_module

__all__ = [
    "get_user_api_keys",
    "get_user_settings",
    "get_user_intervals_client",
    "get_server_llm_client",
    "get_user_profile",
    "get_data_processor",
    "UserApiServiceError",
    "UserApiKeysData",
    "UserSettingsData",
]


def __getattr__(name):
    if name in __all__:
        module = import_module(".user_api_service", __name__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
