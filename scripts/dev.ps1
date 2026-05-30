<#
.SYNOPSIS
    Start the Omnivra backend (FastAPI/uvicorn :8000) and frontend (Vite :5173)
    in two new PowerShell windows.
.EXAMPLE
    pwsh ./scripts/dev.ps1
#>
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$backend = Join-Path $root 'backend'
$frontend = Join-Path $root 'frontend'
$py = Join-Path $backend '.venv/Scripts/python.exe'

if (-not (Test-Path $py)) {
    Write-Error "Backend venv not found. Run ./scripts/setup.ps1 first."
}

Write-Host "Starting backend (uvicorn) on http://localhost:8000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList @(
    '-NoExit', '-Command',
    "Set-Location '$backend'; & '$py' -m uvicorn app.main:app --reload --port 8000"
)

Write-Host "Starting frontend (vite) on http://localhost:5173 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList @(
    '-NoExit', '-Command',
    "Set-Location '$frontend'; npm run dev"
)

Write-Host "`nBoth dev servers launching in new windows." -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:5173   (proxies /api and /ws to :8000)"
Write-Host "  Backend:  http://localhost:8000/docs"
