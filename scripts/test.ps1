# Runs the backend pytest suite (hermetic, no live services needed).
# Pass -E2e to run the frontend Playwright suite instead - that one needs
# the stack already running (scripts\stack.ps1 up).
param(
    [switch]$E2e
)
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

if ($E2e) {
    Write-Host "==> Frontend e2e tests (Playwright) - requires the stack to already be running (scripts\stack.ps1 up)"
    Set-Location frontend
    npm run test:e2e
    exit 0
}

Write-Host "==> Backend unit tests (pytest)"
Set-Location backend
& .\.venv\Scripts\python.exe -m pytest
