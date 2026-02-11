"""
Lightweight i18n for API responses.
Uses JSON translation files consistent with frontend approach.
"""
import json
from pathlib import Path
from typing import Optional

_translations: dict[str, dict] = {}
_fallback = "en"

def _load_translations():
    global _translations
    i18n_dir = Path(__file__).parent / "locales"
    if not i18n_dir.exists():
        return
    for f in i18n_dir.glob("*.json"):
        lang = f.stem
        with open(f, "r", encoding="utf-8") as fh:
            _translations[lang] = json.load(fh)

def t(key: str, lang: str = "en", **kwargs) -> str:
    """Translate a dot-notation key. Falls back to English."""
    if not _translations:
        _load_translations()
    parts = key.split(".")
    for try_lang in [lang, _fallback]:
        node = _translations.get(try_lang, {})
        for part in parts:
            if isinstance(node, dict):
                node = node.get(part)
            else:
                node = None
                break
        if node and isinstance(node, str):
            if kwargs:
                return node.format(**kwargs)
            return node
    return key

def get_language(accept_language: Optional[str] = None) -> str:
    """Extract preferred language from Accept-Language header."""
    if not accept_language:
        return _fallback
    for part in accept_language.split(","):
        lang = part.split(";")[0].strip().lower()
        if lang.startswith("ko"):
            return "ko"
        if lang.startswith("en"):
            return "en"
    return _fallback

_load_translations()
