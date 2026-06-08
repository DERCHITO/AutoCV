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

Si `Activate.ps1` falla por *execution policy*, usa las rutas directas (abajo) o [PowerShell: política de ejecución](#powershell-política-de-ejecución).

**Sin activar el venv (recomendado en Windows):**

```powershell
cd C:\Users\user\Documents\GitHub\AutoCV
.\.venv\Scripts\pip.exe install -r requirements-dev.txt
.\.venv\Scripts\ruff.exe check app tests scripts
.\.venv\Scripts\pytest.exe -q
.\.venv\Scripts\python.exe -m app.core.cli health
```

O un solo comando:

```powershell
.\scripts\ci-local.ps1
```

**Con venv activado** (tras `Activate.ps1` o `activate.bat`):

```powershell
pip install -r requirements-dev.txt
ruff check app tests scripts
pytest -q
python -m app.core.cli health
```

### PowerShell: política de ejecución

Error: *«la ejecución de scripts está deshabilitada en este sistema»*.

**Opción A — Una vez por usuario (recomendado):**

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Cierra y abre la terminal; luego `.\.venv\Scripts\Activate.ps1`.

**Opción B — CMD en lugar de PowerShell:**

```cmd
cd C:\Users\crisb\Documents\GitHub\AutoCV
.venv\Scripts\activate.bat
```

**Opción C — No activar:** usa `.\.venv\Scripts\pip.exe`, `ruff.exe`, `pytest.exe` (primer bloque de esta sección).

## Protección de `main`

La rama `main` se protege en **GitHub (interfaz web)**, no solo con archivos del repo.

Sigue la guía: [GITHUB_BRANCH_PROTECTION.md](GITHUB_BRANCH_PROTECTION.md)

## Archivos que no deben subirse

- `.env`, `.env.local`
- `database/*.sqlite`
- `assets/mi_cv.pdf`
- `.venv/`

.