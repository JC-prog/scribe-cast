import re

_UNSAFE_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_MAX_LENGTH = 150


def sanitize_filename(name: str) -> str:
    """Strip characters unsafe for a filesystem path and cap length, for
    turning arbitrary text (e.g. a downloaded video's title) into a filename."""
    cleaned = _UNSAFE_CHARS.sub("", name).strip(" .")
    return cleaned[:_MAX_LENGTH] or "download"
