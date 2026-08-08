# Architecture

## Overview

```
frontend (React/Vite, served by nginx) ──/api/*──▶ api (FastAPI)
                                                       │
                                                       ▼
                                                    redis (job queue)
                                                       ▲
                                                       │
                                                    worker (RQ) ──▶ ffmpeg ──▶ faster-whisper ──▶ .srt
```

Four containers:

| Container | Responsibility |
|---|---|
| `frontend` | Static React build served by nginx; proxies `/api/*` to `api` same-origin |
| `api` | FastAPI app. Thin HTTP layer — validates requests, enqueues jobs, reports job status. **Never imports the ML stack.** |
| `redis` | Backing store for the RQ job queue and job status/metadata |
| `worker` | Runs the actual pipeline: ffmpeg audio extraction → faster-whisper transcription → SRT writing |

## Why the API never imports faster-whisper

`app/worker/tasks.py` imports `model_manager`, which imports `faster_whisper`/`ctranslate2`. If any API route imported that module directly, the API container would silently pull in the entire ML stack — defeating the point of keeping it lightweight and device-agnostic.

Instead, routes enqueue jobs **by dotted string path** (`app/worker/task_names.py`) rather than importing the task functions:

```python
queue.enqueue(TASK_TRANSCRIBE_UPLOAD, str(upload_path), file.filename, model_size, resolved_language)
```

RQ resolves and imports the real function only when the **worker** process executes the job. This is verified with a `grep` gate over `app/api` and `app/schemas` (no matches for `worker.tasks`, `model_manager`, or `faster_whisper`) and by checking `pip show faster-whisper` inside the built `api` image, which reports "not found."

## CPU/GPU portability

This is the central non-functional requirement the design is built around: the same worker image needs to run on a CUDA-enabled host and on a plain CPU-only host, without maintaining two separate images.

**One image, not two.** Modern `ctranslate2` (the inference engine behind faster-whisper) ships its CUDA/cuDNN runtime libraries as ordinary pip dependencies. A single `python:3.11-slim`-based image can do both CPU and GPU inference — no `nvidia/cuda` base image is needed. GPU access becomes a purely *runtime* concern: the container needs `--gpus`/a Compose device reservation, and the host needs an NVIDIA driver + `nvidia-container-toolkit`. See `backend/Dockerfile`.

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

`app/core/model_manager.py` holds an LRU cache of loaded `WhisperModel` instances, keyed by `(model_size, device, compute_type)`, capped at `MAX_CACHED_MODELS` (default 1 — safe given VRAM constraints).

The worker runs as **`SimpleWorker`**, not RQ's default `Worker` — this is a specific, deliberate choice. RQ's default worker forks a new OS process per job for crash isolation, but a module-level cache loaded in a forked child is lost when that child exits. `SimpleWorker` runs jobs in a single long-lived process, so the cache actually persists across jobs. The trade-off (no per-job crash isolation) is acceptable for a trusted, single-tenant, local-first tool.

The **model-load pre-check** (`POST /api/models/validate`) enqueues `task_validate_model` on the *same* queue the real transcription jobs run on. `ModelManager.validate()` never raises — it wraps `load()` and always returns a structured `ValidationResult(ok, device_used, fallback_occurred, load_time_ms, error)`. If validation succeeds, the model is now warm in the cache the subsequent real job will hit, so that job's `timings_ms.model_load` is typically ~0 — the completion overlay's elapsed time ends up being close to pure transcription time.

## Pipeline stages

`app/core/pipeline.py`'s `run_transcription_pipeline()` is the single orchestration function shared by both the upload flow and the folder-batch flow:

1. **loading_model** — `model_manager.load()` (no-op on cache hit)
2. **extracting_audio** — ffmpeg, `-vn -ac 1 -ar 16000 -c:a pcm_s16le`, producing 16kHz mono WAV in a per-job temp work dir (never the source folder)
3. **transcribing** — `model.transcribe(..., vad_filter=True)`; timed across the full segment-generator iteration, since faster-whisper does its real work lazily while iterating
4. **writing_subtitles** — pure-function SRT formatting
5. temp audio cleanup (always, success or failure)

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
