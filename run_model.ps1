$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

function Invoke-ProjectPython {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)
    & $script:pythonExe @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python termino con codigo de salida $LASTEXITCODE."
    }
}

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'No fue posible crear el entorno virtual.' }
}

$script:pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'

# No se actualiza pip automáticamente. En Windows, hacerlo desde un entorno
# activado puede bloquear sus propios archivos. Si pip quedó incompleto,
# ensurepip lo restaura usando la copia incluida con Python.
& $script:pythonExe -m pip --version *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host 'pip esta incompleto; se intentara reparar con ensurepip...' -ForegroundColor Yellow
    Invoke-ProjectPython -Arguments @('-m', 'ensurepip', '--upgrade')
}

Invoke-ProjectPython -Arguments @('-m', 'pip', 'install', '--disable-pip-version-check', '-r', 'requirements.txt')
$modelArguments = @('train_model.py') + $args
Invoke-ProjectPython -Arguments $modelArguments
