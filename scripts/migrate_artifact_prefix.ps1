param(
    [string]$OldPrefix = "onchain_crypto_graduation_research",
    [string]$NewPrefix = "btc_onchain"
)

$ErrorActionPreference = "Stop"

function Rename-WithPrefix {
    param(
        [string]$BaseDir
    )

    if (-not (Test-Path $BaseDir)) {
        return 0
    }

    $renamed = 0
    $files = Get-ChildItem -Path $BaseDir -Recurse -File | Sort-Object FullName -Descending
    foreach ($file in $files) {
        $newName = $file.Name
        $newName = $newName.Replace("${OldPrefix}_BTC_USD_", "${NewPrefix}_")
        $newName = $newName.Replace("${OldPrefix}_", "${NewPrefix}_")
        if ($newName -like "latest_prediction_*") {
            $newName = $newName.Replace("latest_prediction_", "${NewPrefix}_latest_")
        }

        if ($newName -ne $file.Name) {
            $dst = Join-Path $file.DirectoryName $newName
            if (-not (Test-Path $dst)) {
                Move-Item -LiteralPath $file.FullName -Destination $dst
                $renamed++
            }
        }
    }

    return $renamed
}

function Merge-DataAuditDirectory {
    $oldDir = Join-Path "reports/summary/data_audit" $OldPrefix
    $newDir = Join-Path "reports/summary/data_audit" $NewPrefix

    if (-not (Test-Path $oldDir)) {
        return $false
    }

    if (-not (Test-Path $newDir)) {
        Move-Item -LiteralPath $oldDir -Destination $newDir
        return $true
    }

    Get-ChildItem -LiteralPath $oldDir | ForEach-Object {
        $dst = Join-Path $newDir $_.Name
        if (-not (Test-Path $dst)) {
            Move-Item -LiteralPath $_.FullName -Destination $dst
        }
    }

    $remaining = Get-ChildItem -LiteralPath $oldDir -Force
    if (-not $remaining) {
        Remove-Item -LiteralPath $oldDir
    }

    return $true
}

function Update-MetaFiles {
    param(
        [string]$MetaDir
    )

    if (-not (Test-Path $MetaDir)) {
        return 0
    }

    $updated = 0
    Get-ChildItem -Path $MetaDir -Filter "${NewPrefix}_*_meta.json" -File | ForEach-Object {
        $raw = Get-Content -LiteralPath $_.FullName -Raw
        $newRaw = $raw.Replace($OldPrefix, $NewPrefix)
        if ($newRaw -ne $raw) {
            Set-Content -LiteralPath $_.FullName -Value $newRaw -Encoding UTF8
            $updated++
        }
    }
    return $updated
}

$targets = @(
    "data/features",
    "models_saved",
    "reports",
    "reports/figures",
    "reports/trading"
)

$totalRenamed = 0
foreach ($target in $targets) {
    $count = Rename-WithPrefix -BaseDir $target
    if ($count -gt 0) {
        Write-Host "Renamed $count files under $target"
    }
    $totalRenamed += $count
}

$mergedAudit = Merge-DataAuditDirectory
$updatedMeta = Update-MetaFiles -MetaDir "models_saved"

Write-Host "Migration complete."
Write-Host "Files renamed: $totalRenamed"
Write-Host "Data audit directory migrated: $mergedAudit"
Write-Host "Meta files updated: $updatedMeta"
