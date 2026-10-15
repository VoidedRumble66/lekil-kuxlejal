$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    # Cada cuenta y ejecucion recibe temporales propios; no reutiliza carpetas
    # de pytest creadas por otra cuenta Windows ni elimina rutas existentes.
    $taskCheckPath = [System.IO.Path]::GetFullPath((Join-Path $projectRoot ('.run\checks\' + [guid]::NewGuid().ToString('N'))))
    if (!$taskCheckPath.StartsWith($projectRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Ruta de pruebas fuera del proyecto.' }
    if (Test-Path -LiteralPath $taskCheckPath) { throw 'La carpeta temporal ya existe.' }
    New-Item -ItemType Directory -Path $taskCheckPath | Out-Null
    $taskPytestPath = Join-Path $taskCheckPath 'pytest'
    $taskCachePath = Join-Path $taskCheckPath 'cache'
    & '.\.venv\Scripts\python.exe' -m pytest backend/tests -q --basetemp $taskPytestPath -o "cache_dir=$taskCachePath"
    if ($LASTEXITCODE -ne 0) { throw 'Fallaron las pruebas del backend.' }
    Push-Location frontend
    try {
        & npm.cmd run build
        if ($LASTEXITCODE -ne 0) { throw 'Fallo la compilacion del frontend.' }
    } finally { Pop-Location }
    Write-Host 'Pruebas y compilacion completadas.'
} finally { Pop-Location }
