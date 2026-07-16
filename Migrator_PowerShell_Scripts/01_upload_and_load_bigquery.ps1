param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [Parameter(Mandatory = $true)]
    [string]$BucketName,

    [string]$Dataset = "tfm_siiccfaa",
    [string]$Location = "europe-southwest1",
    [string]$Prefix = "siiccfaa",
    [string]$PackageRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
)

$ErrorActionPreference = "Stop"

function Assert-Command {
    param([string]$Name)
    if ($null -eq (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name no esta instalado o no esta en PATH."
    }
}

function Load-CsvTable {
    param(
        [string]$TableName,
        [string]$CsvName,
        [string]$SchemaName
    )

    $schemaPath = Join-Path $SchemaDir $SchemaName
    $target = "$ProjectId`:$Dataset.$TableName"
    $source = "$GcsPrefix/$CsvName"

    Write-Host "Loading $source -> $target" -ForegroundColor Cyan
    & bq load `
        --location=$Location `
        --source_format=CSV `
        --skip_leading_rows=1 `
        --replace `
        $target `
        $source `
        $schemaPath
}

Assert-Command "gcloud"
Assert-Command "bq"

$UploadDir = Join-Path $PackageRoot "data\bigquery_upload"
$SchemaDir = Join-Path $PackageRoot "config\bigquery_schemas"
$SqlDir = Join-Path $PackageRoot "sql\bigquery"
$GcsPrefix = "gs://$BucketName/$Prefix"

Write-Host "Project: $ProjectId"
Write-Host "Bucket:  $BucketName"
Write-Host "Dataset: $Dataset"
Write-Host "Region:  $Location"
Write-Host "Prefix:  $GcsPrefix"

& gcloud config set project $ProjectId
& gcloud services enable bigquery.googleapis.com
& gcloud services enable storage.googleapis.com

try {
    & gcloud storage buckets describe "gs://$BucketName" | Out-Null
    Write-Host "Bucket already exists: gs://$BucketName"
} catch {
    Write-Host "Creating bucket: gs://$BucketName" -ForegroundColor Cyan
    & gcloud storage buckets create "gs://$BucketName" `
        --location=$Location `
        --uniform-bucket-level-access
}

try {
    & bq --location=$Location show "$ProjectId`:$Dataset" | Out-Null
    Write-Host "Dataset already exists: $ProjectId`:$Dataset"
} catch {
    Write-Host "Creating dataset: $ProjectId`:$Dataset" -ForegroundColor Cyan
    & bq --location=$Location mk --dataset "$ProjectId`:$Dataset"
}

$filesToUpload = @(
    "province_month_family.csv",
    "province_week_family.csv",
    "data_dictionary.csv",
    "quality_metrics.csv",
    "exploration_summary.csv",
    "province_family_totals.csv",
    "coverage_monthly_long.csv",
    "manifest_bigquery_upload.csv"
)

foreach ($file in $filesToUpload) {
    $localPath = Join-Path $UploadDir $file
    if (-not (Test-Path -LiteralPath $localPath)) {
        throw "No existe el archivo local: $localPath"
    }
    & gcloud storage cp $localPath "$GcsPrefix/$file"
}

Load-CsvTable "province_month_family" "province_month_family.csv" "province_month_family.schema.json"
Load-CsvTable "province_week_family" "province_week_family.csv" "province_week_family.schema.json"
Load-CsvTable "data_dictionary" "data_dictionary.csv" "data_dictionary.schema.json"
Load-CsvTable "quality_metrics" "quality_metrics.csv" "quality_metrics.schema.json"
Load-CsvTable "exploration_summary" "exploration_summary.csv" "exploration_summary.schema.json"
Load-CsvTable "province_family_totals" "province_family_totals.csv" "province_family_totals.schema.json"
Load-CsvTable "coverage_monthly_long" "coverage_monthly_long.csv" "coverage_monthly_long.schema.json"

$viewSqlPath = Join-Path $SqlDir "01_create_views.sql"
$viewSql = Get-Content -LiteralPath $viewSqlPath -Raw
$viewSql = $viewSql.Replace("{{PROJECT_ID}}", $ProjectId).Replace("{{DATASET}}", $Dataset)

Write-Host "Creating analytical views" -ForegroundColor Cyan
& bq query `
    --location=$Location `
    --project_id=$ProjectId `
    --use_legacy_sql=false `
    $viewSql

Write-Host "BigQuery package loaded. Run 02_validate_bigquery.ps1 next." -ForegroundColor Green
