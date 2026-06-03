# Configuración obligatoria en GitHub (fuera del repo)

Los archivos en `.github/workflows/` ejecutan CI, pero **bloquear push directo a `main`** requiere configurar el remoto en GitHub.

## Requisitos previos

1. Repositorio creado en GitHub y código subido (`git remote add origin ...`).
2. Al menos **un PR** ejecutado para que aparezcan los checks `lint`, `test`, `smoke`, `require-labels` en la lista de status checks.

## Paso 1 — Proteger `main`

**Settings → Branches → Add branch protection rule** (o **Rules → Rulesets** en organizaciones).

| Opción | Valor |
|--------|--------|
| Branch name pattern | `main` |
| Require a pull request before merging | ✅ |
| Required approvals | 1 (si trabajas solo, ver nota abajo) |
| Dismiss stale pull request approvals when new commits are pushed | ✅ |
| Require status checks to pass before merging | ✅ |
| Require branches to be up to date before merging | ✅ (recomendado) |
| Status checks that are required | `lint`, `test`, `smoke`, `require-labels` |
| Require conversation resolution before merging | ✅ (recomendado) |
| Require linear history | ✅ (recomendado con Squash merge) |
| Do not allow bypassing the above settings | ✅ |
| Restrict who can push to matching branches | ✅ (dejar vacío = nadie pushea directo) |
| Allow force pushes | ❌ |
| Allow deletions | ❌ |

### Trabajas solo (1 persona)

GitHub no permite auto-aprobarte en muchos casos. Opciones:

- **A)** Dejar **0 approvals** pero mantener **CI obligatoria** (mínimo viable).
- **B)** Segunda cuenta o compañero como reviewer.
- **C)** Bot de revisión (futuro).

## Paso 2 — Opciones de merge

**Settings → General → Pull Requests**

- ✅ Allow squash merging
- ❌ Allow merge commits (opcional, para historial simple)
- ❌ Allow rebase merging (opcional)

## Paso 3 — Dependabot (recomendado)

El archivo `.github/dependabot.yml` ya está en el repo. Activa en:

**Settings → Code security and analysis → Dependabot alerts / security updates**

## Paso 4 — Verificar que funciona

```bash
git checkout main
echo "test" >> README.md
git commit -am "test direct push"
git push origin main
```

Debe **fallar** con error de rama protegida.

## Checks en el PR

| Job / workflow | Qué valida |
|----------------|------------|
| `lint` | Ruff + que no exista `.env` commiteado |
| `test` | pytest |
| `smoke` | `python -m app.core.cli health` |
| `require-labels` | El PR tiene al menos una label (automática o manual) |

Etiquetado automático: ver [PR_LABELS.md](PR_LABELS.md).

## Opcional (escalar después)

- **CODEOWNERS** en `.github/CODEOWNERS`
- **Environments** con secrets para despliegue
- **Rulesets** a nivel organización
- Job CI con Playwright (más lento; añadir cuando haya tests de scrapers)

## GitLab

Equivalente: Protected branch `main` + pipeline must succeed + Merge Request required. Ver `.gitlab-ci.yml` si migras (no incluido por defecto).
