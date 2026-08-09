from pathlib import Path

import pytest

from app.core.errors import VideoDownloadError
from app.core.pipeline import PipelineResult
from app.core.video_downloader import DownloadResult
from app.worker import tasks as tasks_module


class FakeJob:
    def __init__(self, job_id="job-1"):
        self.id = job_id
        self.meta = {}

    def save_meta(self):
        pass


def _fake_pipeline_result(output_path):
    return PipelineResult(
        output_path=output_path,
        detected_language="en",
        device_used="cpu",
        fallback_occurred=False,
        timings_ms={"model_load": 1.0, "audio_extract": 2.0, "transcribe": 3.0, "srt_write": 0.5, "total": 6.5},
    )


def test_task_transcribe_upload_updates_meta_and_cleans_up_upload(monkeypatch, tmp_path):
    job = FakeJob()
    monkeypatch.setattr(tasks_module, "get_current_job", lambda: job)

    def fake_run_pipeline(**kwargs):
        output_path = kwargs["output_srt_path"]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("fake srt")
        return _fake_pipeline_result(output_path)

    monkeypatch.setattr(tasks_module, "run_transcription_pipeline", fake_run_pipeline)
    monkeypatch.setattr(tasks_module.settings, "results_dir", tmp_path / "results")

    upload_path = tmp_path / "uploads" / "video.mp4"
    upload_path.parent.mkdir(parents=True, exist_ok=True)
    upload_path.write_bytes(b"fake video")

    result = tasks_module.task_transcribe_upload(str(upload_path), "video.mp4", "tiny", None)

    assert result["detected_language"] == "en"
    assert job.meta["stage"] == "completed"
    assert job.meta["source_filename"] == "video.mp4"
    assert job.meta["translate"] is False  # default
    assert not upload_path.exists()  # cleaned up


def test_task_transcribe_upload_passes_translate_through(monkeypatch, tmp_path):
    job = FakeJob()
    monkeypatch.setattr(tasks_module, "get_current_job", lambda: job)
    captured = {}

    def fake_run_pipeline(**kwargs):
        captured.update(kwargs)
        output_path = kwargs["output_srt_path"]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("fake srt")
        return _fake_pipeline_result(output_path)

    monkeypatch.setattr(tasks_module, "run_transcription_pipeline", fake_run_pipeline)
    monkeypatch.setattr(tasks_module.settings, "results_dir", tmp_path / "results")

    upload_path = tmp_path / "uploads" / "video.mp4"
    upload_path.parent.mkdir(parents=True, exist_ok=True)
    upload_path.write_bytes(b"fake video")

    tasks_module.task_transcribe_upload(str(upload_path), "video.mp4", "tiny", "es", translate=True)

    assert captured["translate"] is True
    assert job.meta["translate"] is True


def test_task_transcribe_upload_marks_failed_on_error(monkeypatch, tmp_path):
    job = FakeJob()
    monkeypatch.setattr(tasks_module, "get_current_job", lambda: job)

    def fake_run_pipeline(**kwargs):
        raise RuntimeError("ffmpeg exploded")

    monkeypatch.setattr(tasks_module, "run_transcription_pipeline", fake_run_pipeline)
    monkeypatch.setattr(tasks_module.settings, "results_dir", tmp_path / "results")

    upload_path = tmp_path / "uploads" / "video.mp4"
    upload_path.parent.mkdir(parents=True, exist_ok=True)
    upload_path.write_bytes(b"fake video")

    try:
        tasks_module.task_transcribe_upload(str(upload_path), "video.mp4", "tiny", None)
    except RuntimeError:
        pass

    assert job.meta["stage"] == "failed"
    assert "ffmpeg exploded" in job.meta["error"]
    assert not upload_path.exists()  # cleaned up even on failure


def test_task_transcribe_folder_item_writes_sibling_srt(monkeypatch, tmp_path):
    job = FakeJob()
    monkeypatch.setattr(tasks_module, "get_current_job", lambda: job)

    def fake_run_pipeline(**kwargs):
        return _fake_pipeline_result(kwargs["output_srt_path"])

    monkeypatch.setattr(tasks_module, "run_transcription_pipeline", fake_run_pipeline)

    video_path = tmp_path / "video.mp4"
    output_path = tmp_path / "video.srt"

    result = tasks_module.task_transcribe_folder_item(
        str(video_path), str(output_path), "tiny", "en", batch_id="batch-1"
    )

    assert result["output_path"] == str(output_path)
    assert job.meta["batch_id"] == "batch-1"
    assert job.meta["stage"] == "completed"
    assert job.meta["translate"] is False  # default


def test_task_transcribe_folder_item_passes_translate_through(monkeypatch, tmp_path):
    job = FakeJob()
    monkeypatch.setattr(tasks_module, "get_current_job", lambda: job)
    captured = {}

    def fake_run_pipeline(**kwargs):
        captured.update(kwargs)
        return _fake_pipeline_result(kwargs["output_srt_path"])

    monkeypatch.setattr(tasks_module, "run_transcription_pipeline", fake_run_pipeline)

    video_path = tmp_path / "video.mp4"
    output_path = tmp_path / "video.srt"

    tasks_module.task_transcribe_folder_item(str(video_path), str(output_path), "tiny", "es", translate=True)

    assert captured["translate"] is True
    assert job.meta["translate"] is True


