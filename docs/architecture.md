# Architecture

## Overview

```
frontend (React/Vite, served by nginx) ──/api/*──▶ api (FastAPI)
                                                       │
                                                       ▼
                                                    redis (job queue)
                                                       ▲
                                                       │
                                        worker (RQ) ──▶ ffmpeg ──▶ WhisperX (ASR + forced alignment) ──▶ .srt
```

Four containers:

| Container | Responsibility |
|---|---|
| `frontend` | Static React build served by nginx; proxies `/api/*` to `api` same-origin |
| `api` | FastAPI app. Thin HTTP layer — validates requests, enqueues jobs, reports job status. **Never imports the ML stack.** |
| `redis` | Backing store for the RQ job queue and job status/metadata |
| `worker` | Runs the actual pipeline: ffmpeg audio extraction → WhisperX batched transcription → wav2vec2 forced alignment → SRT writing |

## Why the API never imports the ML stack

`app/worker/tasks.py` imports `model_manager`, which imports `whisperx` (and, through it, `torch`/`faster_whisper`/`ctranslate2`). If any API route imported that module directly, the API container would silently pull in the entire ML stack — defeating the point of keeping it lightweight and device-agnostic.

Instead, routes enqueue jobs **by dotted string path** (`app/worker/task_names.py`) rather than importing the task functions:

```python
queue.enqueue(TASK_TRANSCRIBE_UPLOAD, str(upload_path), file.filename, model_size, resolved_language)
```

RQ resolves and imports the real function only when the **worker** process executes the job. This is verified with a `grep` gate over `app/api` and `app/schemas` (no matches for `worker.tasks`, `model_manager`, or `whisperx`) and by checking `pip show whisperx` inside the built `api` image, which reports "not found."

## CPU/GPU portability

This is the central non-functional requirement the design is built around: the same worker image needs to run on a CUDA-enabled host and on a plain CPU-only host, without maintaining two separate images.

**One image, not two.** `whisperx` wraps `faster-whisper`/`ctranslate2` for the ASR pass and `torch`/`torchaudio` for wav2vec2 forced alignment; both can do CUDA inference without needing CUDA baked into the OS image, via pip-installable `nvidia-*-cu12` runtime packages. Getting there needs two things this repo wires up explicitly, neither of which `ctranslate2` handles on its own:

1. **The cuBLAS/cuDNN shared libraries themselves.** `ctranslate2` does not declare them as install dependencies (`pip show ctranslate2` lists only `numpy`/`pyyaml`/`setuptools`) — but `whisperx`'s own `torch` dependency does, and pulls compatible versions transitively. This matters concretely: `torch` is strict about exact companion `nvidia-cublas-cu12`/`nvidia-cudnn-cu12` versions, and those do **not** match the versions `ctranslate2` alone was happy with pre-`whisperx` — pinning them ourselves (as an earlier version of this file did) would fight `torch`'s own resolution. `requirements-worker.txt` now leaves them to `whisperx`'s transitive resolution rather than pinning explicitly.
2. **Making those libraries findable at runtime.** `pip` puts their `.so` files inside `site-packages`, not on the default dynamic linker search path, and `ctranslate2` does not locate them automatically (unlike `torch`, which manages its own `nvidia-*-cu12` companions via a different mechanism and does not need this). `backend/Dockerfile`'s worker stage sets `LD_LIBRARY_PATH` to the relevant `site-packages/nvidia/*/lib` directories for this reason.

Skipping either step surfaces the same misleading symptom: `ctranslate2.get_cuda_device_count()` still returns `>0` and model *construction* still succeeds (`nvidia-smi` works, the driver/GPU passthrough is fine), because neither of those touches cuBLAS. The failure only shows up at the first real `transcribe()` call, when the encoder actually needs a cuBLAS GEMM, as `Library libcublas.so.12 is not found or cannot be loaded`. A model-load pre-check alone (see below) won't catch this class of failure, since it never runs actual inference — the same gap applies to the forced-alignment step, which is a second, separate model with its own load-vs-use distinction. With both pieces in place, a single `python:3.11-slim`-based image can do both CPU and GPU inference; no `nvidia/cuda` base image is needed. GPU access itself is a purely *runtime* concern: the container needs `--gpus`/a Compose device reservation, and the host needs an NVIDIA driver + `nvidia-container-toolkit`. See `backend/Dockerfile`.

**CPU-only hosts pay a real cost for this, not just a theoretical one.** Adopting `whisperx` means every install — including CPU-only ones — now pulls the full `torch`/`torchaudio`/`pyannote-audio`/`transformers` stack (whisperx uses `torch` for forced alignment regardless of device), which is a meaningfully heavier image and slower CPU inference than the plain `ctranslate2`-only setup this repo shipped before. This was a deliberate trade-off (full replacement over a dual-engine config flag) made in exchange for materially better subtitle timestamp accuracy; see the changelog for `v2.0.0`.

**`vad_method="silero"` is deliberate, not `whisperx`'s default.** `whisperx.load_model()` defaults to `vad_method="pyannote"`, a gated Hugging Face model requiring an auth token. `app/core/model_manager.py` passes `vad_method="silero"` explicitly — ungated, fully local — so the core transcription path never needs a Hugging Face account. (Speaker diarization, a separate opt-in `whisperx` feature this repo does not use, would still need one.)

**Device resolution is centralized** in `app/core/device.py`:

```python
def resolve_device(requested: "auto" | "cuda" | "cpu", compute_type_override=None) -> DeviceResolution:
    ...
```

