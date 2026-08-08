from dataclasses import dataclass
from pathlib import Path

from app.config import ALLOWED_VIDEO_EXTENSIONS
from app.core.errors import FolderNotFoundError, InvalidPathError
from app.core.paths import has_existing_subtitle


@dataclass
class DiscoveredVideo:
    absolute_path: Path
    relative_path: Path
    size_bytes: int
    existing_srt: bool


def _is_video(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in ALLOWED_VIDEO_EXTENSIONS


def _to_discovered(path: Path, root: Path) -> DiscoveredVideo:
    return DiscoveredVideo(
        absolute_path=path,
        relative_path=path.relative_to(root),
        size_bytes=path.stat().st_size,
        existing_srt=has_existing_subtitle(path),
    )


def scan_folder(root: Path) -> list[DiscoveredVideo]:
    """Recursively discover videos, limited to `root` itself and one level of subfolders."""
    if not root.exists() or not root.is_dir():
        raise FolderNotFoundError(f"Not a directory: {root}")

    discovered: list[DiscoveredVideo] = []

    # Depth 0: files directly in root.
    for entry in root.iterdir():
        if _is_video(entry):
            discovered.append(_to_discovered(entry, root))

    # Depth 1: files directly in each immediate subfolder.
    for entry in root.iterdir():
        if entry.is_dir():
            for nested in entry.iterdir():
                if _is_video(nested):
                    discovered.append(_to_discovered(nested, root))

    discovered.sort(key=lambda video: str(video.relative_path))
    return discovered


def resolve_selected_videos(root: Path, requested_paths: list[str]) -> list[Path]:
    """
    Defends /api/folder/transcribe against stale UI state or a tampered
    request pointing outside the scanned root: each path must resolve to
    somewhere inside `root` and must still exist.
    """
    resolved_root = root.resolve()
    resolved: list[Path] = []

    for raw_path in requested_paths:
        candidate = Path(raw_path).resolve()
        if resolved_root not in candidate.parents and candidate != resolved_root:
            raise InvalidPathError(f"Path is outside the scanned folder: {raw_path}")
        if not candidate.is_file():
            raise InvalidPathError(f"Video no longer exists: {raw_path}")
        resolved.append(candidate)

    return resolved
