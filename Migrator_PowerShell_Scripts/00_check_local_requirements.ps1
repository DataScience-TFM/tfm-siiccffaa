param(
    [string]$PackageRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
)

$ErrorActionPreference = "Stop"

Write-Host "TFM BigQuery pre-check" -ForegroundColor Cyan
Write-Host "Package root: $PackageRoot"

$requiredCommands = @("gcloud", "bq")
foreach ($cmd in $requiredCommands) {
    $found = Get-Command $cmd -ErrorAction SilentlyContinue
    if ($null -eq $found) {
        Write-Warning "$cmd no esta en PATH. Instala Google Cloud CLI y abre una nueva terminal."
    } else {
        Write-Host "$cmd OK: $($found.Source)"
    }
}

$uploadDir = Join-Path $PackageRoot "data\bigquery_upload"
$schemaDir = Join-Path $PackageRoot "config\bigquery_schemas"

$requiredFiles = @(
    "province_month_family.csv",
    "province_week_family.csv",
    "data_dictionary.csv",
    "quality_metrics.csv",
    "exploration_summary.csv",
    "province_family_totals.csv",
    "coverage_monthly_long.csv",
    "manifest_bigquery_upload.csv"
)

foreach ($file in $requiredFiles) {
    $path = Join-Path $uploadDir $file
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Falta archivo requerido: $path"
    }
}

$requiredSchemas = @(
    "province_month_family.schema.json",
    "province_week_family.schema.json",
    "data_dictionary.schema.json",
    "quality_metrics.schema.json",
    "exploration_summary.schema.json",
    "province_family_totals.schema.json",
    "coverage_monthly_long.schema.json"
)

foreach ($schema in $requiredSchemas) {
    $path = Join-Path $schemaDir $schema
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Falta schema requerido: $path"
    }
}

Write-Host ""
Write-Host "Archivos listos para BigQuery:" -ForegroundColor Green
Import-Csv -LiteralPath (Join-Path $uploadDir "manifest_bigquery_upload.csv") |
    Where-Object { $_.load_to_bigquery -eq "yes" } |
    Select-Object file, table_name, rows, bytes |
    Format-Table -AutoSize

Write-Host "Nota de seguridad: report_features_controlled.csv no forma parte del paquete de subida." -ForegroundColor Yellow
