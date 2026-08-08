import logging
from dataclasses import dataclass
from pathlib import Path

from app.core.srt_writer import SubtitleSegment
from app.utils.timing import Stopwatch

logger = logging.getLogger("scribecast.transcriber")


@dataclass
class TranscriptionResult:
    segments: list[SubtitleSegment]
    detected_language: str
    elapsed_ms: float


def transcribe(model, audio_path: Path, language: str | None) -> TranscriptionResult:
    """
    Run Whisper inference. `language` is None for auto-detect, else an ISO code.
    Times the full segment-generator iteration, since faster-whisper's
    `.transcribe()` returns lazily and does the real work while iterating.
    """
    with Stopwatch() as stopwatch:
        segment_iter, info = model.transcribe(str(audio_path), language=language, vad_filter=True)
        segments = [
            SubtitleSegment(start=segment.start, end=segment.end, text=segment.text) for segment in segment_iter
        ]

    logger.info(
        "event=transcription_complete audio=%s detected_language=%s segments=%d duration_ms=%.1f",
        audio_path,
        info.language,
        len(segments),
        stopwatch.elapsed_ms,
    )

    return TranscriptionResult(segments=segments, detected_language=info.language, elapsed_ms=stopwatch.elapsed_ms)
