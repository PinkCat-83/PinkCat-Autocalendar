"""
language.py
Language manager for AutoCalendario.
Loads translations from language/translations.csv.
Each column header (except 'key') is treated as an available language.
"""

import csv
import json
import locale
from pathlib import Path

BASE_DIR      = Path(__file__).parent.parent
CSV_PATH      = BASE_DIR / "language" / "translations.csv"
SETTINGS_PATH = BASE_DIR / "data" / "settings.json"

_translations: dict[str, dict[str, str]] = {}   # lang -> {key -> value}
_languages: list[str] = []
_current: str = "English"


def load(path: Path = CSV_PATH) -> list[str]:
    """
    Reads the CSV and builds the translation tables.
    Returns the list of available language names (column headers).
    """
    global _translations, _languages

    _translations = {}
    _languages = []

    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        # Every column except 'key' is a language
        _languages = [col for col in reader.fieldnames if col != "key"]
        for lang in _languages:
            _translations[lang] = {}
        for row in reader:
            key = row["key"]
            for lang in _languages:
                _translations[lang][key] = row.get(lang, key)

    _detect_system_language()
    _load_saved_language()
    return _languages


def _detect_system_language() -> None:
    """
    Tries to match the OS locale to an available language.
    Matching is case-insensitive; checks whether a known locale prefix
    corresponds to a fragment of any language name in translations.csv.
    Falls back to the first available language if nothing matches.
    """
    global _current

    # locale.getlocale() returns e.g. ('es_ES', 'UTF-8') or (None, None)
    system_locale = (locale.getlocale()[0] or "").lower()

    # Map common ISO-639 prefixes to fragments likely to appear in column headers
    LOCALE_HINTS: list[tuple[str, str]] = [
        ("es", "spanish"), ("es", "español"),
        ("en", "english"),
        ("fr", "french"),  ("fr", "français"),
        ("de", "german"),  ("de", "deutsch"),
        ("it", "italian"), ("it", "italiano"),
        ("pt", "portuguese"), ("pt", "português"),
        ("nl", "dutch"),
        ("pl", "polish"),
        ("ru", "russian"),
        ("ca", "catalan"), ("ca", "català"),
    ]

    locale_prefix = system_locale[:2]  # 'es', 'en', 'fr', …

    for prefix, fragment in LOCALE_HINTS:
        if locale_prefix == prefix:
            for available_lang in _languages:
                if fragment in available_lang.lower():
                    _current = available_lang
                    return

    # Direct substring match as a last resort
    for available_lang in _languages:
        if available_lang.lower() in system_locale:
            _current = available_lang
            return

    # Keep the first available language if nothing matched
    if _languages:
        _current = _languages[0]


def _load_saved_language() -> None:
    """Override detected language with the user's saved preference, if any."""
    global _current
    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        saved = data.get("language", "")
        if saved in _translations:
            _current = saved
    except Exception:
        pass  # No settings file yet, or unreadable — keep detected language


def set_language(lang: str) -> None:
    """Sets the active language and persists the choice to settings.json."""
    global _current
    if lang in _translations:
        _current = lang
        _save_language(lang)
    else:
        print(f"[Language] Unknown language '{lang}', keeping '{_current}'.")


def _save_language(lang: str) -> None:
    try:
        data = {}
        if SETTINGS_PATH.exists():
            try:
                data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            except Exception:
                pass
        data["language"] = lang
        SETTINGS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                                 encoding="utf-8")
    except Exception as e:
        print(f"[Language] Could not save settings: {e}")


def get(key: str, **kwargs) -> str:
    """
    Returns the translation for key in the current language.
    Falls back to the key itself if not found.
    Supports simple keyword substitution: get('confirm_delete_msg', name='My Course')
    """
    text = _translations.get(_current, {}).get(key, key)
    if kwargs:
        for k, v in kwargs.items():
            text = text.replace(f"{{{k}}}", str(v))
    return text


def available() -> list[str]:
    """Returns the list of available language names."""
    return _languages


def current() -> str:
    """Returns the currently active language name."""
    return _current
