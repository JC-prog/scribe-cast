from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class SubtitleSegment:
    start: float
    end: float
    text: str


def format_timestamp(seconds: float) -> str:
    """SRT timestamp: HH:MM:SS,mmm"""
    if seconds < 0:
        seconds = 0
    total_ms = round(seconds * 1000)
    hours, remainder_ms = divmod(total_ms, 3_600_000)
    minutes, remainder_ms = divmod(remainder_ms, 60_000)
    secs, ms = divmod(remainder_ms, 1_000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def write_srt(segments: Iterable[SubtitleSegment], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    blocks = []
    index = 1
    for segment in segments:
        text = segment.text.strip()
        if not text:
            continue
        blocks.append(
            f"{index}\n"
            f"{format_timestamp(segment.start)} --> {format_timestamp(segment.end)}\n"
            f"{text}\n"
        )
        index += 1
    output_path.write_text("\n".join(blocks), encoding="utf-8")
