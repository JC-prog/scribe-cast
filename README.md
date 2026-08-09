# scribe-cast

![Version](https://img.shields.io/badge/version-2.1.0-7c3aed)
![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Node](https://img.shields.io/badge/node-22-green)

Local-first video transcription. Upload a video (or point at a folder) and get back an `.srt` subtitle file, transcribed and forced-aligned with [WhisperX](https://github.com/m-bain/whisperX). Everything runs on your own machine via Docker, so video never leaves your host.

**Full documentation:** [`docs/`](docs/index.md) (browse on GitHub, or run `scripts/docs.sh serve` / `scripts\docs.ps1 serve` for the built [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) site at `http://localhost:8000`).

## Features

- **Single upload:** upload a video, download the generated `.srt`; a completion overlay shows how long transcription took.
- **Folder batch:** point at a folder, pick which discovered videos to process, get an `.srt` next to each source video.
- **Model & language selection:** per job, with a pre-flight check that a chosen model can actually load before committing to the job.
- **CPU/GPU portable:** the same worker image runs on a CPU-only host or a CUDA host; a requested-but-unavailable GPU falls back to CPU automatically, with a visible warning.
- **Observability:** structured JSON logs in `logs/` for model latency, transcription duration, and errors.

See [`docs/features.md`](docs/features.md) for detail on each.

## Architecture

```
frontend (React/Vite, served by nginx) ──/api/*──▶ api (FastAPI)
                                                       │
                                                       ▼
                                                    redis (job queue)
                                                       ▲
                                                       │
                                        worker (RQ) ──▶ ffmpeg ──▶ WhisperX (ASR + forced alignment) ──▶ .srt
```

The `api` container never imports the ML stack; the `worker` container does the real work and is the only place a GPU is used, when one's available. See [`docs/architecture.md`](docs/architecture.md) for the full design, especially the [CPU/GPU portability](docs/architecture.md#cpugpu-portability) section, since it's the design constraint most of this repo's structure is built around.

## Quick start

```bash
cp .env.example .env
# edit .env: set DATA_DIR to the folder you want available for folder-batch jobs
```

Then, on a CPU-only host:

```bash
scripts/stack.sh up        # or: scripts\stack.ps1 up
```

or on a CUDA host:

```bash
scripts/stack.sh up --gpu  # or: scripts\stack.ps1 up -Gpu
```

Open [http://localhost:5173](http://localhost:5173). See [`docs/getting-started.md`](docs/getting-started.md) for prerequisites and the `/data/...` path-mapping caveat for folder-batch jobs.

## Scripts

| Script | Does |
|---|---|
| `scripts/setup-dev.{sh,ps1}` | Bootstrap a local dev environment: `.env`, backend venv + deps, frontend deps |
| `scripts/build.{sh,ps1}` | Build the Docker images (`--gpu`/`-Gpu` to layer the GPU override) |
| `scripts/stack.{sh,ps1}` | `up` / `down` / `logs` for the Compose stack (`--gpu`/`-Gpu` supported) |
| `scripts/test.{sh,ps1}` | Run the backend pytest suite (`--e2e`/`-E2e` for the frontend Playwright suite instead) |
| `scripts/docs.{sh,ps1}` | `serve` / `build` this documentation site |

## Development

```bash
scripts/setup-dev.sh   # or scripts\setup-dev.ps1
scripts/test.sh         # or scripts\test.ps1 - backend unit tests
cd frontend && npm run dev
```

See [`docs/development.md`](docs/development.md) for the full project layout, e2e test setup, and conventions.

## Changelog

See [`CHANGELOG.md`](CHANGELOG.md).

## License

[MIT](LICENSE)
