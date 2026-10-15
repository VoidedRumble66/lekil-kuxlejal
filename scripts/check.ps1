$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    & '.\.venv\Scripts\python.exe' -m pytest backend/tests -q
    if ($LASTEXITCODE -ne 0) { throw 'Fallaron las pruebas del backend.' }
    Push-Location frontend
    try {
        & npm.cmd run build
        if ($LASTEXITCODE -ne 0) { throw 'Fallo la compilacion del frontend.' }
    } finally { Pop-Location }
    Write-Host 'Pruebas y compilacion completadas.'
} finally { Pop-Location }
