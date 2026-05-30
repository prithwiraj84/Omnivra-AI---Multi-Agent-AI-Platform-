<#
.SYNOPSIS
    One-time local setup for Omnivra AI Company OS (no Docker — venv + npm only).
.DESCRIPTION
    Creates the backend Python venv and installs requirements, installs frontend
    npm dependencies, and seeds .env files from their .env.example templates.
.EXAMPLE
    pwsh ./scripts/setup.ps1
#>
[CmdletBinding()]
param(
    [switch]$SkipFrontend,
    [switch]$SkipBackend
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
Write-Host "Omnivra setup — repo root: $root" -ForegroundColor Cyan

function Copy-EnvExample([string]$dir) {
    $example = Join-Path $dir '.env.example'
    $target = Join-Path $dir '.env'
    if ((Test-Path $example) -and -not (Test-Path $target)) {
        Copy-Item $example $target
        Write-Host "  created $target (fill in your keys)" -ForegroundColor Yellow
    }
}

# --- Backend ---------------------------------------------------------------
if (-not $SkipBackend) {
    Write-Host "`n[backend] Python venv + requirements" -ForegroundColor Green
    $backend = Join-Path $root 'backend'
    $venv = Join-Path $backend '.venv'
    if (-not (Test-Path $venv)) { python -m venv $venv }
    $py = Join-Path $venv 'Scripts/python.exe'
    & $py -m pip install --upgrade pip
    & $py -m pip install -r (Join-Path $backend 'requirements.txt')
    Copy-EnvExample $backend
    Write-Host "  backend ready." -ForegroundColor Green
}

# --- Frontend --------------------------------------------------------------
if (-not $SkipFrontend) {
    Write-Host "`n[frontend] npm install" -ForegroundColor Green
    $frontend = Join-Path $root 'frontend'
    Push-Location $frontend
    try { npm install } finally { Pop-Location }
    Copy-EnvExample $frontend
    Write-Host "  frontend ready." -ForegroundColor Green
}

Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "  1. Fill backend/.env and frontend/.env with your provider + Supabase keys."
Write-Host "  2. Create a Supabase project and run supabase/schema.sql, rls.sql, seed.sql (see docs/SUPABASE_INTEGRATION.md)."
Write-Host "  3. Start everything:  pwsh ./scripts/dev.ps1"
