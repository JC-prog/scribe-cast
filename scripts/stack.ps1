# Lifecycle for the Docker Compose stack.
# Usage: scripts\stack.ps1 up [-Gpu]  |  down [-Gpu]  |  logs [-Gpu]
param(
    [Parameter(Position = 0)]
    [ValidateSet("up", "down", "logs")]
    [string]$Action = "up",
    [switch]$Gpu
)
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

$env:VERSION = (Get-Content VERSION -Raw).Trim()

$files = @("-f", "docker-compose.yml")
if ($Gpu) { $files += @("-f", "docker-compose.gpu.yml") }

switch ($Action) {
    "up" {
        docker compose @files up -d --build
        Write-Host "==> scribe-cast running at http://localhost:5173"
    }
    "down" {
        docker compose @files down
    }
    "logs" {
        docker compose @files logs -f
    }
}
