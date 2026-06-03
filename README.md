# AutoCV

Automatización local de postulaciones (Python + n8n + SQLite + Playwright + Ollama), sin servicios cloud de pago.

## Inicio rápido

Documentación completa: [docs/SETUP_LOCAL.md](docs/SETUP_LOCAL.md)

```powershell
cd c:\Users\crisb\Documents\GitHub\AutoCV
.\scripts\setup.ps1
```

Copia tu CV: `Copy-Item "C:\ruta\tu_cv.pdf" ".\assets\mi_cv.pdf"`

Configuración sensible: `Copy-Item .env.example .env` → editar `.env` (no se sube a Git).

Puente n8n: `python -m app.core.cli serve` → http://localhost:8765/health
