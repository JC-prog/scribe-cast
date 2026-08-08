# Builds the Docker images. Pass -Gpu on the CUDA host to also layer
# docker-compose.gpu.yml (no separate image - see docs/architecture.md).
param(
    [switch]$Gpu
)
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

if ($Gpu) {
    Write-Host "==> Building images (GPU override: worker gets the CUDA device reservation)"
    docker compose -f docker-compose.yml -f docker-compose.gpu.yml build
} else {
    Write-Host "==> Building images (CPU-safe)"
    docker compose build
}