def test_task_transcribe_url_downloads_then_transcribes(monkeypatch, tmp_path):
    job = FakeJob()
    monkeypatch.setattr(tasks_module, "get_current_job", lambda: job)
    monkeypatch.setattr(tasks_module.settings, "results_dir", tmp_path / "results")
    monkeypatch.setattr(tasks_module.settings, "work_dir", tmp_path / "work")

    downloaded_path = tmp_path / "work" / job.id / "source.webm"

    def fake_download_video(url, work_dir):
        downloaded_path.parent.mkdir(parents=True, exist_ok=True)
        downloaded_path.write_bytes(b"fake audio")
        return DownloadResult(path=downloaded_path, title="My Video", source_url=url)

    monkeypatch.setattr(tasks_module, "download_video", fake_download_video)

    def fake_run_pipeline(**kwargs):
        output_path = kwargs["output_srt_path"]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("fake srt")
        assert kwargs["source_video_path"] == downloaded_path
        return _fake_pipeline_result(output_path)

    monkeypatch.setattr(tasks_module, "run_transcription_pipeline", fake_run_pipeline)

    result = tasks_module.task_transcribe_url("https://example.com/watch?v=abc", "tiny", None)

    assert result["detected_language"] == "en"
    assert job.meta["stage"] == "completed"
    assert job.meta["source_url"] == "https://example.com/watch?v=abc"
    assert job.meta["source_filename"] == "My Video"
    assert job.meta["translate"] is False  # default
    assert "My Video.srt" in result["output_path"]


def test_task_transcribe_url_passes_translate_through(monkeypatch, tmp_path):
    job = FakeJob()
    monkeypatch.setattr(tasks_module, "get_current_job", lambda: job)
    monkeypatch.setattr(tasks_module.settings, "results_dir", tmp_path / "results")
    monkeypatch.setattr(tasks_module.settings, "work_dir", tmp_path / "work")

    downloaded_path = tmp_path / "work" / job.id / "source.webm"

    def fake_download_video(url, work_dir):
        downloaded_path.parent.mkdir(parents=True, exist_ok=True)
        downloaded_path.write_bytes(b"fake audio")
        return DownloadResult(path=downloaded_path, title="My Video", source_url=url)

    monkeypatch.setattr(tasks_module, "download_video", fake_download_video)
    captured = {}

    def fake_run_pipeline(**kwargs):
        captured.update(kwargs)
        output_path = kwargs["output_srt_path"]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("fake srt")
        return _fake_pipeline_result(output_path)

    monkeypatch.setattr(tasks_module, "run_transcription_pipeline", fake_run_pipeline)

    tasks_module.task_transcribe_url("https://example.com/watch?v=abc", "tiny", "es", translate=True)

    assert captured["translate"] is True
    assert job.meta["translate"] is True


def test_task_transcribe_url_marks_failed_on_download_error(monkeypatch, tmp_path):
    job = FakeJob()
    monkeypatch.setattr(tasks_module, "get_current_job", lambda: job)
    monkeypatch.setattr(tasks_module.settings, "work_dir", tmp_path / "work")

    def fake_download_video(url, work_dir):
        raise VideoDownloadError("Could not download video: unsupported URL")

    monkeypatch.setattr(tasks_module, "download_video", fake_download_video)

    with pytest.raises(VideoDownloadError):
        tasks_module.task_transcribe_url("https://example.com/not-a-video", "tiny", None)

    assert job.meta["stage"] == "failed"
    assert "unsupported URL" in job.meta["error"]


def test_task_validate_model_ok(monkeypatch):
    job = FakeJob()
    monkeypatch.setattr(tasks_module, "get_current_job", lambda: job)

    class FakeManager:
        def validate(self, model_size, device_request):
            from app.core.model_manager import ValidationResult

            return ValidationResult(
                ok=True, device_used="cpu", fallback_occurred=True, load_time_ms=123.0, error=None
            )

    monkeypatch.setattr(tasks_module, "get_model_manager", lambda: FakeManager())

    result = tasks_module.task_validate_model("tiny")

    assert result["ok"] is True
    assert result["fallback_occurred"] is True
    assert job.meta["stage"] == "completed"
    assert job.meta["fallback_occurred"] is True


def test_task_validate_model_failure(monkeypatch):
    job = FakeJob()
    monkeypatch.setattr(tasks_module, "get_current_job", lambda: job)

    class FakeManager:
        def validate(self, model_size, device_request):
            from app.core.model_manager import ValidationResult

            return ValidationResult(
                ok=False, device_used=None, fallback_occurred=False, load_time_ms=None, error="CUDA OOM"
            )

    monkeypatch.setattr(tasks_module, "get_model_manager", lambda: FakeManager())

    result = tasks_module.task_validate_model("large-v3")

    assert result["ok"] is False
    assert job.meta["stage"] == "failed"
    assert job.meta["error"] == "CUDA OOM"
