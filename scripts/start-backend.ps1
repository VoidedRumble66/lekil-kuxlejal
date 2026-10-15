$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $pythonPath)) { throw 'Ejecuta primero .\scripts\setup.ps1.' }
Push-Location (Join-Path $projectRoot 'backend')
try {
    & $pythonPath -m uvicorn app.main:app --host 127.0.0.1 --port 8000
    if ($LASTEXITCODE -ne 0) { throw 'La API termino con un error. Revisa el mensaje anterior.' }
} finally { Pop-Location }
