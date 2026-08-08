"""
Shared shape for `job.meta`, written by worker/tasks.py as a pipeline runs
and read by the API's jobs routes. RQ only populates `.result` after a job
function returns, so `.meta` is the only channel for live progress.

Expected keys (all optional, filled in incrementally):
  stage: queued|loading_model|extracting_audio|transcribing|writing_subtitles|completed|failed
  model_size, language, detected_language: str | None
  source_filename: str | None
  batch_id: str | None
  timings_ms: dict[str, float]
  device_used: str | None
  fallback_occurred: bool
  error: str | None
  output_path: str | None
"""


def update_job_meta(job, **fields) -> None:
    job.meta.update(fields)
    job.save_meta()
