# AutoCV — Entorno de desarrollo local

Arquitectura híbrida: **Python + n8n + SQLite + Playwright**, 100 % local y open-source (sin AWS, Azure, GCP, Redis, Celery ni Kafka).

## Estructura del monorepo

```
├── app/
│   ├── core/
│   ├── database/
│   └── scrapers/
├── assets/
├── database/
├── logs/
├── n8n/
├── scripts/
└── tests/
```

## 1. Python (venv + dependencias + Playwright)

Desde la raíz del repositorio en **PowerShell**:

```powershell
cd c:\Users\crisb\Documents\GitHub\AutoCV

# Crear entorno virtual
python -m venv .venv

# Activar (cada nueva terminal)
.\.venv\Scripts\Activate.ps1

# Instalar dependencias
python -m pip install --upgrade pip
pip install -r requirements.txt

# Navegadores y drivers nativos de Playwright
playwright install
```

O en un solo paso:

```powershell
.\scripts\setup.ps1
```

## 1.1 Búsqueda de ofertas (scrapers)

Ver guía completa: [BUSQUEDA_EMPLEOS.md](BUSQUEDA_EMPLEOS.md)

```powershell
.\.venv\Scripts\Activate.ps1
python app\scrapers\base.py desarrollador 10
```

## 2. Assets

| Archivo | Uso |
|---------|-----|
| `assets/keywords.json` | Palabras clave para filtrar ofertas |
| `assets/profile.md` | Perfil en Markdown para el LLM local |
| `assets/mi_cv.pdf` | Tu CV en PDF (cópialo manualmente; está en `.gitignore`) |

```powershell
Copy-Item "C:\ruta\a\tu\CV.pdf" ".\assets\mi_cv.pdf"
```

## 3. n8n (self-hosted con Docker)

Requisito: [Docker Desktop](https://www.docker.com/products/docker-desktop/) en Windows.

```powershell
cd n8n
docker compose up -d
```

- UI: http://localhost:5678  
- Datos persistentes: volumen Docker `n8n_data`  
- Carpeta `assets/` montada en solo lectura como `/data/assets` dentro del contenedor  

Detener:

```powershell
docker compose down
```

Ver logs:

```powershell
docker compose logs -f n8n
```

## 4. Ollama (LLM local: Llama 3 / Qwen)

1. Instalar desde https://ollama.com/download (Windows).
2. Verificar que el servicio esté activo:

```powershell
ollama --version
ollama list
```

3. Descargar modelos (elige uno o ambos):

```powershell
ollama pull llama3
ollama pull qwen2.5
```

4. Probar inferencia:

```powershell
ollama run llama3 "Resume en una frase qué es un ingeniero de plataforma."
```

API local (para n8n o Python): `http://localhost:11434`

Ejemplo desde PowerShell:

```powershell
Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get
```

En **n8n**, usa el nodo HTTP Request o un nodo de comunidad compatible apuntando a `http://host.docker.internal:11434` (desde Docker en Windows) o `http://localhost:11434` si n8n corre fuera de Docker.

## 5. Variables de entorno (`.env`)

```powershell
Copy-Item .env.example .env
# Edita .env con tus credenciales (nunca lo subas a Git)
pip install -r requirements.txt   # incluye python-dotenv
```

| Variable | Uso |
|----------|-----|
| `DATABASE_URL` | SQLite en `database/autocv.sqlite` |
| `BRIDGE_API_PORT` | Puerto API para n8n (default `8765`) |
| `BRIDGE_API_TOKEN` | Opcional: header `X-Bridge-Token` |
| `OLLAMA_BASE_URL` | LLM local |

## 6. Base de datos (conexión Python)

Código en `app/database/`; archivo en `database/autocv.sqlite`.

```powershell
python -m app.core.cli db-init
python -m app.core.cli health
```

## 7. Puente n8n ↔ Python

API HTTP mínima en `app/core/server.py`:

```powershell
python -m app.core.cli serve
# o: .\scripts\start-bridge.ps1
```

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Estado + SQLite |
| POST | `/db/init` | Crear tablas |
| GET | `/applications` | Listar postulaciones |

Desde n8n (Docker): `http://host.docker.internal:8765/health`

CLI alternativo (sin HTTP):

```powershell
python -m app.core.cli health
python -m app.core.cli applications
```

## 8. Workflows n8n exportados

Importa los JSON desde `n8n/workflows/` (ver `n8n/README.md`).

## 9. Orden recomendado al arrancar el día

1. `.\.venv\Scripts\Activate.ps1`
2. `Copy-Item .env.example .env` (solo la primera vez) y editar
3. `python -m app.core.cli serve` (puente HTTP)
4. `cd n8n; docker compose up -d`
5. Comprobar Ollama: `ollama list`
6. Importar/ejecutar workflows en http://localhost:5678

## Restricciones cumplidas

- Sin servicios cloud de pago ni colas distribuidas (Redis, Celery, Kafka).
- SQLite en `database/` para persistencia.
- Automatización web con Playwright instalado localmente.
