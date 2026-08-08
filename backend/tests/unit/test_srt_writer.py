from app.core.srt_writer import SubtitleSegment, format_timestamp, write_srt


def test_format_timestamp_zero():
    assert format_timestamp(0) == "00:00:00,000"


def test_format_timestamp_sub_second():
    assert format_timestamp(1.234) == "00:00:01,234"


def test_format_timestamp_hour_rollover():
    assert format_timestamp(3661.5) == "01:01:01,500"


def test_format_timestamp_negative_clamped_to_zero():
    assert format_timestamp(-5) == "00:00:00,000"


def test_write_srt_formats_blocks_and_skips_empty_text(tmp_path):
    segments = [
        SubtitleSegment(start=0.0, end=1.5, text="Hello there"),
        SubtitleSegment(start=1.5, end=1.5, text="   "),  # blank, should be skipped
        SubtitleSegment(start=2.0, end=3.25, text="Second line"),
    ]
    output_path = tmp_path / "out.srt"

    write_srt(segments, output_path)

    content = output_path.read_text(encoding="utf-8")
    assert content == (
        "1\n"
        "00:00:00,000 --> 00:00:01,500\n"
        "Hello there\n"
        "\n"
        "2\n"
        "00:00:02,000 --> 00:00:03,250\n"
        "Second line\n"
    )


def test_write_srt_creates_parent_dirs(tmp_path):
    output_path = tmp_path / "nested" / "dir" / "out.srt"
    write_srt([SubtitleSegment(start=0, end=1, text="hi")], output_path)
    assert output_path.exists()
