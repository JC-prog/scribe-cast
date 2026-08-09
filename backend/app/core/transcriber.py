from dataclasses import dataclass
from pathlib import Path

import whisperx

from app.core.srt_writer import SubtitleSegment
from app.logging_config import get_logger, log_event
from app.utils.timing import Stopwatch

logger = get_logger("scribecast.transcriber")

_BATCH_SIZE = 16


@dataclass
class TranscriptionResult:
    segments: list[dict]
    detected_language: str
    elapsed_ms: float


@dataclass
class AlignmentResult:
    segments: list[SubtitleSegment]
    elapsed_ms: float


def transcribe(model, audio_path: Path, language: str | None) -> TranscriptionResult:
    """
    Run WhisperX's batched ASR pass. `language` is None for auto-detect,
    else an ISO code. Unlike faster-whisper's lazy generator, this returns
    a fully materialized result - the Stopwatch times the single blocking
    call rather than a generator iteration.
    """
    with Stopwatch() as stopwatch:
        audio = whisperx.load_audio(str(audio_path))
        result = model.transcribe(audio, batch_size=_BATCH_SIZE, language=language)

    log_event(
        logger,
        "transcription_complete",
        audio_path=str(audio_path),
        detected_language=result["language"],
        segments=len(result["segments"]),
        duration_ms=round(stopwatch.elapsed_ms, 1),
    )

    return TranscriptionResult(
        segments=result["segments"], detected_language=result["language"], elapsed_ms=stopwatch.elapsed_ms
    )


def align(transcription: TranscriptionResult, audio_path: Path, align_model, metadata, device: str) -> AlignmentResult:
    """
    Forced alignment: re-times every word against the audio using a
    wav2vec2 phoneme model, producing tighter segment boundaries than
    Whisper's own segment-level timestamps.
    """
    with Stopwatch() as stopwatch:
        audio = whisperx.load_audio(str(audio_path))
        aligned = whisperx.align(
            transcription.segments, align_model, metadata, audio, device, return_char_alignments=False
        )
        segments = [
            SubtitleSegment(start=segment["start"], end=segment["end"], text=segment["text"])
            for segment in aligned["segments"]
        ]

    log_event(
        logger,
        "alignment_complete",
        audio_path=str(audio_path),
        segments=len(segments),
        duration_ms=round(stopwatch.elapsed_ms, 1),
    )

    return AlignmentResult(segments=segments, elapsed_ms=stopwatch.elapsed_ms)
