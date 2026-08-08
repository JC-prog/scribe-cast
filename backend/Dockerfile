# Single Dockerfile, two final targets (api / worker) sharing one base.
# Deliberately NOT built from an nvidia/cuda base image: ctranslate2>=4.x
# ships its CUDA/cuDNN runtime libraries as ordinary pip dependencies, so a
# plain slim image does both CPU and GPU inference. GPU access is a
# container-runtime concern (Compose device reservation, see
# docker-compose.gpu.yml) plus the host having an NVIDIA driver +
# nvidia-container-toolkit — not something baked into this image. This is
# what makes the same worker image portable across a CPU-only host and the
# CUDA host it's primarily built for.

FROM python:3.11-slim AS base
WORKDIR /app
COPY requirements-base.txt .
RUN pip install --no-cache-dir --default-timeout=180 --retries 5 -r requirements-base.txt
COPY app ./app

FROM base AS api
COPY requirements-api.txt .
RUN pip install --no-cache-dir --default-timeout=180 --retries 5 -r requirements-api.txt
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS worker
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*
COPY requirements-worker.txt .
RUN pip install --no-cache-dir --default-timeout=180 --retries 5 -r requirements-worker.txt
CMD ["python", "-m", "app.worker.rq_worker"]
