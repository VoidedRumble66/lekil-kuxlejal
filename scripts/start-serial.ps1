param(
    [string]$Port = 'COM6',
    [string]$BackendUrl = 'http://127.0.0.1:8000',
    [string]$TokenFile = ''
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $pythonPath)) { throw 'Ejecuta primero scripts/setup.ps1.' }
Push-Location (Join-Path $projectRoot 'backend')
try {
    $readerArguments = @('-m', 'serial_reader.service', '--port', $Port, '--backend-url', $BackendUrl)
    if ($TokenFile) { $readerArguments += @('--token-file', $TokenFile) }
    & $pythonPath @readerArguments
    if ($LASTEXITCODE -ne 0) { throw 'El lector serial termino con un error.' }
} finally { Pop-Location }
