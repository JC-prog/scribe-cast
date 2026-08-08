# Serves or builds the MkDocs documentation site.
# Usage: scripts\docs.ps1 {serve|build}
param(
    [Parameter(Position = 0)]
    [ValidateSet("serve", "build")]
    [string]$Action = "serve"
)
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

if (-not (Test-Path ".docs-venv")) {
    python -m venv .docs-venv
}
& .\.docs-venv\Scripts\python.exe -m pip install --quiet --upgrade pip
& .\.docs-venv\Scripts\python.exe -m pip install --quiet -r docs\requirements.txt

switch ($Action) {
    "serve" { & .\.docs-venv\Scripts\python.exe -m mkdocs serve }
    "build" { & .\.docs-venv\Scripts\python.exe -m mkdocs build --strict }
}
