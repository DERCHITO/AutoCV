# AutoCV

Automatización local de postulaciones (Python + n8n + SQLite + Playwright + Ollama), sin servicios cloud de pago.

## Inicio rápido

Documentación completa: [docs/SETUP_LOCAL.md](docs/SETUP_LOCAL.md)

```powershell
cd c:\Users\user\Documents\GitHub\AutoCV
.\.venv\Scripts\Activate.ps1
```

Copia tu CV: `Copy-Item "C:\ruta\tu_cv.pdf" ".\assets\mi_cv.pdf"`

Configuración sensible: `Copy-Item .env.example .env` → editar `.env` (no se sube a Git).

Puente n8n: `python -m app.core.cli serve` → http://localhost:8765/health

## Desarrollo y PRs

- Flujo de ramas y CI: [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)
- **Config obligatoria en GitHub** (proteger `main`): [docs/GITHUB_BRANCH_PROTECTION.md](docs/GITHUB_BRANCH_PROTECTION.md)
- Labels automáticas en PRs: [docs/PR_LABELS.md](docs/PR_LABELS.md)
