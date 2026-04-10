param(
    [string]$Config = "configs/experiment.yaml",
    [string]$DataConfig = "configs/data.yaml",
    [string]$ArtifactPrefix = "btc_predict",
    [string[]]$Models = @("tcn", "lstm", "cnn_lstm"),
    [string[]]$Tasks = @("classification", "regression"),
    [string[]]$Variants = @("boruta_onchain"),
    [double]$CostBps = 5.0,
    [switch]$RunLatest,
    [switch]$RunSummary,
    [switch]$ContinueOnError
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$logRoot = Join-Path $projectRoot "reports\batch_runs"
$null = New-Item -ItemType Directory -Force -Path $logRoot
$demoRoot = Join-Path $projectRoot "reports\demos"
$demoFiguresDir = Join-Path $demoRoot "figures"
$demoTradingDir = Join-Path $demoRoot "trading"
$demoSummariesDir = Join-Path $demoRoot "summaries"
$null = New-Item -ItemType Directory -Force -Path $demoFiguresDir, $demoTradingDir, $demoSummariesDir

function Format-Duration {
    param([double]$Seconds)
    if ($Seconds -lt 0) { $Seconds = 0 }
    $ts = [TimeSpan]::FromSeconds([math]::Round($Seconds))
    if ($ts.TotalHours -ge 1) {
        return ("{0:d2}:{1:d2}:{2:d2}" -f [int]$ts.TotalHours, $ts.Minutes, $ts.Seconds)
    }
    return ("{0:d2}:{1:d2}" -f $ts.Minutes, $ts.Seconds)
}

function Invoke-DemoStep {
    param(
        [string]$Model,
        [string]$Task,
        [string]$Variant,
        [string]$Step,
        [string[]]$ExtraArgs,
        [int]$JobIndex,
        [int]$JobTotal,
        [datetime]$BatchStart,
        [double]$AverageJobSeconds,
        [int]$PlannedSteps,
        [int]$CurrentStepIndex
    )

    $logFile = Join-Path $logRoot ("demo_{0}_{1}_{2}_{3}.log" -f $Model, $Task, $Variant, $Step)
    $stdoutFile = Join-Path $logRoot ("demo_{0}_{1}_{2}_{3}.stdout.tmp" -f $Model, $Task, $Variant, $Step)
    $stderrFile = Join-Path $logRoot ("demo_{0}_{1}_{2}_{3}.stderr.tmp" -f $Model, $Task, $Variant, $Step)
    $arguments = @(
        "-m", "src.cli", $Step,
        "--config", $Config,
        "--data-config", $DataConfig,
        "--model", $Model,
        "--task", $Task,
        "--dataset-variant", $Variant
    ) + $ExtraArgs

    $elapsedBatchSeconds = ((Get-Date) - $BatchStart).TotalSeconds
    $remainingJobs = $JobTotal - $JobIndex
    $etaSeconds = $remainingJobs * $AverageJobSeconds
    $stepLabel = "$CurrentStepIndex/$PlannedSteps"

    Write-Host ""
    Write-Host "Progress: job $JobIndex/$JobTotal | step $stepLabel" -ForegroundColor Yellow
    Write-Host "[$Step] model=$Model task=$Task variant=$Variant" -ForegroundColor Cyan
    Write-Host "elapsed=$(Format-Duration $elapsedBatchSeconds) | avg/job=$(Format-Duration $AverageJobSeconds) | eta~$(Format-Duration $etaSeconds)"
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

function Copy-DemoArtifacts {
    param(
        [string]$Model,
        [string]$Task,
        [string]$Variant
    )

    $summaryName = "{0}_summary_{1}_{2}_{3}.md" -f $ArtifactPrefix, $Model, $Task, $Variant
    $summarySrc = Join-Path $projectRoot "reports\experiments\summaries\$summaryName"
    $equitySrc = Join-Path $projectRoot ("reports\experiments\figures\{0}_{1}_{2}_{3}_equity.pdf" -f $ArtifactPrefix, $Model, $Task, $Variant)
    $drawdownSrc = Join-Path $projectRoot ("reports\experiments\figures\{0}_{1}_{2}_{3}_drawdown.pdf" -f $ArtifactPrefix, $Model, $Task, $Variant)
    $predSrc = Join-Path $projectRoot ("reports\experiments\figures\{0}_{1}_{2}_{3}_pred_vs_actual.pdf" -f $ArtifactPrefix, $Model, $Task, $Variant)
    $tradingSrc = Join-Path $projectRoot ("reports\experiments\trading\BTC_USD_{0}_trading_chart.html" -f $Model)

    foreach ($pair in @(
        @{ src = $summarySrc; dst = (Join-Path $demoSummariesDir $summaryName) },
        @{ src = $equitySrc; dst = (Join-Path $demoFiguresDir ([IO.Path]::GetFileName($equitySrc))) },
        @{ src = $drawdownSrc; dst = (Join-Path $demoFiguresDir ([IO.Path]::GetFileName($drawdownSrc))) },
        @{ src = $predSrc; dst = (Join-Path $demoFiguresDir ([IO.Path]::GetFileName($predSrc))) },
        @{ src = $tradingSrc; dst = (Join-Path $demoTradingDir ([IO.Path]::GetFileName($tradingSrc))) }
    )) {
        if (Test-Path $pair.src) {
            Copy-Item -Path $pair.src -Destination $pair.dst -Force
        }
    }
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

$plannedSteps = 2
if ($RunLatest) { $plannedSteps += 1 }
if ($plannedSteps -eq 0) { $plannedSteps = 1 }

foreach ($job in $matrix) {
    $index += 1
    $jobStart = Get-Date
    $averageJobSeconds = if ($completedJobDurations.Count -gt 0) {
        ($completedJobDurations | Measure-Object -Average).Average
    } else {
        60
    }

    Write-Host ""
    Write-Host "=== [$index/$total] $($job.Model) | $($job.Task) | $($job.Variant) ===" -ForegroundColor Yellow

    $status = "success"
    $failedStep = $null
    $stepCounter = 0

    try {
        $stepCounter += 1
        Invoke-DemoStep -Model $job.Model -Task $job.Task -Variant $job.Variant -Step "backtest" -ExtraArgs @() -JobIndex $index -JobTotal $total -BatchStart $batchStart -AverageJobSeconds $averageJobSeconds -PlannedSteps $plannedSteps -CurrentStepIndex $stepCounter

        $stepCounter += 1
        Invoke-DemoStep -Model $job.Model -Task $job.Task -Variant $job.Variant -Step "report" -ExtraArgs @() -JobIndex $index -JobTotal $total -BatchStart $batchStart -AverageJobSeconds $averageJobSeconds -PlannedSteps $plannedSteps -CurrentStepIndex $stepCounter
        Copy-DemoArtifacts -Model $job.Model -Task $job.Task -Variant $job.Variant

        if ($RunLatest) {
            $stepCounter += 1
            Invoke-DemoStep -Model $job.Model -Task $job.Task -Variant $job.Variant -Step "predict-latest" -ExtraArgs @() -JobIndex $index -JobTotal $total -BatchStart $batchStart -AverageJobSeconds $averageJobSeconds -PlannedSteps $plannedSteps -CurrentStepIndex $stepCounter
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

if ($RunSummary) {
    & python -m src.cli experiment-summary --config $Config --data-config $DataConfig --cost-bps $CostBps
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$summaryPath = Join-Path $logRoot "dl_demo_summary_$timestamp.csv"
$summary | Export-Csv -Path $summaryPath -NoTypeInformation -Encoding UTF8

Write-Host ""
Write-Host "=== Demo Summary ===" -ForegroundColor Green
Write-Host "total_elapsed=$(Format-Duration (((Get-Date) - $batchStart).TotalSeconds))"
$summary | Format-Table -AutoSize
Write-Host "summary -> $summaryPath"

if (($summary | Where-Object { $_.status -eq "failed" }).Count -gt 0 -and -not $ContinueOnError) {
    exit 1
}
