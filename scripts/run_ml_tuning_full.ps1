param(
    [string[]]$Models = @("rf", "xgboost", "lgbm"),
    [string[]]$Tasks = @("classification", "regression"),
    [string[]]$Variants = @("onchain", "ta", "all", "boruta_onchain", "boruta_ta", "boruta_all", "univariate"),
    [int]$Trials = 20,
    [string]$Config = "configs/experiment.yaml",
    [string]$DataConfig = "configs/data.yaml",
    [switch]$ContinueOnError
)

$ErrorActionPreference = "Stop"

$jobs = @()
foreach ($model in $Models) {
    foreach ($task in $Tasks) {
        foreach ($variant in $Variants) {
            $jobs += [PSCustomObject]@{
                Model = $model
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

    Write-Host ("[{0}/{1}] tune {2} {3} {4}" -f $completed, $total, $job.Model, $job.Task, $job.Variant)
    Write-Host ("  elapsed={0:hh\:mm\:ss} | eta={1:hh\:mm\:ss} | trials={2}" -f $elapsed, $eta, $Trials)

    $cmd = @(
        "python", "-m", "src.cli", "tune",
        "--config", $Config,
        "--data-config", $DataConfig,
        "--model", $job.Model,
        "--task", $job.Task,
        "--dataset-variant", $job.Variant,
        "--trials", "$Trials"
    )

    & $cmd[0] $cmd[1..($cmd.Length - 1)]
    $exitCode = $LASTEXITCODE

    $jobElapsed = (Get-Date) - $jobStart
    if ($exitCode -eq 0) {
        Write-Host ("  status=success | job_elapsed={0:mm\:ss}" -f $jobElapsed)
    } else {
        Write-Host ("  status=failed({0}) | job_elapsed={1:mm\:ss}" -f $exitCode, $jobElapsed)
        if (-not $ContinueOnError) {
            exit $exitCode
        }
    }
}

$totalElapsed = (Get-Date) - $batchStart
Write-Host ("[done] jobs={0} | total_elapsed={1:hh\:mm\:ss}" -f $total, $totalElapsed)
