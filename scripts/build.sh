#!/usr/bin/env bash
# Builds the Docker images. Pass --gpu on the CUDA host to also layer
# docker-compose.gpu.yml (no separate image - see docs/architecture.md).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

export VERSION="$(cat VERSION)"

if [ "${1:-}" = "--gpu" ]; then
  echo "==> Building images (GPU override: worker gets the CUDA device reservation)"
  docker compose -f docker-compose.yml -f docker-compose.gpu.yml build
else
  echo "==> Building images (CPU-safe)"
  docker compose build
fi
