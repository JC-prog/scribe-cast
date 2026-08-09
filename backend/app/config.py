from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    # Sourced from the repo-root VERSION file via APP_VERSION, set by
    # scripts/build.*/stack.* - not duplicated into .env to avoid drift
    # from the single source of truth.
    app_version: str = "0.0.0-dev"

    # Device / model
    device: Literal["auto", "cuda", "cpu"] = "auto"
    compute_type: str | None = None
    model_cache_dir: Path = Path("/app/model_cache")
    max_cached_models: int = 1

    # Redis / queue
    redis_url: str = "redis://localhost:6379/0"
    queue_name: str = "transcription"
    batch_ttl_seconds: int = 60 * 60 * 24
    # How long a finished/failed job's meta+result stay fetchable in Redis -
    # RQ's own defaults (result_ttl=500s for finished jobs) are far too
    # short for a history panel to be useful, so this overrides both at
    # every enqueue() call site.
    job_result_ttl_seconds: int = 60 * 60 * 24 * 7

    # Storage
    uploads_dir: Path = Path("/app/uploads")
    results_dir: Path = Path("/app/results")
    work_dir: Path = Path("/app/work")
    data_dir: Path = Path("/data")

    # Logging
    logs_dir: Path = Path("logs")
    log_max_bytes: int = 10 * 1024 * 1024
    log_backup_count: int = 5

    # CORS
    cors_allow_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
