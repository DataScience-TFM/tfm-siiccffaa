$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot
$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

# Cargo las variables definidas en .env. Las rutas relativas se resuelven
# respecto de la carpeta del proyecto, no respecto del usuario de Windows.
$envFile = Join-Path $PSScriptRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
            $name, $value = $line -split "=", 2
            if (-not [Environment]::GetEnvironmentVariable($name.Trim(), "Process")) {
                [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim().Trim('"'), "Process")
            }
        }
    }
}

if (-not (Test-Path $python)) {
    Write-Host "Creando entorno virtual..." -ForegroundColor Cyan
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -m venv .venv
    } else {
        & python -m venv .venv
    }
}

if (-not $env:GOOGLE_APPLICATION_CREDENTIALS) {
    throw "Falta GOOGLE_APPLICATION_CREDENTIALS. Revise el archivo .env."
}

if (-not [System.IO.Path]::IsPathRooted($env:GOOGLE_APPLICATION_CREDENTIALS)) {
    $env:GOOGLE_APPLICATION_CREDENTIALS = Join-Path $PSScriptRoot $env:GOOGLE_APPLICATION_CREDENTIALS
}

if (-not (Test-Path $env:GOOGLE_APPLICATION_CREDENTIALS)) {
    throw "No existe el archivo indicado en GOOGLE_APPLICATION_CREDENTIALS."
}

& $python -m pip --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Preparando el instalador de Python..." -ForegroundColor Cyan
    & $python -m ensurepip --upgrade
}

Write-Host "Comprobando e instalando dependencias..." -ForegroundColor Cyan
& $python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    throw "No se pudieron instalar las dependencias de requirements.txt."
}

Write-Host "Dashboard: http://127.0.0.1:8000" -ForegroundColor Green
Start-Process "http://127.0.0.1:8000"
& $python web_app.py
