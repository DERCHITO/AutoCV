# n8n — AutoCV

## Arrancar

```powershell
cd n8n
docker compose up -d
```

UI: http://localhost:5678

## Importar workflows

1. Abre n8n → **Workflows** → **Import from File**.
2. Importa los JSON de `n8n/workflows/`:
   - `autocv-python-bridge-health.json` — requiere API Python en marcha.
   - `autocv-db-init.json` — crea tablas SQLite vía puente.
   - `autocv-ollama-tags.json` — comprueba Ollama en el host.

## Antes de ejecutar workflows de Python

En otra terminal (raíz del repo):

```powershell
.\.venv\Scripts\Activate.ps1
Copy-Item .env.example .env   # solo la primera vez; edita valores
python -m app.core.cli db-init
python -m app.core.cli serve
```

Si definiste `BRIDGE_API_TOKEN` en `.env`, añade en cada nodo HTTP de n8n el header:

- Nombre: `X-Bridge-Token`
- Valor: el mismo token de tu `.env`

## URLs desde el contenedor n8n

| Destino | URL en n8n |
|---------|------------|
| Puente Python | `http://host.docker.internal:8765` |
| Ollama | `http://host.docker.internal:11434` |
| Assets montados | `/data/assets/profile.md` (lectura en nodos de archivo) |
