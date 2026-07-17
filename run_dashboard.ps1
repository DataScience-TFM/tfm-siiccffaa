$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $python)) {
    throw 'No existe .venv. Ejecute primero .\run_model.ps1.'
}

& $python -c "import flask" 2>$null
if ($LASTEXITCODE -ne 0) {
    & $python -m pip install --disable-pip-version-check -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'No fue posible instalar Flask.' }
}

Start-Process 'http://127.0.0.1:8001'
& $python web_app.py

