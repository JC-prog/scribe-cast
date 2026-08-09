from dataclasses import dataclass
from pathlib import Path

import whisperx

from app.core.srt_writer import SubtitleSegment
from app.core.subtitle_segmenter import segment_aligned_output, segment_raw_output
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


def transcribe(model, audio_path: Path, language: str | None, task: str = "transcribe") -> TranscriptionResult:
    """
    Run WhisperX's batched ASR pass. `language` is None for auto-detect,
    else an ISO code. `task="translate"` always translates to English
    specifically - Whisper has no other target language. Unlike
    faster-whisper's lazy generator, this returns a fully materialized
    result - the Stopwatch times the single blocking call rather than a
    generator iteration.
    """
    with Stopwatch() as stopwatch:
        audio = whisperx.load_audio(str(audio_path))
        result = model.transcribe(audio, batch_size=_BATCH_SIZE, language=language, task=task)

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


def to_subtitle_segments(transcription: TranscriptionResult) -> list[SubtitleSegment]:
    """
    Converts raw ASR segments to subtitle cues, bypassing forced
    alignment. Used for translated output: alignment matches text to audio
    using a phoneme model for one language, but translated text is English
    while the audio's actual phonemes are the source language - there's no
    language for which both would match, so alignment would just produce
    meaningless timestamps. WhisperX's raw segments can span up to its
    ~30s batching chunk size, so subtitle_segmenter still splits them into
    readable cues, interpolating word timing proportionally within each
    segment since there's no real word-level timing here.
    """
    return segment_raw_output(transcription.segments)


def align(transcription: TranscriptionResult, audio_path: Path, align_model, metadata, device: str) -> AlignmentResult:
    """
    Forced alignment: re-times every word against the audio using a
    wav2vec2 phoneme model. subtitle_segmenter then packs those words into
    readable, capped-length/duration cues - whisperx's own aligned
    segments can still span a long multi-sentence run of continuous
    speech with no internal breaks, which is exactly what produces a
    screen-covering wall of subtitle text without this step.
    """
    with Stopwatch() as stopwatch:
        audio = whisperx.load_audio(str(audio_path))
        aligned = whisperx.align(
            transcription.segments, align_model, metadata, audio, device, return_char_alignments=False
        )
        segments = segment_aligned_output(aligned["segments"])

    log_event(
        logger,
        "alignment_complete",
        audio_path=str(audio_path),
        segments=len(segments),
        duration_ms=round(stopwatch.elapsed_ms, 1),
    )

    return AlignmentResult(segments=segments, elapsed_ms=stopwatch.elapsed_ms)
