param(
    [string]$Config = "configs/experiment.yaml",
    [string]$DataConfig = "configs/data.yaml",
    [string[]]$Models = @("svm", "lgbm", "rf"),
    [string[]]$Tasks = @("classification", "regression"),
    [string[]]$Variants = @("onchain", "all", "boruta_onchain", "boruta_all"),
    [switch]$SkipTrain,
    [switch]$SkipBacktest,
    [switch]$SkipReport,
    [switch]$ContinueOnError
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$logRoot = Join-Path $projectRoot "reports\batch_runs"
$null = New-Item -ItemType Directory -Force -Path $logRoot

function Format-Duration {
    param([double]$Seconds)
    if ($Seconds -lt 0) { $Seconds = 0 }
    $ts = [TimeSpan]::FromSeconds([math]::Round($Seconds))
    if ($ts.TotalHours -ge 1) {
        return ("{0:d2}:{1:d2}:{2:d2}" -f [int]$ts.TotalHours, $ts.Minutes, $ts.Seconds)
    }
    return ("{0:d2}:{1:d2}" -f $ts.Minutes, $ts.Seconds)
}

function Invoke-ExperimentStep {
    param(
        [string]$Model,
        [string]$Task,
        [string]$Variant,
        [string]$Step,
        [int]$JobIndex,
        [int]$JobTotal,
        [datetime]$BatchStart,
        [double]$AverageJobSeconds,
        [int]$PlannedSteps,
        [int]$CurrentStepIndex
    )

    $logFile = Join-Path $logRoot ("{0}_{1}_{2}_{3}.log" -f $Model, $Task, $Variant, $Step)
    $stdoutFile = Join-Path $logRoot ("{0}_{1}_{2}_{3}.stdout.tmp" -f $Model, $Task, $Variant, $Step)
    $stderrFile = Join-Path $logRoot ("{0}_{1}_{2}_{3}.stderr.tmp" -f $Model, $Task, $Variant, $Step)
    $arguments = @(
        "-m", "src.cli", $Step,
        "--config", $Config,
        "--data-config", $DataConfig,
        "--model", $Model,
        "--task", $Task,
        "--dataset-variant", $Variant
    )

    $elapsedBatchSeconds = ((Get-Date) - $BatchStart).TotalSeconds
    $remainingJobs = $JobTotal - $JobIndex
    $etaSeconds = $remainingJobs * $AverageJobSeconds
    $stepLabel = "$CurrentStepIndex/$PlannedSteps"

    Write-Host ""
    Write-Host "Progress: job $JobIndex/$JobTotal | step $stepLabel" -ForegroundColor Yellow
    Write-Host "[$Step] model=$Model task=$Task variant=$Variant" -ForegroundColor Cyan
    $elapsedText = Format-Duration $elapsedBatchSeconds
    $avgText = Format-Duration $AverageJobSeconds
    $etaText = Format-Duration $etaSeconds
    Write-Host "elapsed=$elapsedText | avg/job=$avgText | eta~$etaText"
    Write-Host "log -> $logFile"

    if (Test-Path $stdoutFile) { Remove-Item $stdoutFile -Force }
    if (Test-Path $stderrFile) { Remove-Item $stderrFile -Force }

    $proc = Start-Process `
        -FilePath "python" `
        -ArgumentList $arguments `
        -WorkingDirectory $projectRoot `
        -NoNewWindow `
        -Wait `
        -PassThru `
        -RedirectStandardOutput $stdoutFile `
        -RedirectStandardError $stderrFile

    $combined = @()
    if (Test-Path $stdoutFile) { $combined += Get-Content $stdoutFile }
    if (Test-Path $stderrFile) { $combined += Get-Content $stderrFile }
    $combined | Set-Content -Path $logFile -Encoding UTF8
    if ($combined.Count -gt 0) {
        $combined | Write-Host
    }

    if ($proc.ExitCode -ne 0) {
        throw "Step failed: $Step model=$Model task=$Task variant=$Variant"
    }

    if (Test-Path $stdoutFile) { Remove-Item $stdoutFile -Force }
    if (Test-Path $stderrFile) { Remove-Item $stderrFile -Force }
}

$matrix = foreach ($model in $Models) {
    foreach ($task in $Tasks) {
        foreach ($variant in $Variants) {
            [pscustomobject]@{
                Model = $model
                Task = $task
                Variant = $variant
            }
        }
    }
}

$summary = New-Object System.Collections.Generic.List[object]
$total = $matrix.Count
$index = 0
$batchStart = Get-Date
$completedJobDurations = New-Object System.Collections.Generic.List[double]

$plannedSteps = 0
if (-not $SkipTrain) { $plannedSteps += 1 }
if (-not $SkipBacktest) { $plannedSteps += 1 }
if (-not $SkipReport) { $plannedSteps += 1 }
if ($plannedSteps -eq 0) { $plannedSteps = 1 }

foreach ($job in $matrix) {
    $index += 1
    $jobStart = Get-Date
    if ($completedJobDurations.Count -gt 0) {
        $averageJobSeconds = ($completedJobDurations | Measure-Object -Average).Average
    }
    else {
        $averageJobSeconds = 120
    }

    Write-Host ""
    Write-Host "=== [$index/$total] $($job.Model) | $($job.Task) | $($job.Variant) ===" -ForegroundColor Yellow

    $status = "success"
    $failedStep = $null
    $stepCounter = 0

    try {
        if (-not $SkipTrain) {
            $stepCounter += 1
            Invoke-ExperimentStep -Model $job.Model -Task $job.Task -Variant $job.Variant -Step "train" -JobIndex $index -JobTotal $total -BatchStart $batchStart -AverageJobSeconds $averageJobSeconds -PlannedSteps $plannedSteps -CurrentStepIndex $stepCounter
        }
        if (-not $SkipBacktest) {
            $stepCounter += 1
            Invoke-ExperimentStep -Model $job.Model -Task $job.Task -Variant $job.Variant -Step "backtest" -JobIndex $index -JobTotal $total -BatchStart $batchStart -AverageJobSeconds $averageJobSeconds -PlannedSteps $plannedSteps -CurrentStepIndex $stepCounter
        }
        if (-not $SkipReport) {
            $stepCounter += 1
            Invoke-ExperimentStep -Model $job.Model -Task $job.Task -Variant $job.Variant -Step "report" -JobIndex $index -JobTotal $total -BatchStart $batchStart -AverageJobSeconds $averageJobSeconds -PlannedSteps $plannedSteps -CurrentStepIndex $stepCounter
        }
    }
    catch {
        $status = "failed"
        $failedStep = $_.Exception.Message
        Write-Host $failedStep -ForegroundColor Red
        if (-not $ContinueOnError) {
            $summary.Add([pscustomobject]@{
                model = $job.Model
                task = $job.Task
                variant = $job.Variant
                status = $status
                error = $failedStep
            })
            break
        }
    }

    $summary.Add([pscustomobject]@{
        model = $job.Model
        task = $job.Task
        variant = $job.Variant
        status = $status
        error = $failedStep
    })

    $jobElapsedSeconds = ((Get-Date) - $jobStart).TotalSeconds
    $completedJobDurations.Add($jobElapsedSeconds)
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$summaryPath = Join-Path $logRoot "summary_$timestamp.csv"
$summary | Export-Csv -Path $summaryPath -NoTypeInformation -Encoding UTF8

Write-Host ""
Write-Host "=== Batch Summary ===" -ForegroundColor Green
$totalElapsedSeconds = ((Get-Date) - $batchStart).TotalSeconds
Write-Host "total_elapsed=$(Format-Duration $totalElapsedSeconds)"
$summary | Format-Table -AutoSize
Write-Host "summary -> $summaryPath"

if (($summary | Where-Object { $_.status -eq "failed" }).Count -gt 0 -and -not $ContinueOnError) {
    exit 1
}
