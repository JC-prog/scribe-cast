from dataclasses import dataclass

from app.core.srt_writer import SubtitleSegment

MAX_CHARS_PER_CUE = 84  # ~2 lines x 42 chars, standard subtitle-style-guide convention
MAX_SECONDS_PER_CUE = 7.0


@dataclass
class TimedWord:
    text: str
    start: float
    end: float


def _words_from_one_aligned_segment(segment: dict) -> list[TimedWord]:
    raw_words = segment.get("words") or []
    missing = [w for w in raw_words if "start" not in w or "end" not in w]
    if missing:
        # A word occasionally has no alignment timing (whisperx couldn't
        # align it); rather than drop its text, interpolate its span from
        # the enclosing segment's own start/end, proportional to
        # character position - same technique as the raw-segment path,
        # just scoped to one segment for better accuracy.
        return _interpolate_words(segment["start"], segment["end"], [w["word"] for w in raw_words])
    return [TimedWord(text=w["word"], start=w["start"], end=w["end"]) for w in raw_words]


def words_from_aligned_segments(aligned_segments: list[dict]) -> list[TimedWord]:
    """Flattened word stream across all segments, for inspection - cue generation uses
    segment_aligned_output, which packs per-segment so cues never merge across an
    original segment's natural pause boundary."""
    words: list[TimedWord] = []
    for segment in aligned_segments:
        words.extend(_words_from_one_aligned_segment(segment))
    return words


def words_from_raw_segments(raw_segments: list[dict]) -> list[TimedWord]:
    """
    For segment-level-only output (no word timing - the translate path,
    which skips forced alignment): distributes each segment's duration
    across its whitespace-split tokens proportional to character length.
    An approximation (assumes uniform reading pace), but far better than
    one cue per ~30s ASR batch chunk.
    """
    words: list[TimedWord] = []
    for segment in raw_segments:
        words.extend(_interpolate_words(segment["start"], segment["end"], segment["text"].split()))
    return words


def _interpolate_words(start: float, end: float, tokens: list[str]) -> list[TimedWord]:
    if not tokens:
        return []
    duration = end - start
    total_chars = sum(len(t) for t in tokens)
    words = []
    cursor_chars = 0
    for token in tokens:
        frac_start = cursor_chars / total_chars if total_chars else 0.0
        cursor_chars += len(token)
        frac_end = cursor_chars / total_chars if total_chars else 1.0
        words.append(TimedWord(text=token, start=start + frac_start * duration, end=start + frac_end * duration))
    return words


def _pack_words_into_cues(
    words: list[TimedWord], max_chars: int = MAX_CHARS_PER_CUE, max_seconds: float = MAX_SECONDS_PER_CUE
) -> list[SubtitleSegment]:
    cues: list[SubtitleSegment] = []
    current: list[TimedWord] = []
    current_chars = 0

    for word in words:
        added_chars = len(word.text) + (1 if current else 0)  # +1 for the joining space
        candidate_duration = word.end - current[0].start if current else 0.0
        if current and (current_chars + added_chars > max_chars or candidate_duration > max_seconds):
            cues.append(_flush(current))
            current = []
            current_chars = 0
            added_chars = len(word.text)
        current.append(word)
        current_chars += added_chars

    if current:
        cues.append(_flush(current))
    return cues


def _flush(words: list[TimedWord]) -> SubtitleSegment:
    return SubtitleSegment(start=words[0].start, end=words[-1].end, text=" ".join(w.text for w in words))


def segment_aligned_output(
    aligned_segments: list[dict], max_chars: int = MAX_CHARS_PER_CUE, max_seconds: float = MAX_SECONDS_PER_CUE
) -> list[SubtitleSegment]:
    """Packs each original segment's words into cues independently (never merging across
    segments) - segment boundaries already mark a natural pause, which is a cue break
    worth keeping; the cap only kicks in when a single segment is itself too long."""
    cues: list[SubtitleSegment] = []
    for segment in aligned_segments:
        cues.extend(_pack_words_into_cues(_words_from_one_aligned_segment(segment), max_chars, max_seconds))
    return cues


def segment_raw_output(
    raw_segments: list[dict], max_chars: int = MAX_CHARS_PER_CUE, max_seconds: float = MAX_SECONDS_PER_CUE
) -> list[SubtitleSegment]:
    cues: list[SubtitleSegment] = []
    for segment in raw_segments:
        words = _interpolate_words(segment["start"], segment["end"], segment["text"].split())
        cues.extend(_pack_words_into_cues(words, max_chars, max_seconds))
    return cues
