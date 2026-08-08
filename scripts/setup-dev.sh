#!/usr/bin/env bash
# Bootstraps a local dev environment: .env, backend venv + deps, frontend deps.
# Safe to re-run.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

echo "==> scribe-cast dev environment setup"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example - edit DATA_DIR if you want folder-batch jobs to see a different host folder."
else
  echo ".env already exists, leaving it as-is."
fi

mkdir -p data logs
touch logs/.gitkeep

echo "==> Backend: creating venv and installing dependencies"
cd backend
if [ ! -d .venv ]; then
  python -m venv .venv
fi
if [ -f .venv/Scripts/python.exe ]; then
  PY=.venv/Scripts/python.exe   # Windows
else
  PY=.venv/bin/python           # macOS/Linux
fi
"$PY" -m pip install --quiet --upgrade pip
"$PY" -m pip install --quiet -r requirements-dev.txt
cd ..

echo "==> Frontend: installing dependencies"
cd frontend
npm install
cd ..

cat <<'EOF'

==> Done. Next steps:
  - Backend tests:  scripts/test.sh
  - Frontend dev:   cd frontend && npm run dev
  - Full stack:     scripts/stack.sh up            (add --gpu on the CUDA host)
  - Docs site:      scripts/docs.sh serve
EOF
