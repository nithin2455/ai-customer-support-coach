"""
Centralized Language Configuration for Multilingual Support.
Defines supported languages, locales, script detection, and utility helpers.
"""
from typing import Dict, List, Optional, Any
import re

SUPPORTED_LANGUAGES: List[Dict[str, str]] = [
    {
        "code": "en",
        "locale": "en-IN",
        "name": "English",
        "native_name": "English",
        "script": "Latin"
    },
    {
        "code": "hi",
        "locale": "hi-IN",
        "name": "Hindi",
        "native_name": "हिन्दी",
        "script": "Devanagari"
    },
    {
        "code": "ta",
        "locale": "ta-IN",
        "name": "Tamil",
        "native_name": "தமிழ்",
        "script": "Tamil"
    },
    {
        "code": "kn",
        "locale": "kn-IN",
        "name": "Kannada",
        "native_name": "ಕನ್ನಡ",
        "script": "Kannada"
    }
]

LANGUAGE_MAP: Dict[str, Dict[str, str]] = {
    lang["code"]: lang for lang in SUPPORTED_LANGUAGES
}

DEFAULT_LANGUAGE_CODE = "en"
DEFAULT_LOCALE = "en-IN"

# Unicode script ranges for secondary lightweight detection
SCRIPT_PATTERNS = {
    "hi": re.compile(r"[\u0900-\u097F]"),  # Devanagari
    "ta": re.compile(r"[\u0B80-\u0BFF]"),  # Tamil
    "kn": re.compile(r"[\u0C80-\u0CFF]"),  # Kannada
}


def get_language(code: Optional[str]) -> Dict[str, str]:
    """Returns language configuration dict by language code, defaulting to English."""
    if not code:
        return LANGUAGE_MAP[DEFAULT_LANGUAGE_CODE]
    norm_code = code.lower().strip()
    # Handle locale strings like 'ta-IN' or 'en_US'
    if "-" in norm_code:
        norm_code = norm_code.split("-")[0]
    elif "_" in norm_code:
        norm_code = norm_code.split("_")[0]
    return LANGUAGE_MAP.get(norm_code, LANGUAGE_MAP[DEFAULT_LANGUAGE_CODE])


def get_locale(code: Optional[str]) -> str:
    """Returns standard Indian locale for given language code (e.g., 'ta' -> 'ta-IN')."""
    return get_language(code).get("locale", DEFAULT_LOCALE)


def get_language_name(code: Optional[str]) -> str:
    """Returns English name for given language code (e.g., 'ta' -> 'Tamil')."""
    return get_language(code).get("name", "English")


def detect_text_language(text: str) -> Optional[str]:
    """
    Lightweight secondary language detection using Unicode script ranges.
    Returns language code ('hi', 'ta', 'kn') if specific script characters are found,
    or None if purely Latin or ambiguous.
    """
    if not text:
        return None

    # Check Indic scripts first
    counts = {
        lang_code: len(pattern.findall(text))
        for lang_code, pattern in SCRIPT_PATTERNS.items()
    }
    best_lang, best_count = max(counts.items(), key=lambda item: item[1])
    if best_count > 0:
        return best_lang

    return None
