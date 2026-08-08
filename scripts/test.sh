#!/usr/bin/env bash
# Runs the backend pytest suite (hermetic, no live services needed).
# Pass --e2e to run the frontend Playwright suite instead - that one needs
# the stack already running (scripts/stack.sh up).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

if [ "${1:-}" = "--e2e" ]; then
  echo "==> Frontend e2e tests (Playwright) - requires the stack to already be running (scripts/stack.sh up)"
  cd frontend
  npm run test:e2e
  exit 0
fi

echo "==> Backend unit tests (pytest)"
cd backend
if [ -f .venv/Scripts/python.exe ]; then
  PY=.venv/Scripts/python.exe
else
  PY=.venv/bin/python
fi
"$PY" -m pytest
