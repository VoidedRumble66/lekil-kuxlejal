$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location (Join-Path $projectRoot 'frontend')
try {
    & npm.cmd run dev -- --port 5173 --strictPort
    if ($LASTEXITCODE -ne 0) { throw 'El frontend termino con un error. Revisa el mensaje anterior.' }
} finally { Pop-Location }
