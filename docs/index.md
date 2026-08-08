# scribe-cast

Local-first video transcription. Upload a video (or point at a folder) and get back an `.srt` subtitle file, transcribed with [faster-whisper](https://github.com/SYSTRAN/faster-whisper).

Everything runs on your own machine via Docker — video never leaves your host.

## Where to go next

<div class="grid cards" markdown>

- **[Getting Started](getting-started.md)**
  Prerequisites, `.env` setup, and the Docker Compose commands to bring the stack up on a CPU-only host or the CUDA host.

- **[Usage](usage.md)**
  Walkthrough of the upload flow and the folder-batch flow, model/language selection, and reading job progress.

- **[Features](features.md)**
  What scribe-cast does, feature by feature.

- **[Architecture](architecture.md)**
  How the pieces fit together: FastAPI + Redis/RQ worker + faster-whisper, the CPU/GPU portability design, logging.

- **[Development](development.md)**
  Backend and frontend dev setup, running the pytest and Playwright e2e suites, project conventions.

</div>

## At a glance

```
frontend (React/Vite, served by nginx) ──/api/*──▶ api (FastAPI)
                                                       │
                                                       ▼
                                                    redis (job queue)
                                                       ▲
                                                       │
                                                    worker (RQ) ──▶ ffmpeg ──▶ faster-whisper ──▶ .srt
```

- The **api** container never imports the ML stack (faster-whisper/ctranslate2) — it stays lightweight regardless of whether you're running on CPU or GPU.
- The **worker** container does the real work and is the only place a GPU is used, when one's available.
- The same worker Docker image runs on a CPU-only host or the CUDA host — device selection is a runtime decision, not a build-time one. See [Architecture](architecture.md#cpugpu-portability) for why.
