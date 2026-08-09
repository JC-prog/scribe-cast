import pytest
from yt_dlp.utils import DownloadError as YtDlpDownloadError

from app.core import video_downloader as video_downloader_module
from app.core.errors import VideoDownloadError
from app.core.video_downloader import download_video


class FakeYoutubeDL:
    def __init__(self, opts):
        self.opts = opts

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def extract_info(self, url, download):
        return {"title": "My Video"}

    def prepare_filename(self, info):
        path = self.opts["outtmpl"].replace("%(ext)s", "webm")
        with open(path, "wb") as f:
            f.write(b"fake audio")
        return path


class FailingYoutubeDL(FakeYoutubeDL):
    def extract_info(self, url, download):
        raise YtDlpDownloadError("Unsupported URL")


def test_download_video_returns_result_with_title_and_path(monkeypatch, tmp_path):
    monkeypatch.setattr(video_downloader_module, "YoutubeDL", FakeYoutubeDL)

    result = download_video("https://example.com/watch?v=abc", tmp_path)

    assert result.title == "My Video"
    assert result.path.is_file()
    assert result.source_url == "https://example.com/watch?v=abc"


def test_download_video_raises_video_download_error_on_yt_dlp_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(video_downloader_module, "YoutubeDL", FailingYoutubeDL)

    with pytest.raises(VideoDownloadError, match="Unsupported URL"):
        download_video("https://example.com/not-a-video", tmp_path)


def test_download_video_creates_work_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(video_downloader_module, "YoutubeDL", FakeYoutubeDL)
    work_dir = tmp_path / "nested" / "work"

    download_video("https://example.com/watch?v=abc", work_dir)

    assert work_dir.exists()
