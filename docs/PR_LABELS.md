# Etiquetado automático de Pull Requests

## Archivos

| Archivo | Función |
|---------|---------|
| `.github/labels.yml` | Catálogo de labels (nombre, color, descripción). Fuente de verdad. |
| `.github/labeler.yml` | Reglas: rama → label y archivos modificados → label. |
| `.github/workflows/labels-sync.yml` | Crea/actualiza labels en GitHub al cambiar `labels.yml` en `main`. |
| `.github/workflows/pr-labels.yml` | En cada PR: sincroniza labels, aplica reglas, falla si el PR queda sin labels. |

## Flujo en un PR

1. **sync-labels** — Asegura que existan `feature`, `bug`, `ci/cd`, etc.
2. **apply-labels** — `actions/labeler` según rama y diff.
3. **require-labels** — Si el PR tiene 0 labels → el check falla (no merge).

## Convención de ramas

Usa prefijos para que el labeler asigne etiquetas automáticamente:

`feature/`, `fix/`, `hotfix/`, `docs/`, `refactor/`, `test/`, `chore/`

Variantes con mayúscula inicial (`Feature/`) también aplican.

## Branch protection

Añade **`require-labels`** a los status checks obligatorios junto a `lint`.

Ver [GITHUB_BRANCH_PROTECTION.md](GITHUB_BRANCH_PROTECTION.md).
