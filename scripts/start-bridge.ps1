# Levanta la API puente para n8n (ejecutar desde la raíz del repo)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (-not (Test-Path ".env")) {
    Write-Host "Crea .env desde .env.example: Copy-Item .env.example .env" -ForegroundColor Yellow
}

& ".\.venv\Scripts\python.exe" -m app.core.cli serve
