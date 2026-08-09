import logging
from dataclasses import dataclass
from pathlib import Path

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError as YtDlpDownloadError

from app.core.errors import VideoDownloadError
from app.logging_config import get_logger, log_event

logger = get_logger("scribecast.video_downloader")


@dataclass
class DownloadResult:
    path: Path
    title: str
    source_url: str


def download_video(url: str, work_dir: Path) -> DownloadResult:
    """Download the best available audio stream for `url` into `work_dir` via yt-dlp.

    Audio-only: the transcription pipeline only ever needs an audio track,
    and ffmpeg's extract_audio step already accepts any media container, so
    there's no need to pull down a full video stream.
    """
    work_dir.mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(work_dir / "source.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
        "noprogress": True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_path = Path(ydl.prepare_filename(info))
    except YtDlpDownloadError as exc:
        log_event(logger, "video_download_failed", level=logging.ERROR, url=url, error=str(exc))
        raise VideoDownloadError(f"Could not download video from {url}: {exc}") from exc

    if not downloaded_path.is_file():
        raise VideoDownloadError(f"yt-dlp reported success but output file is missing: {downloaded_path}")

    title = info.get("title") or downloaded_path.stem
    log_event(logger, "video_downloaded", url=url, title=title, path=str(downloaded_path))
    return DownloadResult(path=downloaded_path, title=title, source_url=url)
