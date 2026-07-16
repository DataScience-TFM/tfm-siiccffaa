<#
.SYNOPSIS
    Ejecuta en orden el flujo reproducible PostgreSQL local -> CSV -> Cloud
    Storage -> BigQuery -> vistas -> validacion.

.DESCRIPTION
    Fases del ciclo de Ciencia de Datos:
      2. Recopilacion y comprension de datos.
      3. Preparacion, limpieza y EDA.
      6. Evaluacion y validacion de la carga.

    Este es el punto unico de entrada para PowerShell. Usa las herramientas
    instaladas con Google Cloud CLI: gcloud y bq.

    Por seguridad:
      - No contiene ni guarda contrasenas.
      - La clave de PostgreSQL se solicita interactivamente.
      - La autenticacion web de Google solo se inicia con -AuthenticateGoogle.
      - La extraccion de PostgreSQL solo se ejecuta con -ExtractFromPostgreSQL.
      - Las cargas usan --replace: reemplazan las tablas analiticas homonimas.

.PARAMETER ProjectId
    Identificador del proyecto de Google Cloud, por ejemplo: mi-proyecto-gcp.

.PARAMETER BucketName
    Nombre globalmente unico del bucket de Cloud Storage.

.PARAMETER Dataset
    Dataset analitico de destino. Valor predeterminado: tfm_siiccfaa.

.PARAMETER Location
    Region de Cloud Storage y BigQuery. Predeterminado: europe-southwest1.

.PARAMETER Prefix
    Carpeta dentro del bucket. Predeterminado: siiccfaa.

.PARAMETER AuthenticateGoogle
    Ejecuta gcloud auth login y gcloud auth application-default login.

.PARAMETER ExtractFromPostgreSQL
    Regenera los CSV desde PostgreSQL antes de subirlos.

.PARAMETER RunExploration
    Al extraer PostgreSQL, ejecuta tambien explore_datasets.py.

