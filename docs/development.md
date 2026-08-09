# Development

## Project layout

```
backend/
  app/
    api/routes/     # thin HTTP handlers
    core/            # business logic: pipeline, model manager, device resolution,
                      # audio extraction, SRT writing, folder scanning
    worker/          # RQ task functions, job meta, worker entrypoint
    schemas/         # pydantic request/response models
  tests/
    unit/            # no external services required
    api/             # FastAPI TestClient + fakeredis
frontend/
  src/
    api/             # fetch client + types
    hooks/           # useModels, useLanguages, useJobPolling, useModelValidation
    pages/           # UploadPage, FolderBatchPage
    components/
  e2e/               # Playwright, needs a live stack
docs/                # this site
scripts/             # setup-dev, build, stack, test, docs — bash + PowerShell
```

## Quick setup

```bash
scripts/setup-dev.sh   # or scripts\setup-dev.ps1
```

Creates `.env` from `.env.example`, `data/`/`logs/` directories, a backend `.venv` with `requirements-dev.txt` installed, and runs `npm install` in `frontend/`. Safe to re-run. The manual steps below are what it does under the hood, useful if you want to run a subset or understand what's happening.

## Backend

```bash
cd backend
python -m venv .venv
./.venv/Scripts/pip install -r requirements-dev.txt   # includes whisperx (torch/faster-whisper/ctranslate2), needed to mock its ASR/align models in tests
./.venv/Scripts/python -m pytest
```

Or, once `scripts/setup-dev` has been run once: `scripts/test.sh` (or `scripts\test.ps1`).

Tests are hermetic — no real Redis, ffmpeg, or model download/inference is required. External calls are mocked (`subprocess.run` for ffmpeg, `whisperx.load_model`/`whisperx.align` for the ASR/alignment models, `fakeredis` for the queue layer in API tests).

To run the API and worker outside Docker, you need a local Redis and ffmpeg on `PATH`:

```bash
uvicorn app.api.main:app --reload       # from backend/, api process
python -m app.worker.rq_worker          # from backend/, worker process
```

The worker must run as `SimpleWorker` (already the case in `rq_worker.py`) — see [Architecture → Model manager](architecture.md#model-manager-the-load-pre-check) for why. On Windows, note that RQ's default signal-based job timeout (`SIGALRM`) doesn't exist; `rq_worker.py` uses a `PortableSimpleWorker` with `TimerDeathPenalty` instead, so this works both natively on Windows and inside Linux containers.

## Frontend

```bash
cd frontend
npm install
npm run dev   # proxies /api/* to localhost:8000, see vite.config.ts
```

## End-to-end tests

Needs a live stack — real `redis`/`api`/`worker` (either `docker compose up` or `npm run dev` against a locally running backend) — since it exercises real model loading and ffmpeg, not mocks. Not wired into CI for that reason.

```bash
cd frontend
npm run test:e2e:install   # first time only, installs the Playwright browser
npm run test:e2e
```

Or `scripts/test.sh --e2e` (`scripts\test.ps1 -E2e`) once the stack is up.

`E2E_BASE_URL` (default `http://localhost:5173`) and `E2E_DATA_DIR` (default resolves to `../data`, matching `docker-compose.yml`'s default `DATA_DIR`) are configurable via env vars — see `frontend/playwright.config.ts` and `frontend/e2e/folder-batch.spec.ts`.

## This documentation site

```bash
scripts/docs.sh serve   # or scripts\docs.ps1 serve
scripts/docs.sh build   # or scripts\docs.ps1 build — outputs to site/
```

These create a throwaway `.docs-venv/` and install `docs/requirements.txt` into it automatically. `serve` runs on `http://localhost:8000`, which clashes with the `api` container's port if both are running — stop one or the other, or pass `mkdocs serve -a 127.0.0.1:8010` directly.

## Conventions

- **Commit messages** follow [Conventional Commits](https://www.conventionalcommits.org/): `feat`, `fix`, `test`, `docs`, `chore`, scoped like `feat(backend): ...`.
- **Layering**: HTTP routes stay thin; business/ML logic lives in `core/`; queue plumbing lives in `worker/`. Routes reach the worker only through `task_names.py` string references, never by importing `worker/tasks.py` directly (see [Architecture](architecture.md#why-the-api-never-imports-the-ml-stack)).
