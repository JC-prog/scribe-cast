"""Static language list supported by faster-whisper's underlying Whisper models."""

AUTO_DETECT = "auto"

# ISO-639-1 code -> display name, for the subset of languages Whisper supports.
SUPPORTED_LANGUAGES: dict[str, str] = {
    "en": "English",
    "zh": "Chinese",
    "de": "German",
    "es": "Spanish",
    "ru": "Russian",
    "ko": "Korean",
    "fr": "French",
    "ja": "Japanese",
    "pt": "Portuguese",
    "tr": "Turkish",
    "pl": "Polish",
    "ca": "Catalan",
    "nl": "Dutch",
    "ar": "Arabic",
    "sv": "Swedish",
    "it": "Italian",
    "id": "Indonesian",
    "hi": "Hindi",
    "fi": "Finnish",
    "vi": "Vietnamese",
    "he": "Hebrew",
    "uk": "Ukrainian",
    "el": "Greek",
    "ms": "Malay",
    "cs": "Czech",
    "ro": "Romanian",
    "da": "Danish",
    "hu": "Hungarian",
    "ta": "Tamil",
    "no": "Norwegian",
    "th": "Thai",
    "ur": "Urdu",
    "hr": "Croatian",
    "bg": "Bulgarian",
    "lt": "Lithuanian",
    "la": "Latin",
    "mi": "Maori",
    "ml": "Malayalam",
    "cy": "Welsh",
    "sk": "Slovak",
    "te": "Telugu",
    "fa": "Persian",
    "lv": "Latvian",
    "bn": "Bengali",
    "sr": "Serbian",
    "az": "Azerbaijani",
    "sl": "Slovenian",
    "et": "Estonian",
    "mk": "Macedonian",
}


def list_languages() -> list[dict[str, str]]:
    """Auto-detect sentinel first, then supported languages sorted by display name."""
    entries = [{"code": AUTO_DETECT, "label": "Auto-detect"}]
    entries += [
        {"code": code, "label": label}
        for code, label in sorted(SUPPORTED_LANGUAGES.items(), key=lambda item: item[1])
    ]
    return entries


def resolve_language(code: str) -> str | None:
    """Whisper's `language` param expects None for auto-detect, else the ISO code."""
    if code == AUTO_DETECT:
        return None
    if code not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language code: {code}")
    return code
