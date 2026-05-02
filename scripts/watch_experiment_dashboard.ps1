param(
    [int]$RefreshSeconds = 30,
    [switch]$Open,
    [switch]$Once
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$dashboardPath = Join-Path $projectRoot "reports\supplement_runs\dashboard.html"
$opened = $false

function Build-Dashboard {
    python scripts\build_experiment_dashboard.py --refresh-seconds $RefreshSeconds | Out-Null
}

while ($true) {
    Build-Dashboard
    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$now] dashboard refreshed -> $dashboardPath" -ForegroundColor Cyan

    if ($Open -and -not $opened) {
        Start-Process $dashboardPath
        $opened = $true
    }

    if ($Once) {
        break
    }

    Start-Sleep -Seconds $RefreshSeconds
}
