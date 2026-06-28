# CI local sin activar el venv (evita ExecutionPolicy de Activate.ps1)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$pip = Join-Path $Root ".venv\Scripts\pip.exe"
$ruff = Join-Path $Root ".venv\Scripts\ruff.exe"

if (-not (Test-Path $pip)) {
    Write-Error "No existe .venv. Ejecuta primero: .\scripts\setup.ps1"
}

& $pip install -r requirements-dev.txt
& $ruff check app scripts
Write-Host "`nCI local OK" -ForegroundColor Green
