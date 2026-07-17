$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { throw 'No existe .venv. Ejecute primero run_model.ps1.' }

& $python generate_diario.py
if ($LASTEXITCODE -ne 0) { throw 'No fue posible generar las predicciones del Diario Ejecutivo.' }

$connection = Get-NetTCPConnection -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue
if (-not $connection) {
    Start-Process -FilePath $python -ArgumentList 'web_app.py' -WorkingDirectory $projectRoot -WindowStyle Hidden
    Start-Sleep -Seconds 2
}
Start-Process 'http://127.0.0.1:8001/diario'

