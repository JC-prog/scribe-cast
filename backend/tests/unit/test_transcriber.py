from types import SimpleNamespace

from app.core.transcriber import transcribe


class FakeSegment:
    def __init__(self, start, end, text):
        self.start = start
        self.end = end
        self.text = text


class FakeModel:
    def __init__(self, segments, language):
        self._segments = segments
        self._language = language
        self.calls = []

    def transcribe(self, audio_path, language, vad_filter):
        self.calls.append({"audio_path": audio_path, "language": language, "vad_filter": vad_filter})
        info = SimpleNamespace(language=self._language)
        return iter(self._segments), info


def test_transcribe_returns_segments_and_detected_language():
    fake_segments = [FakeSegment(0.0, 1.0, "hello"), FakeSegment(1.0, 2.5, "world")]
    model = FakeModel(fake_segments, language="en")

    result = transcribe(model, audio_path="audio.wav", language=None)

    assert len(result.segments) == 2
    assert result.segments[0].text == "hello"
    assert result.detected_language == "en"
    assert result.elapsed_ms >= 0


def test_transcribe_passes_language_and_vad_filter_through():
    model = FakeModel([], language="fr")

    transcribe(model, audio_path="audio.wav", language="fr")

    assert model.calls[0]["language"] == "fr"
    assert model.calls[0]["vad_filter"] is True
