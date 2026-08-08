#!/usr/bin/env bash
# Serves or builds the MkDocs documentation site.
# Usage: scripts/docs.sh {serve|build}
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

ACTION="${1:-serve}"

if [ ! -d .docs-venv ]; then
  python -m venv .docs-venv
fi
if [ -f .docs-venv/Scripts/python.exe ]; then
  PY=.docs-venv/Scripts/python.exe
else
  PY=.docs-venv/bin/python
fi
"$PY" -m pip install --quiet --upgrade pip
"$PY" -m pip install --quiet -r docs/requirements.txt

case "$ACTION" in
  serve) "$PY" -m mkdocs serve ;;
  build) "$PY" -m mkdocs build --strict ;;
  *)
    echo "Usage: $0 {serve|build}" >&2
    exit 1
    ;;
esac
