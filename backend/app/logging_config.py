import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Literal

from pythonjsonlogger.json import JsonFormatter

from app.config import settings

_LOG_FIELDS = "%(asctime)s %(levelname)s %(name)s %(message)s"

_configured = False


def _json_formatter() -> JsonFormatter:
    return JsonFormatter(
        _LOG_FIELDS,
        rename_fields={"asctime": "timestamp", "levelname": "level", "name": "logger"},
    )


def setup_logging(component: Literal["api", "worker"]) -> None:
    """
    Configure structured JSON logging once per process:
      - logs/{component}.log  (component-specific rotating file)
      - logs/errors.log       (shared, ERROR+ from any component, for cross-component grepping)
      - stdout                (visible via `docker compose logs`)
    """
    global _configured
    if _configured:
        return

    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    formatter = _json_formatter()
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    component_handler = RotatingFileHandler(
        settings.logs_dir / f"{component}.log",
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count,
        encoding="utf-8",
    )
    component_handler.setFormatter(formatter)
    component_handler.setLevel(logging.INFO)
    root.addHandler(component_handler)

    error_handler = RotatingFileHandler(
        settings.logs_dir / "errors.log",
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count,
        encoding="utf-8",
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    root.addHandler(error_handler)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    stdout_handler.setLevel(logging.INFO)
    root.addHandler(stdout_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_event(logger: logging.Logger, event: str, level: int = logging.INFO, **fields) -> None:
    """Keeps structured field names consistent across call sites (job_id, model, stage, duration_ms, ...)."""
    logger.log(level, event, extra=fields)
