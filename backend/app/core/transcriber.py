from dataclasses import dataclass
from pathlib import Path

from app.core.srt_writer import SubtitleSegment
from app.logging_config import get_logger, log_event
from app.utils.timing import Stopwatch

logger = get_logger("scribecast.transcriber")


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

    log_event(
        logger,
        "transcription_complete",
        audio_path=str(audio_path),
        detected_language=info.language,
        segments=len(segments),
        duration_ms=round(stopwatch.elapsed_ms, 1),
    )

    return TranscriptionResult(segments=segments, detected_language=info.language, elapsed_ms=stopwatch.elapsed_ms)
