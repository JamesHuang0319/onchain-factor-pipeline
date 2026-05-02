param(
    [string]$Config = "configs/experiment.yaml",
    [string]$DataConfig = "configs/data.yaml",
    [string[]]$Models = @("svm", "rf", "lgbm", "xgboost", "lasso", "ridge", "lstm", "cnn_lstm", "gru", "tcn"),
    [string[]]$Tasks = @("classification", "regression"),
    [string[]]$Variants = @("onchain", "ta", "all", "boruta_onchain", "boruta_ta", "boruta_all", "univariate"),
    [switch]$RunExisting,
    [switch]$KeepBest,
    [switch]$SkipBacktest,
    [switch]$SkipReport,
    [switch]$ContinueOnError,
    [switch]$DryRun,
    [int]$HeartbeatSeconds = 5
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$runId = Get-Date -Format "yyyyMMdd_HHmmss"
$runRoot = Join-Path $projectRoot "reports\supplement_runs\$runId"
$logRoot = Join-Path $runRoot "logs"
$backupRoot = Join-Path $runRoot "backup"
$statePath = Join-Path $runRoot "run_state.json"
$latestStatePath = Join-Path $projectRoot "reports\supplement_runs\latest_run_state.json"
$null = New-Item -ItemType Directory -Force -Path $logRoot
$null = New-Item -ItemType Directory -Force -Path $backupRoot

$validTasksByModel = @{
    "svm"      = @("classification", "regression")
    "rf"       = @("classification", "regression")
    "lgbm"     = @("classification", "regression")
    "xgboost"  = @("classification", "regression")
    "lasso"    = @("regression")
    "ridge"    = @("regression")
    "lstm"     = @("classification", "regression")
    "cnn_lstm" = @("classification", "regression")
    "gru"      = @("classification", "regression")
    "tcn"      = @("classification", "regression")
}

function Get-ArtifactPrefix {
    param([string]$ConfigPath)
    if (-not (Test-Path $ConfigPath)) {
        return "btc_predict"
    }
    $match = Select-String -Path $ConfigPath -Pattern '^\s*artifact_prefix:\s*(\S+)\s*$' | Select-Object -First 1
    if ($match -and $match.Matches.Count -gt 0) {
        return $match.Matches[0].Groups[1].Value.Trim('"').Trim("'")
    }
    return "btc_predict"
}

function Format-Duration {
    param([double]$Seconds)
    if ($Seconds -lt 0) { $Seconds = 0 }
    $ts = [TimeSpan]::FromSeconds([math]::Round($Seconds))
    if ($ts.TotalHours -ge 1) {
        return ("{0:d2}:{1:d2}:{2:d2}" -f [int]$ts.TotalHours, $ts.Minutes, $ts.Seconds)
    }
    return ("{0:d2}:{1:d2}" -f $ts.Minutes, $ts.Seconds)
}

function Save-JsonAtomic {
    param(
        [string]$Path,
        [string]$Json
    )
    $dir = Split-Path -Parent $Path
    $name = Split-Path -Leaf $Path
    $tmp = Join-Path $dir (".{0}.{1}.tmp" -f $name, $PID)
    for ($attempt = 1; $attempt -le 10; $attempt += 1) {
        try {
            $Json | Set-Content -Path $tmp -Encoding UTF8
            Move-Item -LiteralPath $tmp -Destination $Path -Force
            return
        }
        catch {
            Start-Sleep -Milliseconds (120 * $attempt)
        }
    }
    $Json | Set-Content -Path $Path -Encoding UTF8
}

function Write-RunState {
    param(
        [string]$Status,
        [int]$Processed,
        [int]$Total,
        [object]$Current,
        [datetime]$BatchStart,
        [System.Collections.Generic.List[object]]$Summary,
        [string]$Message = ""
    )

    $elapsedSeconds = ((Get-Date) - $BatchStart).TotalSeconds
    $avgSeconds = $null
    $etaSeconds = $null
    $estimatedFinish = $null
    if ($script:completedJobDurations -and $script:completedJobDurations.Count -gt 0) {
        $avgSeconds = ($script:completedJobDurations | Measure-Object -Average).Average
        $remaining = [math]::Max(0, $Total - $Processed)
        $etaSeconds = $remaining * $avgSeconds
        $estimatedFinish = (Get-Date).AddSeconds($etaSeconds).ToString("yyyy-MM-dd HH:mm:ss")
    }

    $counts = [ordered]@{}
    foreach ($group in ($Summary | Group-Object status)) {
        $counts[$group.Name] = $group.Count
    }

    $state = [ordered]@{
        run_id = $runId
        status = $Status
        started_at = $BatchStart.ToString("yyyy-MM-dd HH:mm:ss")
        updated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        total = $Total
        processed = $Processed
        elapsed_seconds = [math]::Round($elapsedSeconds, 1)
        avg_seconds_per_job = if ($avgSeconds -ne $null) { [math]::Round($avgSeconds, 1) } else { $null }
        eta_seconds = if ($etaSeconds -ne $null) { [math]::Round($etaSeconds, 1) } else { $null }
        estimated_finish_at = $estimatedFinish
        current = $Current
        counts = $counts
        message = $Message
        run_root = $runRoot
    }

    $json = $state | ConvertTo-Json -Depth 6
    Save-JsonAtomic -Path $statePath -Json $json
    Save-JsonAtomic -Path $latestStatePath -Json $json
}

function Get-ComboPaths {
    param(
        [string]$Prefix,
        [string]$Model,
        [string]$Task,
        [string]$Variant
    )
    $stem = "${Prefix}_${Model}_${Task}_${Variant}"
    return @{
        Preds       = Join-Path $projectRoot "data\features\${stem}_preds.parquet"
        Metrics     = Join-Path $projectRoot "data\features\${stem}_metrics.json"
        Backtest    = Join-Path $projectRoot "data\features\${stem}_backtest_sensitivity.csv"
        Equity      = Join-Path $projectRoot "data\features\${stem}_equity.parquet"
        ModelPkl    = Join-Path $projectRoot "models_saved\${stem}.pkl"
        ModelMeta   = Join-Path $projectRoot "models_saved\${stem}_meta.json"
        Summary     = Join-Path $projectRoot "reports\experiments\summaries\${Prefix}_summary_${Model}_${Task}_${Variant}.md"
        FigureGlob  = Join-Path $projectRoot "reports\experiments\figures\${stem}_*.pdf"
        TradingGlob = Join-Path $projectRoot "reports\experiments\trading\${stem}_*"
    }
}

function Test-ComboComplete {
    param(
        [hashtable]$Paths,
        [bool]$NeedBacktest,
        [bool]$NeedReport
    )
    if (-not (Test-Path $Paths.Preds)) { return $false }
    if (-not (Test-Path $Paths.Metrics)) { return $false }
    if ($NeedBacktest) {
        if (-not (Test-Path $Paths.Backtest)) { return $false }
        if (-not (Test-Path $Paths.Equity)) { return $false }
    }
    if ($NeedReport) {
        if (-not (Test-Path $Paths.Summary)) { return $false }
    }
    return $true
}

function Get-MissingSteps {
    param(
        [hashtable]$Paths,
        [bool]$NeedBacktest,
        [bool]$NeedReport,
        [bool]$ForceAll
    )
    if ($ForceAll) {
        $steps = @("train")
        if ($NeedBacktest) { $steps += "backtest" }
        if ($NeedReport) { $steps += "report" }
        return $steps
    }

    $hasTrain = (Test-Path $Paths.Preds) -and (Test-Path $Paths.Metrics)
    $hasBacktest = (Test-Path $Paths.Backtest) -and (Test-Path $Paths.Equity)
    $hasReport = Test-Path $Paths.Summary

    $missing = @()
    if (-not $hasTrain) {
        $missing += "train"
        if ($NeedBacktest) {
            $missing += "backtest"
        }
        if ($NeedReport) {
            $missing += "report"
        }
        return $missing
    }

    if ($NeedBacktest -and -not $hasBacktest) {
        $missing += "backtest"
    }
    if ($NeedReport -and -not $hasReport) {
        $missing += "report"
    }
    return $missing
}

function Get-PrimaryMetric {
    param(
        [string]$MetricsPath,
        [string]$Model,
        [string]$Task
    )
    if (-not (Test-Path $MetricsPath)) {
        return $null
    }
    $json = Get-Content -Raw -Path $MetricsPath | ConvertFrom-Json
    if ($Task -eq "classification") {
        $key = "${Model}_classification_oos_f1"
        $value = $json.PSObject.Properties[$key].Value
        return [pscustomobject]@{ Metric = "F1"; Value = [double]$value; Score = [double]$value }
    }
    $rmseKey = "${Model}_regression_oos_rmse"
    $value = $json.PSObject.Properties[$rmseKey].Value
    return [pscustomobject]@{ Metric = "RMSE"; Value = [double]$value; Score = -1.0 * [double]$value }
}

function Copy-RelativeFile {
    param(
        [string]$SourcePath,
        [string]$DestinationRoot
    )
    $sourceFull = [System.IO.Path]::GetFullPath($SourcePath)
    if (-not $sourceFull.StartsWith($projectRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to copy path outside project root: $sourceFull"
    }
    $relative = $sourceFull.Substring($projectRoot.Length).TrimStart('\', '/')
    $dest = Join-Path $DestinationRoot $relative
    $destDir = Split-Path -Parent $dest
    $null = New-Item -ItemType Directory -Force -Path $destDir
    Copy-Item -LiteralPath $sourceFull -Destination $dest -Force
}

function Backup-ComboArtifacts {
    param(
        [hashtable]$Paths,
        [string]$DestinationRoot
    )
    $files = New-Object System.Collections.Generic.List[string]
    foreach ($name in @("Preds", "Metrics", "Backtest", "Equity", "ModelPkl", "ModelMeta", "Summary")) {
        $path = $Paths[$name]
        if ($path -and (Test-Path $path)) {
            $files.Add($path)
        }
    }
    foreach ($path in Get-ChildItem -Path $Paths.FigureGlob -File -ErrorAction SilentlyContinue) {
        $files.Add($path.FullName)
    }
    foreach ($path in Get-ChildItem -Path $Paths.TradingGlob -File -ErrorAction SilentlyContinue) {
        $files.Add($path.FullName)
    }
    foreach ($file in $files) {
        Copy-RelativeFile -SourcePath $file -DestinationRoot $DestinationRoot
    }
    return $files.Count
}

function Restore-ComboArtifacts {
    param([string]$SourceRoot)
    if (-not (Test-Path $SourceRoot)) {
        return
    }
    $sourceFull = [System.IO.Path]::GetFullPath($SourceRoot)
    if (-not $sourceFull.StartsWith($backupRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to restore from unexpected path: $sourceFull"
    }
    foreach ($file in Get-ChildItem -Path $SourceRoot -Recurse -File) {
        $relative = $file.FullName.Substring($sourceFull.Length).TrimStart('\', '/')
        $dest = Join-Path $projectRoot $relative
        $destDir = Split-Path -Parent $dest
        $null = New-Item -ItemType Directory -Force -Path $destDir
        Copy-Item -LiteralPath $file.FullName -Destination $dest -Force
    }
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
        [System.Collections.Generic.List[object]]$Summary
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

    Write-Host ""
    Write-Host "Progress: job $JobIndex/$JobTotal | $Step | $Model | $Task | $Variant" -ForegroundColor Cyan
    Write-Host "elapsed=$(Format-Duration (((Get-Date) - $BatchStart).TotalSeconds))"
    Write-Host "log -> $logFile"

    if (Test-Path $stdoutFile) { Remove-Item $stdoutFile -Force }
    if (Test-Path $stderrFile) { Remove-Item $stderrFile -Force }

    $stepStart = Get-Date
    $proc = Start-Process `
        -FilePath "python" `
        -ArgumentList $arguments `
        -WorkingDirectory $projectRoot `
        -NoNewWindow `
        -PassThru `
        -RedirectStandardOutput $stdoutFile `
        -RedirectStandardError $stderrFile

    while (-not $proc.HasExited) {
        $currentState = [ordered]@{
            model = $Model
            task = $Task
            variant = $Variant
            steps = $Step
            active_step = $Step
            step_started_at = $stepStart.ToString("yyyy-MM-dd HH:mm:ss")
            step_elapsed_seconds = [math]::Round(((Get-Date) - $stepStart).TotalSeconds, 1)
        }
        Write-RunState -Status "running" -Processed ($JobIndex - 1) -Total $JobTotal -Current $currentState -BatchStart $BatchStart -Summary $Summary -Message "running $Step"
        Start-Sleep -Seconds ([math]::Max(1, $HeartbeatSeconds))
    }

    $proc.WaitForExit()

    $combined = @()
    if (Test-Path $stdoutFile) { $combined += Get-Content $stdoutFile }
    if (Test-Path $stderrFile) { $combined += Get-Content $stderrFile }
    $combined | Set-Content -Path $logFile -Encoding UTF8

    $proc.Refresh()
    $exitCode = $proc.ExitCode
    $combinedText = ($combined -join "`n")
    $successPattern = switch ($Step) {
        "train" { "train complete|Predictions saved|Final model saved" }
        "backtest" { "backtest complete|Backtest Sensitivity" }
        "report" { "report complete|Plotly chart" }
        default { "" }
    }
    $logIndicatesSuccess = ($successPattern -ne "" -and $combinedText -match $successPattern)

    if (($null -eq $exitCode -or $exitCode -ne 0) -and -not $logIndicatesSuccess) {
        throw "Step failed: $Step model=$Model task=$Task variant=$Variant. See $logFile"
    }
    if (($null -eq $exitCode -or $exitCode -ne 0) -and $logIndicatesSuccess) {
        Write-Host "Step reported a non-zero/unknown exit code, but expected artifacts were logged. Continuing." -ForegroundColor DarkYellow
    }

    if (Test-Path $stdoutFile) { Remove-Item $stdoutFile -Force }
    if (Test-Path $stderrFile) { Remove-Item $stderrFile -Force }
}

$prefix = Get-ArtifactPrefix -ConfigPath $Config
$needBacktest = -not $SkipBacktest
$needReport = -not $SkipReport

$matrix = New-Object System.Collections.Generic.List[object]
foreach ($modelInput in $Models) {
    $model = $modelInput.ToLowerInvariant()
    if (-not $validTasksByModel.ContainsKey($model)) {
        throw "Unsupported model: $model"
    }
    foreach ($task in $Tasks) {
        if ($task -notin $validTasksByModel[$model]) {
            continue
        }
        foreach ($variant in $Variants) {
            $matrix.Add([pscustomobject]@{
                Model = $model
                Task = $task
                Variant = $variant
            })
        }
    }
}

$summary = New-Object System.Collections.Generic.List[object]
$batchStart = Get-Date
$total = $matrix.Count
$index = 0
$script:completedJobDurations = New-Object System.Collections.Generic.List[double]

Write-Host "Run id: $runId"
Write-Host "Artifact prefix: $prefix"
Write-Host "Matrix size: $total"
Write-Host "Run root: $runRoot"
Write-RunState -Status "running" -Processed 0 -Total $total -Current ([ordered]@{ model = ""; task = ""; variant = ""; steps = "" }) -BatchStart $batchStart -Summary $summary

foreach ($job in $matrix) {
    $index += 1
    $jobStart = Get-Date
    $paths = Get-ComboPaths -Prefix $prefix -Model $job.Model -Task $job.Task -Variant $job.Variant
    $isComplete = Test-ComboComplete -Paths $paths -NeedBacktest $needBacktest -NeedReport $needReport
    $stepsToRun = Get-MissingSteps -Paths $paths -NeedBacktest $needBacktest -NeedReport $needReport -ForceAll:$RunExisting
    $oldMetric = Get-PrimaryMetric -MetricsPath $paths.Metrics -Model $job.Model -Task $job.Task
    $action = "run_missing"
    $status = "pending"
    $errorText = $null
    $backupCount = 0
    $comboBackupRoot = Join-Path $backupRoot ("{0}_{1}_{2}" -f $job.Model, $job.Task, $job.Variant)
    $currentState = [ordered]@{
        model = $job.Model
        task = $job.Task
        variant = $job.Variant
        steps = ($stepsToRun -join ";")
    }
    Write-RunState -Status "running" -Processed ($index - 1) -Total $total -Current $currentState -BatchStart $batchStart -Summary $summary

    if ($isComplete -and -not $RunExisting) {
        $status = "skipped_existing"
        $action = "skip"
        Write-Host ("[{0}/{1}] skip existing: {2} {3} {4}" -f $index, $total, $job.Model, $job.Task, $job.Variant) -ForegroundColor DarkGray
        $summary.Add([pscustomobject]@{
            model = $job.Model
            task = $job.Task
            variant = $job.Variant
            action = $action
            status = $status
            old_metric = if ($oldMetric) { $oldMetric.Metric } else { "" }
            old_value = if ($oldMetric) { $oldMetric.Value } else { "" }
            new_value = ""
            steps = ""
            backup_files = 0
            error = ""
        })
        $script:completedJobDurations.Add(((Get-Date) - $jobStart).TotalSeconds)
        Write-RunState -Status "running" -Processed $index -Total $total -Current $currentState -BatchStart $batchStart -Summary $summary
        continue
    }

    if ($RunExisting -and $isComplete) {
        $action = "rerun_existing"
        $backupCount = Backup-ComboArtifacts -Paths $paths -DestinationRoot $comboBackupRoot
    }

    if ($DryRun) {
        $status = if ($isComplete) { "dry_run_existing" } else { "dry_run_missing" }
        Write-Host ("[{0}/{1}] dry-run {2}: {3} {4} {5}" -f $index, $total, $status, $job.Model, $job.Task, $job.Variant) -ForegroundColor Yellow
        $summary.Add([pscustomobject]@{
            model = $job.Model
            task = $job.Task
            variant = $job.Variant
            action = $action
            status = $status
            old_metric = if ($oldMetric) { $oldMetric.Metric } else { "" }
            old_value = if ($oldMetric) { $oldMetric.Value } else { "" }
            new_value = ""
            steps = ($stepsToRun -join ";")
            backup_files = $backupCount
            error = ""
        })
        $script:completedJobDurations.Add(((Get-Date) - $jobStart).TotalSeconds)
        Write-RunState -Status "dry_run" -Processed $index -Total $total -Current $currentState -BatchStart $batchStart -Summary $summary
        continue
    }

    try {
        foreach ($step in $stepsToRun) {
            Invoke-ExperimentStep -Model $job.Model -Task $job.Task -Variant $job.Variant -Step $step -JobIndex $index -JobTotal $total -BatchStart $batchStart -Summary $summary
        }

        $newMetric = Get-PrimaryMetric -MetricsPath $paths.Metrics -Model $job.Model -Task $job.Task
        $status = "completed"

        if ($RunExisting -and $KeepBest -and $oldMetric -and $newMetric -and ($newMetric.Score -lt $oldMetric.Score)) {
            Restore-ComboArtifacts -SourceRoot $comboBackupRoot
            $status = "restored_old_better"
        }

        $summary.Add([pscustomobject]@{
            model = $job.Model
            task = $job.Task
            variant = $job.Variant
            action = $action
            status = $status
            old_metric = if ($oldMetric) { $oldMetric.Metric } else { if ($newMetric) { $newMetric.Metric } else { "" } }
            old_value = if ($oldMetric) { $oldMetric.Value } else { "" }
            new_value = if ($newMetric) { $newMetric.Value } else { "" }
            steps = ($stepsToRun -join ";")
            backup_files = $backupCount
            error = ""
        })
        $script:completedJobDurations.Add(((Get-Date) - $jobStart).TotalSeconds)
        Write-RunState -Status "running" -Processed $index -Total $total -Current $currentState -BatchStart $batchStart -Summary $summary
    }
    catch {
        $errorText = $_.Exception.Message
        if ($backupCount -gt 0) {
            Restore-ComboArtifacts -SourceRoot $comboBackupRoot
        }
        $summary.Add([pscustomobject]@{
            model = $job.Model
            task = $job.Task
            variant = $job.Variant
            action = $action
            status = "failed"
            old_metric = if ($oldMetric) { $oldMetric.Metric } else { "" }
            old_value = if ($oldMetric) { $oldMetric.Value } else { "" }
            new_value = ""
            steps = ($stepsToRun -join ";")
            backup_files = $backupCount
            error = $errorText
        })
        $script:completedJobDurations.Add(((Get-Date) - $jobStart).TotalSeconds)
        Write-RunState -Status "failed" -Processed $index -Total $total -Current $currentState -BatchStart $batchStart -Summary $summary
        Write-Host $errorText -ForegroundColor Red
        if (-not $ContinueOnError) {
            break
        }
    }
}

$summaryPath = Join-Path $runRoot "full_matrix_summary.csv"
$summary | Export-Csv -Path $summaryPath -NoTypeInformation -Encoding UTF8
$finalStatus = if ($DryRun) { "dry_run_completed" } else { "completed" }
Write-RunState -Status $finalStatus -Processed $summary.Count -Total $total -Current ([ordered]@{ model = ""; task = ""; variant = ""; steps = "" }) -BatchStart $batchStart -Summary $summary

Write-Host ""
Write-Host "=== Supplement Run Summary ===" -ForegroundColor Green
Write-Host "elapsed=$(Format-Duration (((Get-Date) - $batchStart).TotalSeconds))"
Write-Host "summary -> $summaryPath"
$summary | Group-Object status | Select-Object Name, Count | Format-Table -AutoSize

if (($summary | Where-Object { $_.status -eq "failed" }).Count -gt 0 -and -not $ContinueOnError) {
    exit 1
}
