# scribe-cast

Local-first video transcription. Upload a video (or point at a folder) and get back an `.srt` subtitle file, transcribed with [faster-whisper](https://github.com/SYSTRAN/faster-whisper).

## Features

- **Single upload** — upload a video, download the generated `.srt` when it's done. The completion overlay shows how long transcription took.
- **Folder batch** — point at a folder; scribe-cast searches it plus one level of subfolders for videos, lets you pick which ones, and writes each `.srt` next to its source video.
- **Model & language selection** — pick a Whisper model size and target language (or auto-detect) per job. Before running a job, scribe-cast tries to load the model and warns you if it can't.
- **CPU/GPU portable** — the same worker image runs on a CPU-only host or a CUDA host; if a GPU is requested but unavailable, it falls back to CPU automatically and tells you.
- **Observability** — structured JSON logs in `logs/` (model load latency, transcription duration, errors), separate from container stdout.

## Architecture

```
frontend (React/Vite, served by nginx) ──/api/*──▶ api (FastAPI)
                                                       │
                                                       ▼
                                                    redis (job queue)
                                                       ▲
                                                       │
                                                    worker (RQ) ──▶ ffmpeg ──▶ faster-whisper ──▶ .srt
```

- **api** never imports the ML stack (faster-whisper/ctranslate2) — routes enqueue jobs by name, so the API container stays lightweight regardless of device.
- **worker** runs as a single non-forking process so a loaded Whisper model stays cached in memory across jobs instead of reloading per request.
- Audio is extracted from the video (ffmpeg, 16kHz mono) before transcription — smaller intermediate files, and it decouples video-codec handling from the ASR step.

## Prerequisites

- Docker Desktop (with Compose v2)
- **GPU host only:** an NVIDIA driver + [nvidia-container-toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) installed on the host

## Running it

```bash
cp .env.example .env
# edit .env: set DATA_DIR to the folder you want available for folder-batch jobs
mkdir -p data   # or point DATA_DIR at an existing folder of videos

# CPU-only host:
docker compose up -d --build

# CUDA host (this repo's primary target):
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build
```

Then open http://localhost:5173.

Folder-batch paths are entered as they appear **inside the container**, under `/data/...` — that's where your host's `DATA_DIR` is bind-mounted. E.g. if `DATA_DIR=D:\Videos` and you have `D:\Videos\learning\lecture1.mp4`, scan `/data` or `/data/learning` in the UI; the `.srt` is written back to `D:\Videos\learning\lecture1.srt` on the host.

Logs land in `./logs/` (`api.log`, `worker.log`, `errors.log`) as JSON lines, bind-mounted from both containers.

## Development

### Backend

```bash
cd backend
python -m venv .venv
./.venv/Scripts/pip install -r requirements-dev.txt   # includes faster-whisper/ctranslate2 for mocking in tests
./.venv/Scripts/python -m pytest
```

Tests are hermetic — no real Redis, ffmpeg, or model download/inference required (external calls are mocked; API tests use `fakeredis`).

To run the API and worker outside Docker, you need a local Redis and ffmpeg on PATH:

```bash
uvicorn app.main:app --reload           # from backend/, api process
python -m app.worker.rq_worker          # from backend/, worker process
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # proxies /api/* to localhost:8000, see vite.config.ts
```

### End-to-end tests

Needs a live stack (real Redis/api/worker — either `docker compose up` or `npm run dev` against a locally running backend), since it exercises real model loading and ffmpeg, not mocks:

```bash
cd frontend
npm run test:e2e:install   # first time only, installs the Playwright browser
npm run test:e2e
```

## Configuration (`.env`)

| Variable | Default | Meaning |
|---|---|---|
| `DATA_DIR` | `./data` | Host folder bind-mounted to `/data` in the api/worker containers, for folder-batch jobs |
| `DEVICE` | `auto` | `auto` \| `cuda` \| `cpu`. `docker-compose.gpu.yml` overrides this to `cuda`. `auto`/`cuda` fall back to CPU with a logged warning if no GPU is actually available |
| `COMPUTE_TYPE` | *(unset)* | Overrides the device-appropriate default (`float16` on GPU, `int8` on CPU) — e.g. `int8_float16` |
