# Getting Started

## Prerequisites

- Docker Desktop (with Compose v2)
- **GPU host only:** an NVIDIA driver + [nvidia-container-toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) installed on the host

## Setup

```bash
cp .env.example .env
```

Edit `.env` and set `DATA_DIR` to the folder you want available for folder-batch jobs (see [Usage](usage.md#folder-batch) for how that path gets mapped into the container).

`scripts/setup-dev.sh` (or `scripts\setup-dev.ps1`) does the `.env` copy plus creates `data/`/`logs/` and installs backend and frontend dependencies for local (non-Docker) development — see [Development](development.md). For just running the app via Docker, the manual `cp` above plus the compose commands below are all you need.

## Running it

=== "CPU-only host"

    ```bash
    scripts/stack.sh up
    # or: scripts\stack.ps1 up
    # or directly: docker compose up -d --build
    ```

=== "CUDA host"

    ```bash
    scripts/stack.sh up --gpu
    # or: scripts\stack.ps1 up -Gpu
    # or directly: docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build
    ```

Then open [http://localhost:5173](http://localhost:5173). Bring it down with `scripts/stack.sh down` (add `--gpu`/`-Gpu` to match how you brought it up — it only affects which compose files are targeted, not what's running).

!!! note "Same image, different compose file"
    There's only one worker Docker image. `docker-compose.gpu.yml` is a small override that adds a GPU device reservation and sets `DEVICE=cuda` — it doesn't rebuild anything differently. See [Architecture → CPU/GPU portability](architecture.md#cpugpu-portability) for why this works.

## Logs

Structured JSON logs land in `./logs/` on the host (bind-mounted from both containers):

- `api.log` — API request-level events (uploads enqueued, batch jobs enqueued, 4xx/5xx errors)
- `worker.log` — model loads, audio extraction, transcription, per-job timings
- `errors.log` — ERROR-level events from either component, for quick cross-component grepping

## Configuration reference

| Variable | Default | Meaning |
|---|---|---|
| `DATA_DIR` | `./data` | Host folder bind-mounted to `/data` in the api/worker containers, for folder-batch jobs |
| `DEVICE` | `auto` | `auto` \| `cuda` \| `cpu`. `docker-compose.gpu.yml` overrides this to `cuda`. `auto`/`cuda` fall back to CPU with a logged warning if no GPU is actually available |
| `COMPUTE_TYPE` | *(unset)* | Overrides the device-appropriate default (`float16` on GPU, `int8` on CPU) — e.g. `int8_float16` |

## Next

- [Usage](usage.md) — walk through uploading a video and running a folder batch
- [Development](development.md) — running this outside Docker, running the test suites
