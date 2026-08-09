from app.core import transcriber as transcriber_module
from app.core.transcriber import TranscriptionResult, align, to_subtitle_segments, transcribe
from app.schemas.runtime_settings import RuntimeSettings


def _patch_runtime_settings(monkeypatch, **overrides):
    rs = RuntimeSettings(**overrides)
    monkeypatch.setattr(transcriber_module, "load_runtime_settings", lambda: rs)
    return rs


class FakeAsrModel:
    def __init__(self, result):
        self._result = result
        self.calls = []

    def transcribe(self, audio, batch_size, language, task, chunk_size):
        self.calls.append(
            {"audio": audio, "batch_size": batch_size, "language": language, "task": task, "chunk_size": chunk_size}
        )
        return self._result


def test_transcribe_returns_segments_and_detected_language(monkeypatch):
    monkeypatch.setattr(transcriber_module.whisperx, "load_audio", lambda path: "fake-audio-array")
    _patch_runtime_settings(monkeypatch)
    model = FakeAsrModel({"segments": [{"start": 0.0, "end": 1.0, "text": "hello"}], "language": "en"})

    result = transcribe(model, audio_path="audio.wav", language=None)

    assert result.segments == [{"start": 0.0, "end": 1.0, "text": "hello"}]
    assert result.detected_language == "en"
    assert result.elapsed_ms >= 0


def test_transcribe_passes_batch_size_chunk_size_and_language_through(monkeypatch):
    monkeypatch.setattr(transcriber_module.whisperx, "load_audio", lambda path: "fake-audio-array")
    _patch_runtime_settings(monkeypatch, batch_size=42, chunk_size=12)
    model = FakeAsrModel({"segments": [], "language": "fr"})

    transcribe(model, audio_path="audio.wav", language="fr")

    assert model.calls[0]["language"] == "fr"
    assert model.calls[0]["batch_size"] == 42
    assert model.calls[0]["chunk_size"] == 12


def test_transcribe_defaults_to_transcribe_task(monkeypatch):
    monkeypatch.setattr(transcriber_module.whisperx, "load_audio", lambda path: "fake-audio-array")
    _patch_runtime_settings(monkeypatch)
    model = FakeAsrModel({"segments": [], "language": "en"})

    transcribe(model, audio_path="audio.wav", language=None)

    assert model.calls[0]["task"] == "transcribe"


def test_transcribe_passes_translate_task_through(monkeypatch):
    monkeypatch.setattr(transcriber_module.whisperx, "load_audio", lambda path: "fake-audio-array")
    _patch_runtime_settings(monkeypatch)
    model = FakeAsrModel({"segments": [], "language": "es"})

    transcribe(model, audio_path="audio.wav", language="es", task="translate")

    assert model.calls[0]["task"] == "translate"


def test_align_returns_subtitle_segments_from_aligned_output(monkeypatch):
    monkeypatch.setattr(transcriber_module.whisperx, "load_audio", lambda path: "fake-audio-array")
    _patch_runtime_settings(monkeypatch)

    def fake_align(segments, model, metadata, audio, device, return_char_alignments):
        assert return_char_alignments is False
        assert device == "cpu"
        return {
            "segments": [
                {
                    "start": 0.4,
                    "end": 1.6,
                    "text": "hello world",
                    "words": [
                        {"word": "hello", "start": 0.4, "end": 0.9},
                        {"word": "world", "start": 1.0, "end": 1.6},
                    ],
                }
            ]
        }

    monkeypatch.setattr(transcriber_module.whisperx, "align", fake_align)

    transcription = TranscriptionResult(
        segments=[{"start": 0.0, "end": 2.0, "text": "hello world"}], detected_language="en", elapsed_ms=1.0
    )

    result = align(transcription, audio_path="audio.wav", align_model="model", metadata={}, device="cpu")

    assert len(result.segments) == 1
    assert result.segments[0].start == 0.4
    assert result.segments[0].end == 1.6
    assert result.segments[0].text == "hello world"
    assert result.elapsed_ms >= 0


def test_align_uses_configured_subtitle_length_caps(monkeypatch):
    monkeypatch.setattr(transcriber_module.whisperx, "load_audio", lambda path: "fake-audio-array")
    _patch_runtime_settings(monkeypatch, max_chars_per_cue=10, max_seconds_per_cue=60.0)

    def fake_align(segments, model, metadata, audio, device, return_char_alignments):
        return {
            "segments": [
                {
                    "start": 0.0,
                    "end": 2.0,
                    "text": "one two three",
                    "words": [
                        {"word": "one", "start": 0.0, "end": 0.5},
                        {"word": "two", "start": 0.5, "end": 1.0},
                        {"word": "three", "start": 1.0, "end": 2.0},
                    ],
                }
            ]
        }

    monkeypatch.setattr(transcriber_module.whisperx, "align", fake_align)

    transcription = TranscriptionResult(
        segments=[{"start": 0.0, "end": 2.0, "text": "one two three"}], detected_language="en", elapsed_ms=1.0
    )

    result = align(transcription, audio_path="audio.wav", align_model="model", metadata={}, device="cpu")

    # max_chars_per_cue=10 forces a split that wouldn't happen at the default 84.
    assert len(result.segments) > 1
    assert all(len(seg.text) <= 10 for seg in result.segments)


def test_to_subtitle_segments_maps_raw_segments_without_alignment(monkeypatch):
    _patch_runtime_settings(monkeypatch)
    transcription = TranscriptionResult(
        segments=[
            {"start": 0.0, "end": 1.2, "text": "hola"},
            {"start": 1.2, "end": 3.0, "text": "como estas"},
        ],
        detected_language="es",
        elapsed_ms=1.0,
    )

    segments = to_subtitle_segments(transcription)

    assert len(segments) == 2
    assert segments[0].start == 0.0
    assert segments[0].end == 1.2
    assert segments[0].text == "hola"
    assert segments[1].text == "como estas"
