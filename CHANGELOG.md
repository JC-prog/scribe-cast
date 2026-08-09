# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-08-09

### Changed

- Subtitle cue timestamps are now trimmed to the first/last actual spoken word in each segment (faster-whisper's `word_timestamps=True`), instead of Whisper's raw segment-level `start`/`end`, which drift around silence. No new dependencies.

## [1.0.0] - 2026-08-09

### Added

- Paste-a-link transcription: paste a YouTube (or any yt-dlp-supported) URL, downloaded audio-only via `yt-dlp` and run through the same transcription pipeline as upload/folder-batch jobs.
- `docs/` — MkDocs (Material) documentation site: Getting Started, Usage, Features, Architecture, Development.
- `scripts/` — dev/build/stack/test/docs automation, with bash and PowerShell variants.
- `VERSION` and this changelog.

### Changed

- Frontend redesigned around a boxed panel/dashboard layout.
- `app/main.py` moved to `app/api/main.py`, so `worker/` reads as a sibling service rather than a subcomponent of `api/`.

### Fixed

- GPU inference (`DEVICE=cuda`) failed at the first real `transcribe()` call with `Library libcublas.so.12 is not found or cannot be loaded`, even though driver/GPU passthrough and model *construction* both succeeded. `ctranslate2` does not declare `nvidia-cublas-cu12`/`nvidia-cudnn-cu12` as dependencies and does not locate their pip-installed `.so` files on its own; the worker image now pins both packages and sets `LD_LIBRARY_PATH` to their `site-packages` lib directories.

## [0.1.0] - 2026-08-09

Initial release.

### Added

- Single video upload with transcription and `.srt` download; completion overlay shows elapsed transcription time.
- Folder-batch transcription: recursive scan of a folder plus one level of subfolders, per-video selection, subtitles written next to their source videos.
- Model size and language selection, gated by a pre-flight model-load check (`POST /api/models/validate`) before a job is committed.
- CPU/GPU portability as a core design constraint: a single worker image with runtime device resolution (`auto`/`cuda`/`cpu`), automatic fallback to CPU when a requested GPU isn't actually available, and that fallback surfaced to the user rather than silent.
- Structured JSON logging to `logs/` (model load latency, transcription duration, errors), separate from container stdout.
- FastAPI backend with a Redis/RQ job queue and a non-forking worker (so a loaded model stays cached across jobs); React/Vite frontend; Docker Compose setup (CPU-safe base + GPU override file).
- Backend pytest suite (hermetic — no live Redis/ffmpeg/model required) and a Playwright end-to-end suite covering the upload and folder-batch flows.
