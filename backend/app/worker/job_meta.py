"""
Shared shape for `job.meta`, written by worker/tasks.py as a pipeline runs
and read by the API's jobs routes. RQ only populates `.result` after a job
function returns, so `.meta` is the only channel for live progress.

Expected keys (all optional, filled in incrementally):
  stage: queued|downloading|loading_model|extracting_audio|transcribing|aligning|writing_subtitles|completed|failed
    ("aligning" is skipped entirely when translate=True - forced alignment
    doesn't work across a source-audio/translated-text language mismatch)
  model_size, language, detected_language: str | None
  translate: bool (True translates to English; language is still a source-language hint)
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
