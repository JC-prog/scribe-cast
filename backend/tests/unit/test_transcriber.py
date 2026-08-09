from types import SimpleNamespace

from app.core.transcriber import transcribe


class FakeWord:
    def __init__(self, start, end):
        self.start = start
        self.end = end


class FakeSegment:
    def __init__(self, start, end, text, words=None):
        self.start = start
        self.end = end
        self.text = text
        self.words = words if words is not None else []


class FakeModel:
    def __init__(self, segments, language):
        self._segments = segments
        self._language = language
        self.calls = []

    def transcribe(self, audio_path, language, vad_filter, word_timestamps):
        self.calls.append(
            {
                "audio_path": audio_path,
                "language": language,
                "vad_filter": vad_filter,
                "word_timestamps": word_timestamps,
            }
        )
        info = SimpleNamespace(language=self._language)
        return iter(self._segments), info


def test_transcribe_returns_segments_and_detected_language():
    fake_segments = [
        FakeSegment(0.0, 1.0, "hello", words=[FakeWord(0.1, 0.9)]),
        FakeSegment(1.0, 2.5, "world", words=[FakeWord(1.2, 2.3)]),
    ]
    model = FakeModel(fake_segments, language="en")

    result = transcribe(model, audio_path="audio.wav", language=None)

    assert len(result.segments) == 2
    assert result.segments[0].text == "hello"
    assert result.detected_language == "en"
    assert result.elapsed_ms >= 0


def test_transcribe_passes_language_vad_filter_and_word_timestamps_through():
    model = FakeModel([], language="fr")

    transcribe(model, audio_path="audio.wav", language="fr")

    assert model.calls[0]["language"] == "fr"
    assert model.calls[0]["vad_filter"] is True
    assert model.calls[0]["word_timestamps"] is True


def test_transcribe_trims_segment_bounds_to_first_and_last_word():
    fake_segments = [
        FakeSegment(0.0, 2.0, "hello world", words=[FakeWord(0.4, 0.9), FakeWord(1.1, 1.6)]),
    ]
    model = FakeModel(fake_segments, language="en")

    result = transcribe(model, audio_path="audio.wav", language=None)

    assert result.segments[0].start == 0.4
    assert result.segments[0].end == 1.6


def test_transcribe_falls_back_to_segment_bounds_when_no_words():
    fake_segments = [FakeSegment(0.0, 2.0, "hello world", words=[])]
    model = FakeModel(fake_segments, language="en")

    result = transcribe(model, audio_path="audio.wav", language=None)

    assert result.segments[0].start == 0.0
    assert result.segments[0].end == 2.0
