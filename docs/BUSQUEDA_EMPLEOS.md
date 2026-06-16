# AutoCV — Búsqueda de ofertas (scrapers)

Guía para buscar empleo en **Laborum**, **Get on Board** y **CompuTrabajo** desde la terminal.

## Requisitos

1. Entorno virtual activo (debes ver `(.venv)` al inicio de la línea):

```powershell
cd C:\Users\crisb\OneDrive\Documentos\GitHub\AutoCV
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea el script, usa:

```powershell
.\.venv\Scripts\python.exe app\scrapers\base.py
```

2. Dependencias instaladas (`.\scripts\setup.ps1`).

## Orquestador (recomendado)

El punto de entrada principal es `app/scrapers/base.py`. Consulta los tres portales, aplica filtros de puesto y nivel, y muestra los resultados agrupados por sitio.

```powershell
python app\scrapers\base.py
```

## Modo interactivo

Sin argumentos, el orquestador pregunta:

| Paso | Pregunta | Ejemplo |
|------|----------|---------|
| 1 | Puesto al que postulas | `desarrollador` |
| 2 | Nivel de experiencia | `junior` |
| 3 | Palabras extra (opcional) | `python, remoto` |
| 4 | Cantidad por portal | `10` |

Ejemplo de sesión:

```
=== AutoCV — busqueda de ofertas ===

Puesto [desarrollador]> desarrollador
Nivel [junior]> junior
Extras> python
Cantidad> 10
```

## Modo línea de comandos

### Desarrollador junior (caso más común)

Busca puestos de **desarrollador** filtrando ofertas aptas para perfil **junior** (excluye senior, lead, arquitecto, etc.):

```powershell
python app\scrapers\base.py desarrollador 10
```

- `desarrollador` → puesto al que postulas
- `10` → cantidad de ofertas **por portal** (último número)

### Con palabras extra

```powershell
python app\scrapers\base.py --rol desarrollador --nivel junior python 10
```

También puedes separar extras con coma:

```powershell
python app\scrapers\base.py --rol desarrollador --nivel junior "python, remoto" 10
```

### Otros niveles

```powershell
python app\scrapers\base.py --rol desarrollador --nivel semi-senior 10
python app\scrapers\base.py --rol desarrollador --nivel senior 10
python app\scrapers\base.py --rol desarrollador --nivel cualquiera 10
```

| Nivel | Qué incluye |
|-------|-------------|
| `junior` | Jr, trainee, practicante; dev sin etiqueta senior |
| `semi-senior` | Semi senior, SSR |
| `senior` | Senior, lead, arquitecto, manager |
| `cualquiera` | Sin filtro de nivel |

### Modo legacy (solo palabras clave)

Si no indicas puesto ni nivel, puedes pasar palabras sueltas:

```powershell
python app\scrapers\base.py "python, remoto" 10
python app\scrapers\base.py python remoto 10
```

## Cómo funciona el filtro junior

1. **Consultas** en cada portal: `desarrollador junior`, `desarrollador jr`, `desarrollador`, etc.
2. **Filtrado** sobre los títulos:
   - ✅ Incluye: junior, jr, practicante, puestos de dev sin marca senior
   - ❌ Excluye: senior, sr, lead, líder, arquitecto, manager

## Salida esperada

```
Perfil: desarrollador (junior) | 10 ofertas por portal

>> Laborum
   Buscando: desarrollador junior ...
...

--- Busqueda en portales de empleo (puesto: desarrollador, nivel: junior), max 10 por portal ---

## Laborum (10 ofertas)
   1. ...
## Get on Board (10 ofertas)
   1. ...
## CompuTrabajo (10 ofertas)
   1. ...
```

## Scrapers individuales

Cada portal tiene su propio módulo. Úsalos solo para pruebas; la búsqueda con filtros la maneja `base.py`.

| Portal | Archivo | Comando |
|--------|---------|---------|
| Laborum | `app/scrapers/laborum.py` | Redirige al orquestador |
| Get on Board | `app/scrapers/getonboard.py` | Redirige al orquestador |
| CompuTrabajo | `app/scrapers/computrabajo.py` | Redirige al orquestador |

```powershell
python app\scrapers\base.py desarrollador 15
```

## Errores frecuentes

### `ModuleNotFoundError: No module named 'requests'`

Estás usando el Python del sistema, no el del venv. Activa `.venv` o usa:

```powershell
.\.venv\Scripts\python.exe app\scrapers\base.py desarrollador 10
```

### El script no hace nada / tarda mucho

- Debes ejecutar con `python` delante: `python app\scrapers\base.py` (no solo la ruta del archivo).
- Con varias palabras clave puede tardar 15–30 s; verás mensajes `>> Laborum`, `Buscando: ...`.

### PowerShell no activa el venv

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

O usa CMD: `.venv\Scripts\activate.bat`

## Resumen rápido

```powershell
# Activar entorno
.\.venv\Scripts\Activate.ps1

# Buscar desarrollador junior (10 por portal)
python app\scrapers\base.py desarrollador 10

# Con python y modo interactivo
python app\scrapers\base.py
```
