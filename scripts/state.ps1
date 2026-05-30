<#
.SYNOPSIS
    Print Omnivra's current build state: phase, progress, and latest checkpoint.
.DESCRIPTION
    Reads the durable control-plane mirror at workspace/.state/project_state.json
    (falling back to docs/PROJECT_STATE.md) so you can see where generation stands
    and resume from the last checkpoint if interrupted.
.EXAMPLE
    pwsh ./scripts/state.ps1
#>
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$stateJson = Join-Path $root 'workspace/.state/project_state.json'
$checkpoints = Join-Path $root 'workspace/.state/checkpoints'

Write-Host "OMNIVRA — build state" -ForegroundColor Cyan
if (Test-Path $stateJson) {
    $s = Get-Content -Raw $stateJson | ConvertFrom-Json
    Write-Host ("  Project : {0}" -f $s.project)
    Write-Host ("  Phase   : {0} — {1}" -f $s.current_phase, $s.current_phase_title)
    Write-Host ("  Status  : {0}" -f $s.status)
    Write-Host ("  Updated : {0}" -f $s.updated_at)
    if ($s.last_checkpoint) { Write-Host ("  Last cp : {0}" -f $s.last_checkpoint) }
} else {
    Write-Host "  No runtime state mirror yet. See docs/PROJECT_STATE.md." -ForegroundColor Yellow
}

if (Test-Path $checkpoints) {
    $cps = Get-ChildItem $checkpoints -Filter 'cp-*.json' -ErrorAction SilentlyContinue | Sort-Object Name
    Write-Host ("`n  Checkpoints ({0}):" -f $cps.Count)
    foreach ($cp in $cps) { Write-Host ("    - {0}" -f $cp.BaseName) }
}