.EXAMPLE
    Set-Location "D:\Usuarios\Jorge\Escritorio\TFM_RESULTADOS"
    .\scripts\bigquery\00_migracion_completa_postgresql_a_bigquery.ps1 `
      -ProjectId "mi-proyecto-gcp" `
      -BucketName "tfm-siiccfaa-jorge-unico" `
      -AuthenticateGoogle

.EXAMPLE
    # Flujo completo, incluida la regeneracion desde PostgreSQL local.
    .\scripts\bigquery\00_migracion_completa_postgresql_a_bigquery.ps1 `
      -ProjectId "mi-proyecto-gcp" `
      -BucketName "tfm-siiccfaa-jorge-unico" `
      -ExtractFromPostgreSQL `
      -RunExploration
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$ProjectId,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$BucketName,

    [string]$Dataset = "tfm_siiccfaa",
    [string]$Location = "europe-southwest1",
    [string]$Prefix = "siiccfaa",
    [string]$PackageRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [string]$PsqlPath = "C:\Program Files\PostgreSQL\16\bin\psql.exe",
    [string]$PostgreSqlHost = "localhost",
    [int]$PostgreSqlPort = 5432,
    [string]$PostgreSqlDatabase = "prevantec",
    [string]$PostgreSqlUser = "postgres",
    [string]$SourcePipeline = "D:\Usuarios\Jorge\Escritorio\TFM\prevantec_tfm_pipeline",
    [switch]$AuthenticateGoogle,
    [switch]$ExtractFromPostgreSQL,
    [switch]$RunExploration
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Step {
    param([int]$Number, [string]$Message)
    Write-Host ""
    Write-Host "[$Number] $Message" -ForegroundColor Cyan
}

function Assert-LastExitCode {
    param([string]$Operation)
    if ($LASTEXITCODE -ne 0) {
        throw "$Operation fallo con codigo de salida $LASTEXITCODE."
    }
}

function Assert-Command {
    param([string]$Name)
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        throw "$Name no esta instalado o no esta en PATH. Instala Google Cloud CLI y abre una nueva consola PowerShell."
    }
    Write-Host "$Name OK: $($command.Source)"
}

function Invoke-BqLoad {
    param(
        [string]$TableName,
        [string]$CsvName,
        [string]$SchemaName
    )

    $schemaPath = Join-Path $script:SchemaDir $SchemaName
    $target = "$ProjectId`:$Dataset.$TableName"
    $source = "$script:GcsPrefix/$CsvName"
    Write-Host "Cargando $source -> $target"
    & bq load `
        --location=$Location `
        --source_format=CSV `
        --skip_leading_rows=1 `
        --replace `
        $target `
        $source `
        $schemaPath
    Assert-LastExitCode "Carga de $TableName"
}

$script:UploadDir = Join-Path $PackageRoot "data\bigquery_upload"
$script:SchemaDir = Join-Path $PackageRoot "config\bigquery_schemas"
$script:SqlDir = Join-Path $PackageRoot "sql\bigquery"
$script:GcsPrefix = "gs://$BucketName/$Prefix"

$tables = @(
    @{ Table = "province_month_family"; Csv = "province_month_family.csv"; Schema = "province_month_family.schema.json" },
    @{ Table = "province_week_family"; Csv = "province_week_family.csv"; Schema = "province_week_family.schema.json" },
    @{ Table = "data_dictionary"; Csv = "data_dictionary.csv"; Schema = "data_dictionary.schema.json" },
    @{ Table = "quality_metrics"; Csv = "quality_metrics.csv"; Schema = "quality_metrics.schema.json" },
    @{ Table = "exploration_summary"; Csv = "exploration_summary.csv"; Schema = "exploration_summary.schema.json" },
    @{ Table = "province_family_totals"; Csv = "province_family_totals.csv"; Schema = "province_family_totals.schema.json" },
    @{ Table = "coverage_monthly_long"; Csv = "coverage_monthly_long.csv"; Schema = "coverage_monthly_long.schema.json" }
)

Write-Host "MIGRACION ANALITICA TFM: PostgreSQL -> BigQuery" -ForegroundColor Green
Write-Host "Proyecto : $ProjectId"
Write-Host "Bucket   : gs://$BucketName"
Write-Host "Dataset  : $Dataset"
Write-Host "Region   : $Location"
Write-Host "Paquete  : $PackageRoot"

Write-Step 1 "Comprobar PowerShell, Google Cloud CLI y archivos locales"
Assert-Command "gcloud"
Assert-Command "bq"

foreach ($item in $tables) {
    $csvPath = Join-Path $script:UploadDir $item.Csv
    $schemaPath = Join-Path $script:SchemaDir $item.Schema
    if (-not (Test-Path -LiteralPath $csvPath)) {
        throw "Falta CSV requerido: $csvPath"
    }
    if (-not (Test-Path -LiteralPath $schemaPath)) {
        throw "Falta esquema requerido: $schemaPath"
    }
}

$viewSqlPath = Join-Path $script:SqlDir "01_create_views.sql"
$validationSqlPath = Join-Path $script:SqlDir "02_validation_queries.sql"
foreach ($requiredPath in @($viewSqlPath, $validationSqlPath)) {
    if (-not (Test-Path -LiteralPath $requiredPath)) {
        throw "Falta archivo SQL requerido: $requiredPath"
    }
}

if ($ExtractFromPostgreSQL) {
    Write-Step 2 "Extraer y agregar datos desde PostgreSQL local"
    $pipelineScript = Join-Path $SourcePipeline "scripts\run_pipeline.ps1"
    if (-not (Test-Path -LiteralPath $PsqlPath)) {
        throw "No se encontro psql: $PsqlPath"
    }
    if (-not (Test-Path -LiteralPath $pipelineScript)) {
        throw "No se encontro el pipeline: $pipelineScript"
    }

    & $pipelineScript `
        -PsqlPath $PsqlPath `
        -HostName $PostgreSqlHost `
        -Port $PostgreSqlPort `
        -Database $PostgreSqlDatabase `
        -UserName $PostgreSqlUser

    if ($RunExploration) {
        Push-Location $SourcePipeline
        try {
            & python ".\scripts\explore_datasets.py"
            Assert-LastExitCode "Exploracion de datos"
        }
        finally {
            Pop-Location
        }
    }

    $copyMap = @{
        "data\province_month_family.csv" = "province_month_family.csv"
        "data\province_week_family.csv" = "province_week_family.csv"
        "data\data_dictionary.csv" = "data_dictionary.csv"
        "reports\quality_metrics.csv" = "quality_metrics.csv"
        "reports\exploration_summary.csv" = "exploration_summary.csv"
        "reports\province_family_totals.csv" = "province_family_totals.csv"
        "reports\coverage_matrix.csv" = "coverage_matrix.csv"
    }
    New-Item -ItemType Directory -Force -Path $script:UploadDir | Out-Null
    foreach ($entry in $copyMap.GetEnumerator()) {
        $source = Join-Path $SourcePipeline $entry.Key
        if (Test-Path -LiteralPath $source) {
            Copy-Item -LiteralPath $source -Destination (Join-Path $script:UploadDir $entry.Value) -Force
        } else {
            Write-Warning "No se encontro: $source"
        }
    }

    $coverageMatrix = Join-Path $script:UploadDir "coverage_matrix.csv"
    $coverageLong = Join-Path $script:UploadDir "coverage_monthly_long.csv"
    if (Test-Path -LiteralPath $coverageMatrix) {
        $longRows = foreach ($row in (Import-Csv -LiteralPath $coverageMatrix)) {
            foreach ($property in $row.PSObject.Properties) {
                if ($property.Name -ne "province_name") {
                    [PSCustomObject]@{
                        province_name = $row.province_name
                        month_start = $property.Name
                        has_coverage = [int]$property.Value
                    }
                }
            }
        }
        $longRows | Export-Csv -LiteralPath $coverageLong -NoTypeInformation -Encoding UTF8
    }
} else {
    Write-Step 2 "Usar los CSV ya preparados (extraccion PostgreSQL omitida)"
}

