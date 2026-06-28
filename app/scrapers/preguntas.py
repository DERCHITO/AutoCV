import re

MSG_PREGUNTAS_LABORUM = (
    "Esta oferta incluye preguntas de seleccion en Laborum "
    "(visibles al postular en el portal con sesion iniciada)."
)
MSG_SIN_PREGUNTAS = "(sin preguntas de seleccion disponibles)"

_PATRON_ORACION_PREGUNTA = re.compile(
    r"(?:^|[\n;.]\s*)(¿[^\n?]{4,}\?|(?:[A-ZÁÉÍÓÚÑ][^\n?]{9,}\?))",
    re.MULTILINE,
)
_PATRON_RUIDO = re.compile(
    r"\b(buscas empleo|iniciar sesion|crear cuenta|computrabajo|laborum|"
    r"get on board|publicidad|cookies|newsletter)\b",
    re.IGNORECASE,
)


def es_pregunta_valida(pregunta: str) -> bool:
    return not _PATRON_RUIDO.search(pregunta)


def deduplicar_preguntas(preguntas: list[str]) -> list[str]:
    """Elimina duplicados conservando el orden (case-insensitive)."""
    vistas: set[str] = set()
    unicas: list[str] = []
    for pregunta in preguntas:
        limpia = " ".join(pregunta.split())
        if len(limpia) < 10 or not es_pregunta_valida(limpia):
            continue
        clave = limpia.lower()
        if clave in vistas:
            continue
        vistas.add(clave)
        unicas.append(limpia)
    return unicas


def extraer_preguntas_de_texto(texto: str) -> list[str]:
    """Extrae oraciones interrogativas presentes en la descripcion u otro texto."""
    if not texto:
        return []

    candidatas: list[str] = []
    for linea in texto.splitlines():
        limpia = linea.strip().lstrip("-•*·").strip()
        if limpia.endswith("?") and len(limpia) >= 10:
            candidatas.append(limpia)

    for match in _PATRON_ORACION_PREGUNTA.finditer(texto):
        candidatas.append(match.group(1).strip())

    return deduplicar_preguntas(candidatas)


def completar_preguntas(
    preguntas: list[str],
    descripcion: str,
    *,
    incluye_preguntas_portal: bool = False,
    mensaje_portal: str = MSG_PREGUNTAS_LABORUM,
) -> list[str]:
    """Completa preguntas con texto de la descripcion o aviso del portal."""
    resultado = list(preguntas) if preguntas else extraer_preguntas_de_texto(descripcion)
    if not resultado and incluye_preguntas_portal:
        resultado = [mensaje_portal]
    return resultado
