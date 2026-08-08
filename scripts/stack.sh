#!/usr/bin/env bash
# Lifecycle for the Docker Compose stack.
# Usage: scripts/stack.sh {up|down|logs} [--gpu]
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

ACTION="${1:-}"
shift || true

GPU=false
for arg in "$@"; do
  [ "$arg" = "--gpu" ] && GPU=true
done

FILES=(-f docker-compose.yml)
if [ "$GPU" = true ]; then
  FILES+=(-f docker-compose.gpu.yml)
fi

case "$ACTION" in
  up)
    docker compose "${FILES[@]}" up -d --build
    echo "==> scribe-cast running at http://localhost:5173"
    ;;
  down)
    docker compose "${FILES[@]}" down
    ;;
  logs)
    docker compose "${FILES[@]}" logs -f
    ;;
  *)
    echo "Usage: $0 {up|down|logs} [--gpu]" >&2
    exit 1
    ;;
esac
