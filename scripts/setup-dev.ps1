# Bootstraps a local dev environment: .env, backend venv + deps, frontend deps.
# Safe to re-run.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

Write-Host "==> scribe-cast dev environment setup"

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example - edit DATA_DIR if you want folder-batch jobs to see a different host folder."
} else {
    Write-Host ".env already exists, leaving it as-is."
}

New-Item -ItemType Directory -Force -Path "data" | Out-Null
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
if (-not (Test-Path "logs\.gitkeep")) {
    New-Item -ItemType File "logs\.gitkeep" | Out-Null
}

Write-Host "==> Backend: creating venv and installing dependencies"
Set-Location backend
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
& .\.venv\Scripts\python.exe -m pip install --quiet --upgrade pip
& .\.venv\Scripts\python.exe -m pip install --quiet -r requirements-dev.txt
Set-Location ..

Write-Host "==> Frontend: installing dependencies"
Set-Location frontend
npm install
Set-Location ..

Write-Host ""
Write-Host "==> Done. Next steps:"
Write-Host "  - Backend tests:  scripts\test.ps1"
Write-Host "  - Frontend dev:   cd frontend; npm run dev"
Write-Host "  - Full stack:     scripts\stack.ps1 up            (add -Gpu on the CUDA host)"
Write-Host "  - Docs site:      scripts\docs.ps1 serve"