- `requested="cpu"` → always CPU.
- `requested="cuda"` → checks `ctranslate2.get_cuda_device_count() > 0`; if no GPU is actually usable, logs a warning and **falls back to CPU** (`fallback_occurred=True`).
- `requested="auto"` (default) → GPU if available, else CPU, no fallback flag (CPU was an acceptable outcome either way).

`compute_type` defaults to `float16` on GPU and `int8` on CPU, overridable via `COMPUTE_TYPE`.

**Two Compose files, not two images:**

- `docker-compose.yml` — base, CPU-safe, no GPU reservation, `DEVICE=auto`.
- `docker-compose.gpu.yml` — override, adds a GPU device reservation and `DEVICE=cuda`. Layered on top with `-f docker-compose.yml -f docker-compose.gpu.yml`.

**Fallback is visible, not silent.** `device_used` and `fallback_occurred` are threaded through `ModelManager` → job meta → the API → the frontend, so a user who forces `DEVICE=cuda` on a host without a working GPU sees a warning banner rather than just slower-than-expected transcription.

## Model manager & the load pre-check

`app/core/model_manager.py` holds two separate LRU caches, each capped at `MAX_CACHED_MODELS` (default 1 — safe given VRAM constraints): one for loaded `whisperx` ASR pipelines, keyed by `(model_size, device, compute_type)`, and one for wav2vec2 alignment models, keyed by `(language, device)` — alignment models are per-language, not per-model-size, so they can't share the ASR cache's key shape.

The worker runs as **`SimpleWorker`**, not RQ's default `Worker` — this is a specific, deliberate choice. RQ's default worker forks a new OS process per job for crash isolation, but a module-level cache loaded in a forked child is lost when that child exits. `SimpleWorker` runs jobs in a single long-lived process, so the cache actually persists across jobs. The trade-off (no per-job crash isolation) is acceptable for a trusted, single-tenant, local-first tool.

The **model-load pre-check** (`POST /api/models/validate`) enqueues `task_validate_model` on the *same* queue the real transcription jobs run on. `ModelManager.validate()` never raises — it wraps `load()` and always returns a structured `ValidationResult(ok, device_used, fallback_occurred, load_time_ms, error)`. If validation succeeds, the model is now warm in the cache the subsequent real job will hit, so that job's `timings_ms.model_load` is typically ~0 — the completion overlay's elapsed time ends up being close to pure transcription time.

## Pipeline stages

`app/core/pipeline.py`'s `run_transcription_pipeline()` is the single orchestration function shared by both the upload flow and the folder-batch flow:

1. **loading_model** — `model_manager.load()` (no-op on cache hit)
2. **extracting_audio** — ffmpeg, `-vn -ac 1 -ar 16000 -c:a pcm_s16le`, producing 16kHz mono WAV in a per-job temp work dir (never the source folder)
3. **transcribing** — `whisperx`'s batched ASR pass (`app/core/transcriber.py::transcribe`); unlike plain faster-whisper's lazy segment generator, this returns a fully materialized result from one blocking call
4. **aligning** — forced alignment (`app/core/transcriber.py::align`): re-times every word against the audio with a wav2vec2 phoneme model, producing tighter segment boundaries than Whisper's own segment-level timestamps; the alignment model is loaded via `model_manager.load_align_model()`, a second cache lookup keyed by the detected language
5. **writing_subtitles** — pure-function SRT formatting, from the *aligned* segments
6. temp audio cleanup (always, success or failure)

Each stage transition is reported through a callback rather than a direct RQ dependency, so `core/` has no import of the queue layer — `worker/tasks.py` wires the callback to `job.meta` updates.

## Job queue design

- **Job meta** (`worker/job_meta.py`) is the live-progress channel: RQ only populates `.result` after a job function returns, so `.meta` (updated via `update_job_meta()` at each stage transition) is what the API can report *while* a job is running.
- **Folder batch = N independent jobs**, not one big job — each video gets its own job (reusing the same task function), correlated by a `batch_id`. The API stores `batch:{batch_id} -> [job_ids]` in Redis (TTL'd) so `GET /api/jobs/batch/{batch_id}` is a single aggregate lookup instead of the frontend polling N endpoints.
- **Polling, not push.** The frontend polls `GET /api/jobs/{id}` (or `/batch/{id}`) every ~1.2s. This was a deliberate simplicity choice over SSE/WebSockets, which would need Redis pub/sub layered on top for marginal benefit at this scale.

## Folder scanning & path safety

`app/core/folder_scanner.py` scans a root directory plus exactly one level of subfolders (two explicit `iterdir()` passes, rather than tracking a depth counter through `os.walk` — makes the depth-1 limit hard to get wrong).

`resolve_selected_videos()` defends `POST /api/folder/transcribe` against a tampered or stale request: every submitted path must resolve to somewhere inside the originally-scanned root and must still exist, or the request is rejected with 400.

## Logging

`app/logging_config.py` configures structured JSON logging once per process:

- `logs/api.log` / `logs/worker.log` — component-specific rotating file handlers
- `logs/errors.log` — shared, ERROR+ from either component, for cross-component grepping
- stdout — visible via `docker compose logs`

`log_event(logger, event, **fields)` keeps field names (`job_id`, `model`, `device`, `duration_ms`, `stage`, ...) consistent across call sites, and guards against passing a field name that collides with a reserved Python `LogRecord` attribute (e.g. `filename`), which would otherwise crash deep inside the logging module with a confusing `KeyError`.
