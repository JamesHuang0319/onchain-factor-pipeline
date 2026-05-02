param(
    [int]$Port = 8765,
    [int]$RefreshSeconds = 5
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$dashboardRoot = Join-Path $projectRoot "reports\supplement_runs"
$watcherScript = Join-Path $projectRoot "scripts\watch_experiment_dashboard.ps1"
$url = "http://127.0.0.1:$Port/dashboard.html"

Set-Location $projectRoot

python scripts\build_experiment_dashboard.py --refresh-seconds $RefreshSeconds | Out-Null

$existing = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $existing) {
    Start-Process -FilePath python `
        -WindowStyle Hidden `
        -WorkingDirectory $dashboardRoot `
        -ArgumentList @("-m", "http.server", "$Port", "--bind", "127.0.0.1")
    Start-Sleep -Seconds 2
}

$watcherArgs = "-NoProfile -ExecutionPolicy Bypass -File `"$watcherScript`" -RefreshSeconds $RefreshSeconds"
Start-Process -FilePath powershell.exe -WindowStyle Hidden -ArgumentList $watcherArgs

Start-Process $url
Write-Host "Live dashboard -> $url" -ForegroundColor Cyan
Write-Host "HTML rebuild interval: $RefreshSeconds seconds; live run-state polling: 1 second." -ForegroundColor DarkCyan
