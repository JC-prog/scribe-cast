# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Recent jobs / history panel (new sidebar tab): `GET /api/jobs` lists jobs across every RQ state (queued, running, finished, failed), most recent first, so a job stays visible and its `.srt` downloadable after the completion overlay is dismissed or the tab is closed. Required a real retention fix alongside the new endpoint - none of the enqueue call sites previously set `result_ttl`/`failure_ttl`, so RQ's default (finished jobs expire after ~500 seconds) meant a "history" view would have gone empty within minutes; jobs now persist for 7 days.

## [2.3.0] - 2026-08-09

### Added

- Admin panel (new sidebar tab) for tuning WhisperX behavior and subtitle formatting at runtime, without a container restart: `batch_size`, `chunk_size`, `beam_size`, `temperature`, `condition_on_previous_text`, VAD method (`silero`/`pyannote`, with a Hugging Face token field for the latter), and the `max_chars_per_cue`/`max_seconds_per_cue` caps from the previous release. Backed by `GET`/`PATCH`/`POST reset` `/api/admin/settings`, persisted in Redis. Defaults match what was previously hardcoded, so out-of-the-box behavior is unchanged until the panel is actually used. `hf_token` is never echoed back once set — only a `hf_token_set` boolean is exposed, and partial updates leave it untouched unless a new value (or an explicit empty string, to clear it) is sent.

## [2.2.0] - 2026-08-09

### Fixed

- Subtitle cues could span an entire long stretch of continuous speech as one unbroken block of text (up to ~30s in the translate path, or a full multi-sentence run in the aligned path when there wasn't a long clean pause) — nothing capped cue duration or length before writing the `.srt`. Cues are now packed to a max of ~84 characters / 7 seconds each, using real per-word timing from forced alignment where available and proportional interpolation within each original segment otherwise, so segment boundaries (natural pauses) still stay as cue breaks and only overlong segments actually get split.

## [2.1.0] - 2026-08-09

### Added

- `GET /api/version`, backed by a new `APP_VERSION` setting, logged at worker startup too — makes "what version is this container actually running" inspectable at runtime instead of having to infer it from commit timestamps vs. container `CREATED` time.
- `docker-compose.yml`'s `api`/`worker`/`frontend` services now build tagged images (`scribe-cast-worker:2.0.0` etc.) instead of always `:latest`. `scripts/build.*`/`scripts/stack.*` export `VERSION` from the repo-root `VERSION` file before invoking `docker compose`, so the `VERSION` file stays the single source of truth (not duplicated into `.env`). Falls back to `latest`/`0.0.0-dev` if invoked without the scripts.
- Translate-to-English mode: a `translate` toggle on all three transcription flows, backed by WhisperX's translate task. Forced alignment is skipped when translating (a phoneme-alignment model can't match English output text against non-English source audio), falling back to Whisper's own segment-level timestamps.

### Changed

- The "Language" selector is relabeled "Audio language" with a hint clarifying it's a source-language hint, not a translation target — the previous label was easy to misread as a target-language picker, which actively corrupts transcription when misused (forces the wrong language's phonetics onto the audio).
- Frontend redesigned around a persistent sidebar nav (replacing the top tab bar), with `lucide-react` icons, real loading spinners, an animated in-flight progress indicator, and motion on panels/pages/the completion overlay.

## [2.0.0] - 2026-08-09

### Changed

- **Breaking:** the transcription engine is now [WhisperX](https://github.com/m-bain/whisperX) instead of plain faster-whisper — batched ASR followed by real wav2vec2 forced alignment, producing meaningfully tighter subtitle timestamps than v1.1.0's word-boundary trimming (which stays as a stepping stone in history, superseded here). New pipeline stage: `aligning`, between `transcribing` and `writing_subtitles`.
- `app/core/model_manager.py` now holds two LRU caches: ASR models keyed by `(model_size, device, compute_type)` as before, plus a new one for wav2vec2 alignment models keyed by `(language, device)`.
- VAD explicitly set to `vad_method="silero"` (WhisperX defaults to a gated `pyannote` model requiring a Hugging Face token) — keeps the "no HF account needed" property of the core transcription path. Diarization, a separate opt-in WhisperX feature that does need a token, is not used.
- Worker image now installs the full `torch`/`torchaudio`/`pyannote-audio`/`transformers` stack (`whisperx`'s dependencies) instead of just `faster-whisper`/`ctranslate2` — a real, accepted image-size and CPU-inference-speed cost on every install, including CPU-only hosts, in exchange for the alignment quality improvement. `nvidia-cublas-cu12`/`nvidia-cudnn-cu12` are no longer pinned explicitly in `requirements-worker.txt`; `torch`'s own dependency resolution is strict about exact companion versions and now drives them.
- `docker-compose.yml`'s worker service sets `TORCH_HOME=/app/model_cache/torch` so WhisperX's Silero VAD and wav2vec2 alignment model downloads land in the existing persisted `model_cache` volume instead of re-downloading on every container recreate.

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
