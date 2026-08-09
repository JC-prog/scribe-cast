from pathlib import Path

from app.core.pipeline import run_transcription_pipeline
from app.core.srt_writer import SubtitleSegment
from app.core.transcriber import AlignmentResult, TranscriptionResult


class FakeModelManager:
    def __init__(self):
        self.load_calls = []
        self.load_align_calls = []

    def load(self, model_size, device_request):
        self.load_calls.append((model_size, device_request))
        return object(), {
            "device_used": "cpu",
            "compute_type": "int8",
            "fallback_occurred": False,
            "load_time_ms": 5.0,
            "cache_hit": True,
        }

    def load_align_model(self, language, device):
        self.load_align_calls.append((language, device))
        return "fake-align-model", {}


def _fake_transcribe(model, audio_path, language):
    assert audio_path.exists()
    return TranscriptionResult(segments=[{"start": 0.0, "end": 1.0, "text": "hi"}], detected_language="en", elapsed_ms=42.0)


def _fake_align(transcription, audio_path, align_model, metadata, device):
    return AlignmentResult(segments=[SubtitleSegment(start=0.0, end=1.0, text="hi")], elapsed_ms=7.0)


def test_pipeline_runs_stages_in_order_and_reports_progress(monkeypatch, tmp_path):
    stage_log = []

    def fake_extract_audio(input_path, output_path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake-audio")

    monkeypatch.setattr("app.core.pipeline.extract_audio", fake_extract_audio)
    monkeypatch.setattr("app.core.pipeline.transcribe", _fake_transcribe)
    monkeypatch.setattr("app.core.pipeline.align", _fake_align)

    def on_stage_change(stage, fields):
        stage_log.append(stage)

    output_path = tmp_path / "out" / "video.srt"
    work_dir = tmp_path / "work"
    manager = FakeModelManager()

    result = run_transcription_pipeline(
        model_manager=manager,
        source_video_path=tmp_path / "video.mp4",
        output_srt_path=output_path,
        model_size="tiny",
        language=None,
        work_dir=work_dir,
        device_request="cpu",
        on_stage_change=on_stage_change,
    )

    assert stage_log == [
        "loading_model",
        "loading_model",
        "extracting_audio",
        "transcribing",
        "aligning",
        "writing_subtitles",
        "completed",
    ]
    assert manager.load_calls == [("tiny", "cpu")]
    assert manager.load_align_calls == [("en", "cpu")]
    assert result.detected_language == "en"
    assert result.device_used == "cpu"
    assert output_path.exists()
    assert set(result.timings_ms.keys()) == {"model_load", "audio_extract", "transcribe", "align", "srt_write", "total"}
    assert result.timings_ms["total"] == sum(
        v for k, v in result.timings_ms.items() if k != "total"
    )


def test_pipeline_cleans_up_work_dir_after_success(monkeypatch, tmp_path):
    def fake_extract_audio(input_path, output_path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake-audio")

    monkeypatch.setattr("app.core.pipeline.extract_audio", fake_extract_audio)
    monkeypatch.setattr("app.core.pipeline.transcribe", _fake_transcribe)
    monkeypatch.setattr("app.core.pipeline.align", _fake_align)

    work_dir = tmp_path / "work"

    run_transcription_pipeline(
        model_manager=FakeModelManager(),
        source_video_path=tmp_path / "video.mp4",
        output_srt_path=tmp_path / "video.srt",
        model_size="tiny",
        language=None,
        work_dir=work_dir,
        device_request="cpu",
    )

    assert not work_dir.exists()


def test_pipeline_cleans_up_work_dir_on_failure(monkeypatch, tmp_path):
    def fake_extract_audio(input_path, output_path):
        raise RuntimeError("boom")

    monkeypatch.setattr("app.core.pipeline.extract_audio", fake_extract_audio)

    work_dir = tmp_path / "work"

    try:
        run_transcription_pipeline(
            model_manager=FakeModelManager(),
            source_video_path=tmp_path / "video.mp4",
            output_srt_path=tmp_path / "video.srt",
            model_size="tiny",
            language=None,
            work_dir=work_dir,
            device_request="cpu",
        )
    except RuntimeError:
        pass

    assert not work_dir.exists()
