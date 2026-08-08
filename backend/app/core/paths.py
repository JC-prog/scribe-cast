from pathlib import Path


def derive_output_path(video_path: Path) -> Path:
    """Same directory and basename as the source video, with a .srt suffix."""
    return video_path.with_suffix(".srt")


def has_existing_subtitle(video_path: Path) -> bool:
    return derive_output_path(video_path).exists()
