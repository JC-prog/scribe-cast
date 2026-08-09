# Single Dockerfile, two final targets (api / worker) sharing one base.
# Deliberately NOT built from an nvidia/cuda base image: the worker's
# requirements-worker.txt pins nvidia-cublas-cu12/nvidia-cudnn-cu12
# (ctranslate2 itself does not declare them as dependencies), so a plain
# slim image can still do CUDA inference. Those pip-installed .so files
# only land in site-packages, not on the default dynamic linker search
# path, so LD_LIBRARY_PATH below is required, not optional; without it,
# ctranslate2 fails at the first real inference call (not at model load -
# model construction never touches cuBLAS) with "Library libcublas.so.12
# is not found or cannot be loaded". GPU access itself is a
# container-runtime concern (Compose device reservation, see
# docker-compose.gpu.yml) plus the host having an NVIDIA driver +
# nvidia-container-toolkit, not something baked into this image. This is
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
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS worker
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*
COPY requirements-worker.txt .
RUN pip install --no-cache-dir --default-timeout=180 --retries 5 -r requirements-worker.txt
ENV LD_LIBRARY_PATH="/usr/local/lib/python3.11/site-packages/nvidia/cublas/lib:/usr/local/lib/python3.11/site-packages/nvidia/cudnn/lib:/usr/local/lib/python3.11/site-packages/nvidia/cuda_nvrtc/lib"
CMD ["python", "-m", "app.worker.rq_worker"]
