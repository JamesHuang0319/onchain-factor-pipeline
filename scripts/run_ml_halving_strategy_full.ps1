param(
    [string[]]$Models = @("rf", "xgboost", "lgbm", "svm", "lasso", "ridge"),
    [string[]]$Tasks = @("classification", "regression"),
    [string[]]$Variants = @("onchain", "ta", "all", "boruta_onchain", "boruta_ta", "boruta_all", "univariate"),
    [double]$CostBps = 5.0,
    [string]$PredictionScope = "oos",
    [string]$Config = "configs/experiment.yaml",
    [string]$DataConfig = "configs/data.yaml",
    [switch]$ContinueOnError
)

$ErrorActionPreference = "Stop"

$validScopes = @("oos", "full_history")
if ($PredictionScope -notin $validScopes) {
    throw "PredictionScope must be one of: $($validScopes -join ', ')"
}

$validTasksByModel = @{
    "rf"      = @("classification", "regression")
    "xgboost" = @("classification", "regression")
    "lgbm"    = @("classification", "regression")
    "svm"     = @("classification", "regression")
    "lasso"   = @("regression")
    "ridge"   = @("regression")
}

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$jobs = @()
foreach ($model in $Models) {
    $modelKey = $model.ToLowerInvariant()
    if (-not $validTasksByModel.ContainsKey($modelKey)) {
        throw "Unsupported ML model: $model"
    }
    foreach ($task in $Tasks) {
        if ($task -notin $validTasksByModel[$modelKey]) {
            continue
        }
        foreach ($variant in $Variants) {
            $jobs += [PSCustomObject]@{
                Model = $modelKey
                Task = $task
                Variant = $variant
            }
        }
    }
}

$total = $jobs.Count
$batchStart = Get-Date
$completed = 0

foreach ($job in $jobs) {
    $completed += 1
    $jobStart = Get-Date
    $elapsed = $jobStart - $batchStart
    $avgSeconds = if ($completed -gt 1) { $elapsed.TotalSeconds / ($completed - 1) } else { 0 }
    $remainingJobs = $total - $completed + 1
    $remainingSeconds = [math]::Max(0, [int]($avgSeconds * $remainingJobs))
    $eta = [TimeSpan]::FromSeconds($remainingSeconds)

    Write-Host ("[{0}/{1}] halving-strategy-study {2} {3} {4}" -f $completed, $total, $job.Model, $job.Task, $job.Variant) -ForegroundColor Yellow
    Write-Host ("  elapsed={0:hh\:mm\:ss} | eta={1:hh\:mm\:ss} | cost_bps={2} | prediction_scope={3}" -f $elapsed, $eta, $CostBps, $PredictionScope)

    $cmd = @(
        "python", "-m", "src.cli", "halving-strategy-study",
        "--config", $Config,
        "--data-config", $DataConfig,
        "--model", $job.Model,
        "--task", $job.Task,
        "--dataset-variant", $job.Variant,
        "--cost-bps", "$CostBps",
        "--prediction-scope", $PredictionScope
    )

    & $cmd[0] $cmd[1..($cmd.Length - 1)]
    $exitCode = $LASTEXITCODE

    $jobElapsed = (Get-Date) - $jobStart
    if ($exitCode -eq 0) {
        Write-Host ("  status=success | job_elapsed={0:mm\:ss}" -f $jobElapsed) -ForegroundColor Green
    } else {
        Write-Host ("  status=failed({0}) | job_elapsed={1:mm\:ss}" -f $exitCode, $jobElapsed) -ForegroundColor Red
        if (-not $ContinueOnError) {
            exit $exitCode
        }
    }
}

$totalElapsed = (Get-Date) - $batchStart
Write-Host ("[done] jobs={0} | total_elapsed={1:hh\:mm\:ss}" -f $total, $totalElapsed) -ForegroundColor Cyan
