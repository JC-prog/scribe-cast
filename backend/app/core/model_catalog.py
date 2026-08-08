"""
Static catalog of faster-whisper model sizes. Deliberately has no dependency
on faster_whisper/ctranslate2 itself, so the API container (which never
imports those ML libraries) can serve /api/models without pulling them in.
"""

MODEL_CATALOG: list[dict[str, str]] = [
    {"size": "tiny", "label": "Tiny", "hint": "Fastest, lowest accuracy, ~1GB VRAM"},
    {"size": "base", "label": "Base", "hint": "Fast, ~1GB VRAM"},
    {"size": "small", "label": "Small", "hint": "Balanced speed/accuracy, ~2GB VRAM"},
    {"size": "medium", "label": "Medium", "hint": "Higher accuracy, ~5GB VRAM"},
    {"size": "large-v3", "label": "Large v3", "hint": "Best accuracy, slowest, ~10GB VRAM"},
]

MODEL_SIZES = {entry["size"] for entry in MODEL_CATALOG}


def list_models() -> list[dict[str, str]]:
    return MODEL_CATALOG


def is_valid_model_size(size: str) -> bool:
    return size in MODEL_SIZES
