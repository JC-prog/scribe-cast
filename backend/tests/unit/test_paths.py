from pathlib import Path

from app.core.paths import derive_output_path, has_existing_subtitle


def test_derive_output_path_same_dir_and_basename():
    video_path = Path("/data/learning/video_1.mp4")
    assert derive_output_path(video_path) == Path("/data/learning/video_1.srt")


def test_derive_output_path_handles_multiple_dots():
    video_path = Path("/data/my.video.file.mkv")
    assert derive_output_path(video_path) == Path("/data/my.video.file.srt")


def test_has_existing_subtitle_false_when_missing(tmp_path):
    video_path = tmp_path / "video.mp4"
    video_path.write_bytes(b"fake")
    assert has_existing_subtitle(video_path) is False


def test_has_existing_subtitle_true_when_present(tmp_path):
    video_path = tmp_path / "video.mp4"
    video_path.write_bytes(b"fake")
    (tmp_path / "video.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nhi\n")
    assert has_existing_subtitle(video_path) is True
