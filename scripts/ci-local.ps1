# CI local sin activar el venv (evita ExecutionPolicy de Activate.ps1)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$py = Join-Path $Root ".venv\Scripts\python.exe"
$pip = Join-Path $Root ".venv\Scripts\pip.exe"
$ruff = Join-Path $Root ".venv\Scripts\ruff.exe"
$pytest = Join-Path $Root ".venv\Scripts\pytest.exe"

if (-not (Test-Path $py)) {
    Write-Error "No existe .venv. Ejecuta primero: .\scripts\setup.ps1"
}

& $pip install -r requirements-dev.txt
& $ruff check app tests scripts
& $pytest -q
& $py -m app.core.cli health
Write-Host "`nCI local OK" -ForegroundColor Green
