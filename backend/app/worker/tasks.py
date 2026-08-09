from pathlib import Path

from rq import get_current_job

from app.config import settings
from app.core.errors import VideoDownloadError
from app.core.model_manager import get_model_manager
from app.core.pipeline import run_transcription_pipeline
from app.core.video_downloader import download_video
from app.logging_config import get_logger, log_event
from app.utils.text import sanitize_filename
from app.worker.job_meta import update_job_meta

logger = get_logger("scribecast.worker.tasks")


def _stage_callback(job):
    def callback(stage: str, fields: dict) -> None:
        update_job_meta(job, stage=stage, **fields)

    return callback


def _run_and_record(
    job,
    source_video_path: Path,
    output_srt_path: Path,
    model_size: str,
    language: str | None,
    work_dir: Path,
    translate: bool = False,
):
    try:
        result = run_transcription_pipeline(
            model_manager=get_model_manager(),
            source_video_path=source_video_path,
            output_srt_path=output_srt_path,
            model_size=model_size,
            language=language,
            work_dir=work_dir,
            device_request=settings.device,
            translate=translate,
            on_stage_change=_stage_callback(job),
        )
    except Exception as exc:
        log_event(logger, "job_failed", job_id=job.id, error=str(exc))
        update_job_meta(job, stage="failed", error=str(exc))
        raise

    update_job_meta(
        job,
        stage="completed",
        output_path=str(result.output_path),
        detected_language=result.detected_language,
        device_used=result.device_used,
        fallback_occurred=result.fallback_occurred,
        timings_ms=result.timings_ms,
    )
    return {
        "output_path": str(result.output_path),
        "detected_language": result.detected_language,
        "device_used": result.device_used,
        "fallback_occurred": result.fallback_occurred,
        "timings_ms": result.timings_ms,
    }


def task_transcribe_upload(
    upload_path: str, original_filename: str, model_size: str, language: str | None, translate: bool = False
) -> dict:
    job = get_current_job()
    work_dir = settings.work_dir / job.id
    output_path = settings.results_dir / job.id / Path(original_filename).with_suffix(".srt").name

    update_job_meta(
        job,
        stage="queued",
        model_size=model_size,
        language=language,
        translate=translate,
        source_filename=original_filename,
    )

    try:
        return _run_and_record(job, Path(upload_path), output_path, model_size, language, work_dir, translate)
    finally:
        Path(upload_path).unlink(missing_ok=True)


def task_transcribe_folder_item(
    video_path: str,
    output_path: str,
    model_size: str,
    language: str | None,
    batch_id: str | None = None,
    translate: bool = False,
) -> dict:
    job = get_current_job()
    work_dir = settings.work_dir / job.id

    update_job_meta(
        job,
        stage="queued",
        model_size=model_size,
        language=language,
        translate=translate,
        source_filename=Path(video_path).name,
        batch_id=batch_id,
    )

    return _run_and_record(job, Path(video_path), Path(output_path), model_size, language, work_dir, translate)


def task_transcribe_url(url: str, model_size: str, language: str | None, translate: bool = False) -> dict:
    job = get_current_job()
    work_dir = settings.work_dir / job.id

    update_job_meta(job, stage="queued", model_size=model_size, language=language, translate=translate, source_url=url)

    try:
        update_job_meta(job, stage="downloading")
        download_result = download_video(url, work_dir)
    except VideoDownloadError as exc:
        log_event(logger, "url_download_failed", job_id=job.id, url=url, error=str(exc))
        update_job_meta(job, stage="failed", error=str(exc))
        raise

    update_job_meta(job, source_filename=download_result.title)
    output_path = settings.results_dir / job.id / f"{sanitize_filename(download_result.title)}.srt"

    return _run_and_record(job, download_result.path, output_path, model_size, language, work_dir, translate)


def task_validate_model(model_size: str) -> dict:
    job = get_current_job()
    update_job_meta(job, stage="queued", model_size=model_size)

    result = get_model_manager().validate(model_size, device_request=settings.device)

    if result.ok:
        update_job_meta(
            job,
            stage="completed",
            device_used=result.device_used,
            fallback_occurred=result.fallback_occurred,
            timings_ms={"model_load": result.load_time_ms},
        )
    else:
        update_job_meta(job, stage="failed", error=result.error)

    return {
        "ok": result.ok,
        "device_used": result.device_used,
        "fallback_occurred": result.fallback_occurred,
        "load_time_ms": result.load_time_ms,
        "error": result.error,
    }
