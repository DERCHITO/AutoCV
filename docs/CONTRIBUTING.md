# Contribuir a AutoCV

## Flujo de trabajo (obligatorio)

1. **Nunca** hagas commit ni push directo a `main`.
2. Actualiza `main` y crea una rama:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/nombre-corto
   ```
3. Desarrolla, commitea y sube la rama:
   ```bash
   git push -u origin feature/nombre-corto
   ```
4. Abre un **Pull Request** hacia `main` en GitHub.
5. Espera a que CI pase: `lint`, `test`, `smoke`.
6. Tras revisión (si aplica), merge con **Squash merge**.

### Prefijos de rama

| Prefijo | Uso |
|---------|-----|
| `feature/` | Nueva funcionalidad |
| `fix/` | Corrección de bugs |
| `chore/` | CI, deps, docs |
| `hotfix/` | Corrección urgente sobre producción |

## CI local (antes del PR)

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
ruff check app tests scripts
pytest -q
python -m app.core.cli health
```

## Protección de `main`

La rama `main` se protege en **GitHub (interfaz web)**, no solo con archivos del repo.

Sigue la guía: [GITHUB_BRANCH_PROTECTION.md](GITHUB_BRANCH_PROTECTION.md)

## Archivos que no deben subirse

- `.env`, `.env.local`
- `database/*.sqlite`
- `assets/mi_cv.pdf`
- `.venv/`
