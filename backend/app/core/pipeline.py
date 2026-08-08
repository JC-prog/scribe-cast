import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from app.core.audio_extractor import extract_audio
from app.core.device import DeviceRequest
from app.core.model_manager import ModelManager
from app.core.srt_writer import write_srt
from app.core.transcriber import transcribe
from app.utils.timing import Stopwatch

logger = logging.getLogger("scribecast.pipeline")

StageCallback = Callable[[str, dict], None]


@dataclass
class PipelineResult:
    output_path: Path
    detected_language: str
    device_used: str
    fallback_occurred: bool
    timings_ms: dict = field(default_factory=dict)


def _noop_callback(stage: str, fields: dict) -> None:
    return None


def run_transcription_pipeline(
    model_manager: ModelManager,
    source_video_path: Path,
    output_srt_path: Path,
    model_size: str,
    language: str | None,
    work_dir: Path,
    device_request: DeviceRequest = "auto",
    on_stage_change: StageCallback = _noop_callback,
) -> PipelineResult:
    """
    Orchestrates the full transcribe-one-video flow, shared by both the
    single-upload and folder-batch job tasks. Reports progress via
    `on_stage_change(stage, fields)` since RQ only exposes `.result` after
    the job function returns — `.meta` (updated through this callback in
    worker/tasks.py) is what makes progress visible while the job runs.
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    audio_path = work_dir / "audio.wav"
    timings_ms: dict[str, float] = {}

    try:
        on_stage_change("loading_model", {})
        model, model_info = model_manager.load(model_size, device_request)
        timings_ms["model_load"] = model_info["load_time_ms"]
        on_stage_change(
            "loading_model",
            {"device_used": model_info["device_used"], "fallback_occurred": model_info["fallback_occurred"]},
        )

        on_stage_change("extracting_audio", {})
        with Stopwatch() as stopwatch:
            extract_audio(source_video_path, audio_path)
        timings_ms["audio_extract"] = stopwatch.elapsed_ms

        on_stage_change("transcribing", {})
        transcription = transcribe(model, audio_path, language)
        timings_ms["transcribe"] = transcription.elapsed_ms

        on_stage_change("writing_subtitles", {"detected_language": transcription.detected_language})
        with Stopwatch() as stopwatch:
            write_srt(transcription.segments, output_srt_path)
        timings_ms["srt_write"] = stopwatch.elapsed_ms

        timings_ms["total"] = sum(timings_ms.values())

        result = PipelineResult(
            output_path=output_srt_path,
            detected_language=transcription.detected_language,
            device_used=model_info["device_used"],
            fallback_occurred=model_info["fallback_occurred"],
            timings_ms=timings_ms,
        )

        on_stage_change("completed", {"timings_ms": timings_ms, "detected_language": transcription.detected_language})
        logger.info(
            "event=pipeline_complete source=%s output=%s timings_ms=%s",
            source_video_path,
            output_srt_path,
            timings_ms,
        )
        return result
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