Write-Step 3 "Autenticar Google Cloud"
if ($AuthenticateGoogle) {
    & gcloud auth login
    Assert-LastExitCode "gcloud auth login"
    & gcloud auth application-default login
    Assert-LastExitCode "gcloud auth application-default login"
} else {
    Write-Host "Autenticacion interactiva omitida. Se usara la sesion actual de gcloud."
    & gcloud auth list --filter=status:ACTIVE --format="value(account)"
    Assert-LastExitCode "Comprobacion de cuenta activa"
}

Write-Step 4 "Seleccionar proyecto y activar APIs"
& gcloud config set project $ProjectId
Assert-LastExitCode "Seleccion del proyecto"
& gcloud services enable bigquery.googleapis.com storage.googleapis.com --project=$ProjectId
Assert-LastExitCode "Activacion de APIs"

Write-Step 5 "Crear o reutilizar el bucket de Cloud Storage"
& gcloud storage buckets describe "gs://$BucketName" --project=$ProjectId 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    & gcloud storage buckets create "gs://$BucketName" `
        --project=$ProjectId `
        --location=$Location `
        --uniform-bucket-level-access
    Assert-LastExitCode "Creacion del bucket"
} else {
    Write-Host "El bucket ya existe: gs://$BucketName"
}

Write-Step 6 "Crear o reutilizar el dataset de BigQuery"
& bq --project_id=$ProjectId --location=$Location show "$ProjectId`:$Dataset" 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    & bq --project_id=$ProjectId --location=$Location mk --dataset "$ProjectId`:$Dataset"
    Assert-LastExitCode "Creacion del dataset"
} else {
    Write-Host "El dataset ya existe: $ProjectId`:$Dataset"
}

Write-Step 7 "Subir CSV a Cloud Storage"
$uploadFiles = @($tables | ForEach-Object { $_.Csv }) + "manifest_bigquery_upload.csv"
foreach ($fileName in $uploadFiles) {
    $localPath = Join-Path $script:UploadDir $fileName
    if (Test-Path -LiteralPath $localPath) {
        & gcloud storage cp $localPath "$script:GcsPrefix/$fileName"
        Assert-LastExitCode "Subida de $fileName"
    } elseif ($fileName -eq "manifest_bigquery_upload.csv") {
        Write-Warning "Manifiesto opcional no encontrado: $localPath"
    } else {
        throw "CSV requerido no encontrado: $localPath"
    }
}

Write-Step 8 "Crear o reemplazar tablas en BigQuery"
foreach ($item in $tables) {
    Invoke-BqLoad -TableName $item.Table -CsvName $item.Csv -SchemaName $item.Schema
}

Write-Step 9 "Crear o reemplazar vistas analiticas"
$viewSql = (Get-Content -LiteralPath $viewSqlPath -Raw).
    Replace("{{PROJECT_ID}}", $ProjectId).
    Replace("{{DATASET}}", $Dataset)
& bq query `
    --location=$Location `
    --project_id=$ProjectId `
    --use_legacy_sql=false `
    $viewSql
Assert-LastExitCode "Creacion de vistas"

Write-Step 10 "Validar tablas, cobertura, familias y particiones temporales"
$validationSql = (Get-Content -LiteralPath $validationSqlPath -Raw).
    Replace("{{PROJECT_ID}}", $ProjectId).
    Replace("{{DATASET}}", $Dataset)
& bq query `
    --location=$Location `
    --project_id=$ProjectId `
    --use_legacy_sql=false `
    $validationSql
Assert-LastExitCode "Validacion final"

Write-Host ""
Write-Host "MIGRACION FINALIZADA CORRECTAMENTE" -ForegroundColor Green
Write-Host "Dataset: $ProjectId.$Dataset"
Write-Host "Archivos: $script:GcsPrefix"
Write-Host "Revisa los conteos antes de continuar con modelado."
