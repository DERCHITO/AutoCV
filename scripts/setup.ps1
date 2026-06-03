# AutoCV — configuración del entorno local (Windows PowerShell)
# Ejecutar desde la raíz del repositorio: .\scripts\setup.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "==> Creando entorno virtual .venv" -ForegroundColor Cyan
$Python = if (Get-Command python -ErrorAction SilentlyContinue) {
    (Get-Command python).Source
} else {
    Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"
}
if (-not (Test-Path ".venv")) {
    & $Python -m venv .venv
}

Write-Host "==> Activando venv e instalando dependencias" -ForegroundColor Cyan
& ".\.venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip
pip install -r requirements.txt

Write-Host "==> Instalando navegadores Playwright" -ForegroundColor Cyan
playwright install

Write-Host "==> Verificando instalación" -ForegroundColor Cyan
python -c "import sqlalchemy, playwright, rapidfuzz, pydantic, httpx; print('OK:', sqlalchemy.__version__, pydantic.__version__)"

Write-Host "`nEntorno listo. Activa el venv con: .\.venv\Scripts\Activate.ps1" -ForegroundColor Green
