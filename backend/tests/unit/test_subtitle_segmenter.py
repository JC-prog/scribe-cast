from app.core.subtitle_segmenter import (
    MAX_CHARS_PER_CUE,
    MAX_SECONDS_PER_CUE,
    TimedWord,
    _pack_words_into_cues,
    segment_aligned_output,
    segment_raw_output,
    words_from_aligned_segments,
    words_from_raw_segments,
)


def _aligned_word(word, start, end):
    return {"word": word, "start": start, "end": end}


def test_short_aligned_segment_stays_one_cue():
    aligned_segments = [
        {
            "start": 0.0,
            "end": 1.5,
            "text": "hello world",
            "words": [_aligned_word("hello", 0.0, 0.6), _aligned_word("world", 0.8, 1.5)],
        }
    ]

    cues = segment_aligned_output(aligned_segments)

    assert len(cues) == 1
    assert cues[0].start == 0.0
    assert cues[0].end == 1.5
    assert cues[0].text == "hello world"


def test_long_aligned_segment_splits_on_duration_cap():
    # 20 one-letter words, one per second - way past MAX_SECONDS_PER_CUE if kept together.
    words = [_aligned_word("a", float(i), float(i) + 0.5) for i in range(20)]
    aligned_segments = [{"start": 0.0, "end": 20.0, "text": " ".join("a" for _ in range(20)), "words": words}]

    cues = segment_aligned_output(aligned_segments)

    assert len(cues) > 1
    for cue in cues:
        assert (cue.end - cue.start) <= MAX_SECONDS_PER_CUE


def test_long_aligned_segment_splits_on_char_cap():
    # Words packed with no time gaps, but enough text to blow past MAX_CHARS_PER_CUE.
    words = [_aligned_word("word", i * 0.1, i * 0.1 + 0.09) for i in range(40)]  # 40 * "word" = 160+ chars w/ spaces
    aligned_segments = [{"start": 0.0, "end": 4.0, "text": "word " * 40, "words": words}]

    cues = segment_aligned_output(aligned_segments)

    assert len(cues) > 1
    for cue in cues:
        assert len(cue.text) <= MAX_CHARS_PER_CUE


def test_aligned_cue_boundaries_match_real_word_timing():
    words = [_aligned_word("hi", 0.2, 0.5), _aligned_word("there", 0.6, 1.1)]
    aligned_segments = [{"start": 0.0, "end": 1.2, "text": "hi there", "words": words}]

    cues = segment_aligned_output(aligned_segments)

    assert len(cues) == 1
    assert cues[0].start == 0.2  # first word's real start, not the segment's
    assert cues[0].end == 1.1  # last word's real end


def test_word_missing_alignment_timing_is_interpolated_not_dropped():
    words = [_aligned_word("hello", 0.0, 0.4), {"word": "world"}]  # no start/end on the second word
    aligned_segments = [{"start": 0.0, "end": 1.0, "text": "hello world", "words": words}]

    extracted = words_from_aligned_segments(aligned_segments)

    assert [w.text for w in extracted] == ["hello", "world"]
    assert all(w.end >= w.start for w in extracted)
    assert extracted[-1].end <= 1.0


def test_raw_segments_interpolate_proportionally_within_bounds():
    raw_segments = [{"start": 10.0, "end": 12.0, "text": "one two three four"}]

    words = words_from_raw_segments(raw_segments)

    assert [w.text for w in words] == ["one", "two", "three", "four"]
    # Monotonically increasing and within the segment's own bounds.
    for prev, curr in zip(words, words[1:]):
        assert curr.start >= prev.start
    assert words[0].start >= 10.0
    assert words[-1].end <= 12.0


def test_long_raw_segment_splits_into_readable_cues():
    long_text = " ".join(["word"] * 60)  # 60 * "word" plus spaces, way over MAX_CHARS_PER_CUE
    raw_segments = [{"start": 0.0, "end": 30.0, "text": long_text}]

    cues = segment_raw_output(raw_segments)

    assert len(cues) > 1
    for cue in cues:
        assert len(cue.text) <= MAX_CHARS_PER_CUE
        assert (cue.end - cue.start) <= MAX_SECONDS_PER_CUE
    # Text is fully preserved across cues, in order.
    assert " ".join(cue.text for cue in cues) == long_text


def test_pack_words_into_cues_keeps_short_runs_together():
    words = [TimedWord("a", 0.0, 0.2), TimedWord("b", 0.3, 0.5), TimedWord("c", 0.6, 0.8)]

    cues = _pack_words_into_cues(words, max_chars=84, max_seconds=7.0)

    assert len(cues) == 1
    assert cues[0].text == "a b c"
    assert cues[0].start == 0.0
    assert cues[0].end == 0.8


def test_pack_words_into_cues_respects_explicit_caps():
    words = [TimedWord("aaaa", 0.0, 1.0), TimedWord("bbbb", 1.0, 2.0), TimedWord("cccc", 2.0, 3.0)]

    cues = _pack_words_into_cues(words, max_chars=9, max_seconds=100.0)

    assert len(cues) == 2
    assert cues[0].text == "aaaa bbbb"
    assert cues[1].text == "cccc"


def test_empty_input_produces_no_cues():
    assert segment_aligned_output([]) == []
    assert segment_raw_output([]) == []
