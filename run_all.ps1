$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $python)) {
    throw 'No existe .venv. Ejecute run_model.ps1 una vez para crear el entorno.'
}

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)][string]$Title,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )
    Write-Host "`n=== $Title ===" -ForegroundColor Cyan
    & $python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Fallo la etapa: $Title"
    }
}

Invoke-Step -Title '1. Preparacion de BigQuery' -Arguments @('prepare_bigquery.py')
Invoke-Step -Title '2. Entrenamiento y evaluacion' -Arguments @('train_model.py')
Invoke-Step -Title '3. Generacion del Diario Ejecutivo' -Arguments @('generate_diario.py')

Write-Host "`n=== 4. Inicio de la aplicacion web ===" -ForegroundColor Cyan
$listeners = Get-NetTCPConnection -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue
foreach ($listener in $listeners) {
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)"
    if ($process.CommandLine -like '*Proyecto_Python_Modelado*web_app.py*') {
        Stop-Process -Id $process.ProcessId -Force
    } else {
        throw "El puerto 8001 esta ocupado por otro proceso: $($process.CommandLine)"
    }
}

Start-Process -FilePath $python -ArgumentList @('-B', (Join-Path $projectRoot 'web_app.py')) -WorkingDirectory $projectRoot -WindowStyle Hidden
$limit = (Get-Date).AddSeconds(15)
do {
    Start-Sleep -Milliseconds 300
    $listener = Get-NetTCPConnection -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue
} until ($listener -or (Get-Date) -gt $limit)

if (-not $listener) { throw 'La aplicacion web no pudo iniciar.' }
Start-Process 'http://127.0.0.1:8001/diario'
Write-Host "`nProceso completo." -ForegroundColor Green
Write-Host 'Resultados: http://127.0.0.1:8001'
Write-Host 'Diario Ejecutivo: http://127.0.0.1:8001/diario'
Write-Host 'PDF: http://127.0.0.1:8001/diario/pdf'

