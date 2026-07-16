param(
    [string]$PsqlPath = "C:\Program Files\PostgreSQL\16\bin\psql.exe",
    [string]$HostName = "localhost",
    [string]$Database = "prevantec",
    [string]$UserName = "postgres",
    [string]$SourcePipeline = "D:\Usuarios\Jorge\Escritorio\TFM\prevantec_tfm_pipeline",
    [string]$TargetUploadDir = "D:\Usuarios\Jorge\Escritorio\TFM_RESULTADOS\data\bigquery_upload",
    [switch]$RunExploration
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $PsqlPath)) {
    throw "No se encontro psql en: $PsqlPath"
}

$runScript = Join-Path $SourcePipeline "scripts\run_pipeline.ps1"
if (-not (Test-Path -LiteralPath $runScript)) {
    throw "No se encontro el pipeline local: $runScript"
}

Write-Host "Este paso regenera los CSV agregados desde PostgreSQL local." -ForegroundColor Cyan
Write-Host "No guarda la clave. El pipeline la pedira por pantalla."
Write-Host "Base: $Database en $HostName"
Write-Host "Pipeline: $SourcePipeline"

& $runScript `
    -PsqlPath $PsqlPath `
    -HostName $HostName `
    -Database $Database `
    -UserName $UserName

if ($RunExploration) {
    Push-Location $SourcePipeline
    try {
        & python ".\scripts\explore_datasets.py"
    }
    finally {
        Pop-Location
    }
}

New-Item -ItemType Directory -Force -Path $TargetUploadDir | Out-Null

$copyMap = @{
    "data\province_month_family.csv" = "province_month_family.csv"
    "data\province_week_family.csv" = "province_week_family.csv"
    "data\data_dictionary.csv" = "data_dictionary.csv"
    "reports\quality_metrics.csv" = "quality_metrics.csv"
    "reports\exploration_summary.csv" = "exploration_summary.csv"
    "reports\province_family_totals.csv" = "province_family_totals.csv"
    "reports\coverage_matrix.csv" = "coverage_matrix.csv"
}

foreach ($entry in $copyMap.GetEnumerator()) {
    $source = Join-Path $SourcePipeline $entry.Key
    if (Test-Path -LiteralPath $source) {
        Copy-Item -LiteralPath $source -Destination (Join-Path $TargetUploadDir $entry.Value) -Force
    } else {
        Write-Warning "No se encontro $source. Si falta un reporte, ejecuta -RunExploration."
    }
}

$coverageMatrix = Join-Path $TargetUploadDir "coverage_matrix.csv"
$coverageLong = Join-Path $TargetUploadDir "coverage_monthly_long.csv"
if (Test-Path -LiteralPath $coverageMatrix) {
    $rows = Import-Csv -LiteralPath $coverageMatrix
    $longRows = foreach ($row in $rows) {
        foreach ($prop in $row.PSObject.Properties) {
            if ($prop.Name -ne "province_name") {
                [PSCustomObject]@{
                    province_name = $row.province_name
                    month_start = $prop.Name
                    has_coverage = [int]$prop.Value
                }
            }
        }
    }
    $longRows | Export-Csv -LiteralPath $coverageLong -NoTypeInformation -Encoding UTF8
}

Write-Host "Extraccion y copia final completadas. Revisa data\bigquery_upload antes de cargar BigQuery." -ForegroundColor Green
