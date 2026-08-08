import os

import pytest

from app.core.errors import FolderNotFoundError
from app.core.folder_scanner import scan_folder


def _touch(path, content=b"fake"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def test_scan_folder_raises_when_root_missing(tmp_path):
    with pytest.raises(FolderNotFoundError):
        scan_folder(tmp_path / "does-not-exist")


def test_scan_folder_raises_when_root_is_a_file(tmp_path):
    file_path = tmp_path / "not_a_dir.mp4"
    _touch(file_path)
    with pytest.raises(FolderNotFoundError):
        scan_folder(file_path)


def test_scan_folder_finds_root_and_depth_one_only(tmp_path):
    _touch(tmp_path / "root_video.mp4")
    _touch(tmp_path / "sub" / "nested_video.mkv")
    _touch(tmp_path / "sub" / "deeper" / "too_deep.mp4")  # depth 2, must be excluded
    _touch(tmp_path / "not_a_video.txt")

    results = scan_folder(tmp_path)
    relative_paths = {str(v.relative_path) for v in results}

    nested_relative = os.path.join("sub", "nested_video.mkv")
    assert relative_paths == {"root_video.mp4", nested_relative}


def test_scan_folder_flags_existing_srt(tmp_path):
    video_path = tmp_path / "video.mp4"
    _touch(video_path)
    _touch(tmp_path / "video.srt", content=b"1\n00:00:00,000 --> 00:00:01,000\nhi\n")

    other_video = tmp_path / "other.mp4"
    _touch(other_video)

    results = {v.relative_path.name: v for v in scan_folder(tmp_path)}
    assert results["video.mp4"].existing_srt is True
    assert results["other.mp4"].existing_srt is False


def test_scan_folder_sorted_by_relative_path(tmp_path):
    _touch(tmp_path / "b_video.mp4")
    _touch(tmp_path / "a_video.mp4")

    results = scan_folder(tmp_path)
    assert [str(v.relative_path) for v in results] == ["a_video.mp4", "b_video.mp4"]
