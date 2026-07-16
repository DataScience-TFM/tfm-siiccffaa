param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [string]$Dataset = "tfm_siiccfaa",
    [string]$Location = "europe-southwest1",
    [string]$PackageRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
)

$ErrorActionPreference = "Stop"

if ($null -eq (Get-Command bq -ErrorAction SilentlyContinue)) {
    throw "bq no esta instalado o no esta en PATH."
}

$sqlPath = Join-Path $PackageRoot "sql\bigquery\02_validation_queries.sql"
$sql = Get-Content -LiteralPath $sqlPath -Raw
$sql = $sql.Replace("{{PROJECT_ID}}", $ProjectId).Replace("{{DATASET}}", $Dataset)

Write-Host "Running validation queries against $ProjectId.$Dataset" -ForegroundColor Cyan
& bq query `
    --location=$Location `
    --project_id=$ProjectId `
    --use_legacy_sql=false `
    $sql

Write-Host "Validation finished. Review row counts, family totals and usable-month checks." -ForegroundColor Green
