from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.core import audio_extractor as audio_extractor_module
from app.core.audio_extractor import extract_audio
from app.core.errors import AudioExtractionError


def test_extract_audio_invokes_ffmpeg_with_expected_args(monkeypatch, tmp_path):
    captured_command = {}

    def fake_run(command, capture_output, text):
        captured_command["command"] = command
        return MagicMock(returncode=0, stderr="")

    monkeypatch.setattr(audio_extractor_module.subprocess, "run", fake_run)

    input_path = tmp_path / "video.mp4"
    output_path = tmp_path / "work" / "audio.wav"

    extract_audio(input_path, output_path)

    command = captured_command["command"]
    assert command[0] == "ffmpeg"
    assert "-i" in command and str(input_path) in command
    assert command[-1] == str(output_path)
    assert "-ar" in command and command[command.index("-ar") + 1] == "16000"
    assert "-ac" in command and command[command.index("-ac") + 1] == "1"


def test_extract_audio_creates_output_parent_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(
        audio_extractor_module.subprocess, "run", lambda *a, **k: MagicMock(returncode=0, stderr="")
    )

    output_path = tmp_path / "nested" / "audio.wav"
    extract_audio(tmp_path / "video.mp4", output_path)

    assert output_path.parent.exists()


def test_extract_audio_raises_on_nonzero_exit(monkeypatch, tmp_path):
    monkeypatch.setattr(
        audio_extractor_module.subprocess,
        "run",
        lambda *a, **k: MagicMock(returncode=1, stderr="Invalid data found"),
    )

    with pytest.raises(AudioExtractionError, match="Invalid data found"):
        extract_audio(tmp_path / "video.mp4", tmp_path / "audio.wav")
