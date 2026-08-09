"""
Admin-tunable settings, persisted as a single JSON blob in Redis rather than
env vars so they can change without a container restart. Deliberately has no
dependency on whisperx/torch (only redis+pydantic), so the API container
(which never imports the ML stack) can serve the admin routes directly.
Uses its own direct Redis connection (same style as worker/rq_worker.py)
rather than FastAPI DI, since this needs to work identically from API routes
and worker code.
"""

import logging

from redis import Redis

from app.config import settings
from app.logging_config import get_logger, log_event
from app.schemas.runtime_settings import RuntimeSettings, RuntimeSettingsUpdate

logger = get_logger("scribecast.runtime_settings")

REDIS_KEY = "scribecast:runtime_settings"

_redis_conn: Redis | None = None


def _get_redis_conn() -> Redis:
    global _redis_conn
    if _redis_conn is None:
        _redis_conn = Redis.from_url(settings.redis_url)
    return _redis_conn


def load_runtime_settings() -> RuntimeSettings:
    """Never raises - a missing key, corrupt JSON, or unreachable Redis all
    fall back to defaults rather than breaking a job."""
    try:
        raw = _get_redis_conn().get(REDIS_KEY)
        if raw is None:
            return RuntimeSettings()
        return RuntimeSettings.model_validate_json(raw)
    except Exception as exc:  # noqa: BLE001
        log_event(logger, "runtime_settings_load_failed", level=logging.ERROR, error=str(exc))
        return RuntimeSettings()


def save_runtime_settings(update: RuntimeSettingsUpdate) -> RuntimeSettings:
    """Merges only the fields the caller actually set (exclude_unset) onto the
    current settings, so omitting hf_token leaves it untouched - only an
    explicitly provided value (including "" to clear it) changes it."""
    current = load_runtime_settings()
    changed_fields = update.model_dump(exclude_unset=True)
    merged = RuntimeSettings(**{**current.model_dump(), **changed_fields})
    _get_redis_conn().set(REDIS_KEY, merged.model_dump_json())
    log_event(logger, "runtime_settings_updated", fields=sorted(changed_fields.keys()))
    return merged


def reset_runtime_settings() -> RuntimeSettings:
    _get_redis_conn().delete(REDIS_KEY)
    log_event(logger, "runtime_settings_reset")
    return RuntimeSettings()
