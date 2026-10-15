param([string]$PythonExe = '')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    if (!(Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
        if ($PythonExe) {
            & $PythonExe -m venv .venv
        } elseif (Get-Command py -ErrorAction SilentlyContinue) {
            & py -3.13 -m venv .venv
        } elseif (Get-Command python -ErrorAction SilentlyContinue) {
            & python -m venv .venv
        } else {
            throw 'Instala Python 3.13 o indica su ruta: .\scripts\setup.ps1 -PythonExe C:\ruta\python.exe'
        }
        if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno Python.' }
    }
    & '.\.venv\Scripts\python.exe' -c 'import sys; print(sys.version); sys.exit(sys.version_info < (3, 12))'
    if ($LASTEXITCODE -ne 0) { throw 'Version de Python no compatible.' }
    & '.\.venv\Scripts\python.exe' -m pip install -r backend\requirements-dev.txt -c backend\constraints-lock.txt
    if ($LASTEXITCODE -ne 0) { throw 'Fallo la instalacion de Python.' }
    if (!(Get-Command node -ErrorAction SilentlyContinue)) { throw 'Instala Node.js 24 LTS.' }
    & node -e 'if (parseInt(process.versions.node, 10) < 24) process.exit(1)'
    if ($LASTEXITCODE -ne 0) { throw 'Se requiere Node.js 24 o superior.' }
    Push-Location frontend
    try {
        & npm.cmd ci
        if ($LASTEXITCODE -ne 0) { throw 'Fallo npm ci.' }
    } finally { Pop-Location }
    Write-Host 'Dependencias listas. Inicia la API y el frontend en dos terminales (consulta README.md).'
} finally { Pop-Location }
