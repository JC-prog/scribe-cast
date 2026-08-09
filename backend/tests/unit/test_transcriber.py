from app.core import transcriber as transcriber_module
from app.core.transcriber import TranscriptionResult, align, to_subtitle_segments, transcribe


class FakeAsrModel:
    def __init__(self, result):
        self._result = result
        self.calls = []

    def transcribe(self, audio, batch_size, language, task):
        self.calls.append({"audio": audio, "batch_size": batch_size, "language": language, "task": task})
        return self._result


def test_transcribe_returns_segments_and_detected_language(monkeypatch):
    monkeypatch.setattr(transcriber_module.whisperx, "load_audio", lambda path: "fake-audio-array")
    model = FakeAsrModel({"segments": [{"start": 0.0, "end": 1.0, "text": "hello"}], "language": "en"})

    result = transcribe(model, audio_path="audio.wav", language=None)

    assert result.segments == [{"start": 0.0, "end": 1.0, "text": "hello"}]
    assert result.detected_language == "en"
    assert result.elapsed_ms >= 0


def test_transcribe_passes_batch_size_and_language_through(monkeypatch):
    monkeypatch.setattr(transcriber_module.whisperx, "load_audio", lambda path: "fake-audio-array")
    model = FakeAsrModel({"segments": [], "language": "fr"})

    transcribe(model, audio_path="audio.wav", language="fr")

    assert model.calls[0]["language"] == "fr"
    assert model.calls[0]["batch_size"] == transcriber_module._BATCH_SIZE


def test_transcribe_defaults_to_transcribe_task(monkeypatch):
    monkeypatch.setattr(transcriber_module.whisperx, "load_audio", lambda path: "fake-audio-array")
    model = FakeAsrModel({"segments": [], "language": "en"})

    transcribe(model, audio_path="audio.wav", language=None)

    assert model.calls[0]["task"] == "transcribe"


def test_transcribe_passes_translate_task_through(monkeypatch):
    monkeypatch.setattr(transcriber_module.whisperx, "load_audio", lambda path: "fake-audio-array")
    model = FakeAsrModel({"segments": [], "language": "es"})

    transcribe(model, audio_path="audio.wav", language="es", task="translate")

    assert model.calls[0]["task"] == "translate"


def test_align_returns_subtitle_segments_from_aligned_output(monkeypatch):
    monkeypatch.setattr(transcriber_module.whisperx, "load_audio", lambda path: "fake-audio-array")

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


def test_to_subtitle_segments_maps_raw_segments_without_alignment():
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
