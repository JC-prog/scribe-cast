import json
import logging

import pytest

from app import logging_config as logging_config_module
from app.config import settings
from app.logging_config import get_logger, log_event, setup_logging


def _reset_logging_state():
    logging_config_module._configured = False
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()


def test_setup_logging_writes_json_lines_to_component_and_error_logs(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "logs_dir", tmp_path)
    _reset_logging_state()

    setup_logging("worker")
    logger = get_logger("scribecast.test")
    log_event(logger, "model_load", model="tiny", duration_ms=12.5)
    log_event(logger, "model_load_failed", level=logging.ERROR, model="tiny", error="boom")

    for handler in logging.getLogger().handlers:
        handler.flush()

    worker_log = (tmp_path / "worker.log").read_text(encoding="utf-8").strip().splitlines()
    errors_log = (tmp_path / "errors.log").read_text(encoding="utf-8").strip().splitlines()

    assert len(worker_log) == 2
    assert len(errors_log) == 1

    info_record = json.loads(worker_log[0])
    assert info_record["message"] == "model_load"
    assert info_record["model"] == "tiny"
    assert info_record["duration_ms"] == 12.5
    assert info_record["level"] == "INFO"
    assert "timestamp" in info_record

    error_record = json.loads(errors_log[0])
    assert error_record["message"] == "model_load_failed"
    assert error_record["level"] == "ERROR"

    _reset_logging_state()


def test_setup_logging_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "logs_dir", tmp_path)
    _reset_logging_state()

    setup_logging("api")
    handler_count_after_first = len(logging.getLogger().handlers)
    setup_logging("api")
    handler_count_after_second = len(logging.getLogger().handlers)

    assert handler_count_after_first == handler_count_after_second

    _reset_logging_state()


def test_log_event_rejects_field_colliding_with_logrecord_attribute():
    logger = get_logger("scribecast.test.collision")

    with pytest.raises(ValueError, match="filename"):
        log_event(logger, "upload_enqueued", filename="video.mp4")
