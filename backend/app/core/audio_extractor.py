import logging
import subprocess
from pathlib import Path

from app.core.errors import AudioExtractionError
from app.logging_config import get_logger, log_event

logger = get_logger("scribecast.audio_extractor")


def extract_audio(input_path: Path, output_path: Path) -> None:
    """Extract mono 16kHz PCM WAV audio from a video, suitable for Whisper input."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        log_event(
            logger,
            "audio_extraction_failed",
            level=logging.ERROR,
            input_path=str(input_path),
            stderr=result.stderr,
        )
        raise AudioExtractionError(
            f"ffmpeg failed extracting audio from {input_path} (exit {result.returncode}): {result.stderr}"
        )
