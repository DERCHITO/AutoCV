import os
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from app.scrapers.models import OfertaLaboral
from app.scrapers.preguntas import MSG_SIN_PREGUNTAS


class BaseScraper:
    def __init__(self, url_base):
        self.url_base = url_base
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

    def obtener_sopa(self, endpoint=""):
        url_completa = f"{self.url_base}{endpoint}"

        try:
            respuesta = requests.get(url_completa, headers=self.headers, timeout=10)
            respuesta.raise_for_status()

            sopa = BeautifulSoup(respuesta.text, "html.parser")
            return sopa

        except requests.exceptions.RequestException as e:
            print(f"Error al conectar con {url_completa}: {e}")
            return None

    def extraer_datos(self, endpoint=""):
        sopa = self.obtener_sopa(endpoint)
        if not sopa:
            return []

        resultados = []

        titulos = sopa.find_all("h2", class_="titulo")

        for t in titulos:
            resultados.append(t.text.strip())

        return resultados


@dataclass
class PerfilBusqueda:
    """Puesto al que postulas + nivel de experiencia + filtros opcionales."""

    rol: str = "desarrollador"
    nivel: str = "junior"
    extras: list[str] = field(default_factory=list)


class ScraperOrchestrator:
    """Ejecuta Laborum, Get on Board y CompuTrabajo y agrupa los resultados."""

    FUENTES = ("laborum", "getonboard", "computrabajo")

    CONSULTAS_POR_DEFECTO: dict[str, list[str | None]] = {
        "laborum": [""],
        "getonboard": [None],
        "computrabajo": ["desarrollador"],
    }

    ETIQUETAS = {
        "laborum": "Laborum",
        "getonboard": "Get on Board",
        "computrabajo": "CompuTrabajo",
    }

    SINONIMOS_ROL: dict[str, list[str]] = {
        "desarrollador": [
            "desarrollador",
            "developer",
            "programador",
            "software",
            "fullstack",
            "full stack",
            "full-stack",
            "backend",
            "front end",
            "frontend",
            "front-end",
            "ingeniero",
            " dev",
            "dev ",
        ],
    }

    _PATRON_JUNIOR = re.compile(
        r"\b(junior|jr\.?|trainee|practicante|pr[aá]ctica|entry[\s-]?level|"
        r"sin experiencia|0[\s-]1 a[nñ]os|0[\s-]2 a[nñ]os)\b",
        re.IGNORECASE,
    )
    _PATRON_SEMI = re.compile(
        r"\b(semi[\s-]?senior|semi[\s-]?sr|ssr|mid[\s-]?level)\b",
        re.IGNORECASE,
    )
    _PATRON_SENIOR = re.compile(
        r"\b(senior|sr\.?|lead|l[ií]der|jefe|architect|arquitecto|"
        r"manager|principal|expert|especialista)\b",
        re.IGNORECASE,
    )

    def __init__(self, limite_por_fuente: int = 15, verbose: bool = True):
        from app.scrapers.computrabajo import CompuTrabajoScraper
        from app.scrapers.getonboard import GetOnBoardScraper
        from app.scrapers.laborum import LaborumScraper

        self.limite_por_fuente = limite_por_fuente
        self.verbose = verbose
        self._scrapers = {
            "laborum": LaborumScraper(),
            "getonboard": GetOnBoardScraper(),
            "computrabajo": CompuTrabajoScraper(),
        }

    @staticmethod
    def _normalizar_texto(texto: str) -> str:
        normalizado = unicodedata.normalize("NFKD", texto)
        ascii_text = normalizado.encode("ascii", "ignore").decode("ascii")
        return ascii_text.lower()

    @classmethod
    def _rol_en_titulo(cls, titulo: str, rol: str) -> bool:
        t = cls._normalizar_texto(titulo)
        rol_l = cls._normalizar_texto(rol)
        terminos = cls.SINONIMOS_ROL.get(rol_l, [rol_l])
        return any(termino in t for termino in terminos)

    @classmethod
    def _coincide_nivel(cls, titulo: str, perfil: PerfilBusqueda) -> bool:
        nivel = perfil.nivel
        if nivel == "cualquiera":
            return True

        t = cls._normalizar_texto(titulo)
        es_junior = bool(cls._PATRON_JUNIOR.search(t))
        es_semi = bool(cls._PATRON_SEMI.search(t))
        es_senior = bool(cls._PATRON_SENIOR.search(t))
        tiene_rol = cls._rol_en_titulo(titulo, perfil.rol)

        if nivel == "junior":
            if es_senior and not es_junior:
                return False
            if es_junior:
                return True
            return tiene_rol and not es_senior and not es_semi

        if nivel == "semi-senior":
            if es_junior and not es_semi:
                return False
            if es_semi:
                return True
            return tiene_rol and es_senior is False

        if nivel == "senior":
            if es_junior and not es_senior:
                return False
            return es_senior or (tiene_rol and not es_junior)

        return True

    @classmethod
    def construir_consultas(cls, perfil: PerfilBusqueda) -> list[str]:
        """Arma consultas: primero el puesto con nivel, luego el puesto solo y extras."""
        rol = perfil.rol.strip()
        consultas: list[str] = []

        if perfil.nivel == "junior":
            consultas.extend([f"{rol} junior", f"{rol} jr"])
        elif perfil.nivel == "semi-senior":
            consultas.extend([f"{rol} semi senior", f"{rol} ssr"])
        elif perfil.nivel == "senior":
            consultas.extend([f"{rol} senior", f"{rol} sr"])

        consultas.append(rol)

        for extra in perfil.extras:
            consultas.append(f"{rol} {extra}")
            if perfil.nivel == "junior":
                consultas.append(f"{rol} junior {extra}")

        vistos: set[str] = set()
        unicas: list[str] = []
        for consulta in consultas:
            clave = consulta.lower()
            if clave not in vistos:
                vistos.add(clave)
                unicas.append(consulta)
        return unicas

    def _log(self, mensaje: str) -> None:
        if self.verbose:
            print(mensaje, flush=True)

    def _consultar_scraper(
        self,
        fuente: str,
        palabra: str | None,
        max_resultados: int,
    ) -> list[OfertaLaboral]:
        scraper = self._scrapers[fuente]

        if fuente == "laborum":
            return scraper.extraer_ofertas(
                query=palabra or "",
                max_resultados=max_resultados,
            )

        if fuente == "getonboard":
            if palabra:
                return scraper.extraer_ofertas(
                    query=palabra,
                    categoria=None,
                    max_resultados=max_resultados,
                )
            return scraper.extraer_ofertas(
                categoria="programacion",
                max_resultados=max_resultados,
            )

        if palabra:
            return scraper.extraer_ofertas(
                query=palabra,
                categoria=None,
                max_resultados=max_resultados,
            )
        return scraper.extraer_ofertas(
            categoria="informatica",
            query=None,
            max_resultados=max_resultados,
        )

    def extraer_de_fuente(
        self,
        fuente: str,
        perfil: PerfilBusqueda | None = None,
        palabras: list[str] | None = None,
    ) -> list[OfertaLaboral]:
        if fuente not in self._scrapers:
            raise ValueError(f"Fuente desconocida: {fuente}. Usa: {', '.join(self.FUENTES)}")

        if perfil:
            consultas = self.construir_consultas(perfil)
            filtrar_nivel = perfil.nivel != "cualquiera"
        else:
            consultas = palabras if palabras else self.CONSULTAS_POR_DEFECTO[fuente]
            filtrar_nivel = False

        acumulado: list[OfertaLaboral] = []
        vistos: set[str] = set()
        buffer = self.limite_por_fuente * 4 if filtrar_nivel else self.limite_por_fuente

        self._log(f"\n>> {self.ETIQUETAS[fuente]}")

        for palabra in consultas:
            if len(acumulado) >= self.limite_por_fuente:
                break

            faltantes = min(buffer, self.limite_por_fuente * 4)
            etiqueta = palabra if palabra else "(general)"
            self._log(f"   Buscando: {etiqueta} ...")

            for oferta in self._consultar_scraper(fuente, palabra, faltantes):
                if oferta.titulo in vistos:
                    continue
                if perfil and filtrar_nivel and not self._coincide_nivel(oferta.titulo, perfil):
                    continue
                vistos.add(oferta.titulo)
                acumulado.append(oferta)
                if len(acumulado) >= self.limite_por_fuente:
                    break

        return acumulado

    def buscar(
        self,
        perfil: PerfilBusqueda | None = None,
        palabras: list[str] | None = None,
    ) -> dict[str, list[OfertaLaboral]]:
        """Consulta las tres fuentes y devuelve ofertas agrupadas por portal."""
        return {
            fuente: self.extraer_de_fuente(fuente, perfil=perfil, palabras=palabras)
            for fuente in self.FUENTES
        }

    @staticmethod
    def _seguro_para_terminal(texto: str) -> str:
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        return texto.encode(encoding, errors="replace").decode(encoding)

    @staticmethod
    def imprimir_resultados(
        resultados: dict[str, list[OfertaLaboral]],
        perfil: PerfilBusqueda | None = None,
        palabras: list[str] | None = None,
        limite_por_fuente: int | None = None,
    ) -> None:
        if perfil:
            extras = f", extras: {', '.join(perfil.extras)}" if perfil.extras else ""
            titulo_busqueda = (
                f" (puesto: {perfil.rol}, nivel: {perfil.nivel}{extras})"
            )
        elif palabras:
            titulo_busqueda = f" (filtros: {', '.join(palabras)})"
        else:
            titulo_busqueda = " (sin filtros; busqueda general por portal)"

        limite_txt = f", max {limite_por_fuente} por portal" if limite_por_fuente else ""
        print(f"--- Busqueda en portales de empleo{titulo_busqueda}{limite_txt} ---\n")

        for fuente in ScraperOrchestrator.FUENTES:
            ofertas = resultados.get(fuente, [])
            print(f"## {ScraperOrchestrator.ETIQUETAS[fuente]} ({len(ofertas)} ofertas)")

            if not ofertas:
                print("   No se encontraron ofertas.\n")
                continue

            for i, oferta in enumerate(ofertas, start=1):
                titulo = ScraperOrchestrator._seguro_para_terminal(oferta.titulo)
                print(f"{i}-{titulo}")
                descripcion = oferta.descripcion.strip() or "(sin descripcion disponible)"
                print(ScraperOrchestrator._seguro_para_terminal(descripcion))
                print()
                print("Preguntas para el cargo:")
                if oferta.preguntas:
                    for pregunta in oferta.preguntas:
                        linea = f"- {pregunta}"
                        print(ScraperOrchestrator._seguro_para_terminal(linea))
                else:
                    print(MSG_SIN_PREGUNTAS)
                print()
            print()


def _parsear_palabras(texto: str) -> list[str]:
    palabras: list[str] = []
    for parte in texto.replace(";", ",").split(","):
        for palabra in parte.split():
            limpia = palabra.strip()
            if limpia:
                palabras.append(limpia)
    return palabras


def _normalizar_nivel(texto: str) -> str:
    clave = texto.lower().strip()
    mapa = {
        "jr": "junior",
        "junior": "junior",
        "semi": "semi-senior",
        "semi-senior": "semi-senior",
        "semisenior": "semi-senior",
        "ssr": "semi-senior",
        "sr": "senior",
        "senior": "senior",
        "cualquiera": "cualquiera",
        "todos": "cualquiera",
    }
    return mapa.get(clave, clave)


NIVELES_VALIDOS = {"junior", "semi-senior", "senior", "cualquiera"}


def _parsear_argumentos(argv: list[str]) -> tuple[PerfilBusqueda | None, list[str] | None, int]:
    """Modos:
    - base.py --rol desarrollador --nivel junior python 10
    - base.py desarrollador python 10  (rol + extras, nivel junior por defecto)
    - base.py python,remoto 10  (modo legacy: solo palabras clave)
    """
    if not argv:
        return None, None, 15

    args = list(argv)
    limite = 15
    perfil = PerfilBusqueda()
    modo_perfil = False

    if args[-1].isdigit():
        limite = int(args.pop())

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--rol" and i + 1 < len(args):
            perfil.rol = args[i + 1]
            modo_perfil = True
            i += 2
            continue
        if arg == "--nivel" and i + 1 < len(args):
            perfil.nivel = _normalizar_nivel(args[i + 1])
            modo_perfil = True
            i += 2
            continue
        if arg.startswith("--rol="):
            perfil.rol = arg.split("=", 1)[1]
            modo_perfil = True
            i += 1
            continue
        if arg.startswith("--nivel="):
            perfil.nivel = _normalizar_nivel(arg.split("=", 1)[1])
            modo_perfil = True
            i += 1
            continue
        i += 1

    restantes = [a for a in args if not a.startswith("--")]

    if modo_perfil:
        perfil.extras = []
        for token in restantes:
            nivel = _normalizar_nivel(token)
            if nivel in NIVELES_VALIDOS:
                perfil.nivel = nivel
            elif token.lower() != perfil.rol.lower():
                perfil.extras.extend(_parsear_palabras(token))
        if perfil.nivel not in NIVELES_VALIDOS:
            perfil.nivel = "junior"
        return perfil, None, limite

    if len(restantes) == 1:
        tokens = _parsear_palabras(restantes[0])
    else:
        tokens = restantes

    if not tokens:
        return None, None, limite

    primer_nivel = _normalizar_nivel(tokens[0])
    if primer_nivel in NIVELES_VALIDOS and len(tokens) == 1:
        return None, tokens, limite

    if _normalizar_nivel(tokens[0]) not in NIVELES_VALIDOS and tokens[0].lower() in {
        "desarrollador",
        "developer",
        "programador",
    }:
        perfil.rol = tokens[0]
        perfil.nivel = "junior"
        perfil.extras = []
        for token in tokens[1:]:
            nivel = _normalizar_nivel(token)
            if nivel in NIVELES_VALIDOS:
                perfil.nivel = nivel
            else:
                perfil.extras.extend(_parsear_palabras(token))
        return perfil, None, limite

    return None, tokens, limite


def solicitar_perfil() -> PerfilBusqueda:
    print("Puesto al que quieres postular:")
    print("  Ejemplo: desarrollador, programador, analista")
    rol = input("Puesto [desarrollador]> ").strip() or "desarrollador"

    print("\nNivel de experiencia:")
    print("  junior | semi-senior | senior | cualquiera")
    nivel_raw = input("Nivel [junior]> ").strip() or "junior"
    nivel = _normalizar_nivel(nivel_raw)
    if nivel not in NIVELES_VALIDOS:
        nivel = "junior"

    print("\nPalabras extra opcionales (python, remoto, etc.):")
    print("  Separadas por coma. Enter vacio = ninguna")
    extras_raw = input("Extras> ").strip()
    extras = _parsear_palabras(extras_raw)

    return PerfilBusqueda(rol=rol, nivel=nivel, extras=extras)


def solicitar_limite() -> int:
    print("\nCuantas ofertas quieres ver por portal?")
    while True:
        texto = input("Cantidad> ").strip()
        if not texto:
            print("  Ingresa un numero mayor a 0.")
            continue
        try:
            limite = int(texto)
        except ValueError:
            print("  Valor invalido. Usa un numero entero.")
            continue
        if limite < 1:
            print("  El minimo es 1.")
            continue
        return limite


def enviar_a_n8n(resultados: dict[str, list[OfertaLaboral]]) -> None:
    URL = os.environ.get("URL_WEBHOOK_N8N")

    if not URL:
        print("\n[AVISO]: No se configuró la variable 'URL_WEBHOOK_N8N' en el archivo .env.")
        print("Se omitirá el envío de datos a n8n.")
        return

    lista_trabajos = []
    for fuente, ofertas in resultados.items():
        for oferta in ofertas:
            lista_trabajos.append(
                {
                    "fuente": fuente,
                    "titulo": oferta.titulo,
                    "descripcion": oferta.descripcion,
                    "preguntas": oferta.preguntas,
                    "url": oferta.url,
                }
            )

    payload = {
        "total_ofertas": len(lista_trabajos),
        "trabajos": lista_trabajos
    }

    try:
        print(f"\n--- Enviando {len(lista_trabajos)} ofertas a tu n8n local ---")
        respuesta = requests.post(URL, json=payload, timeout=15)
        respuesta.raise_for_status()
        print("¡Datos enviados exitosamente a n8n!")
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar datos a n8n: {e}")


if __name__ == "__main__":
    load_dotenv()

    if len(sys.argv) > 1:
        perfil, palabras, limite = _parsear_argumentos(sys.argv[1:])
    else:
        print("=== AutoCV — busqueda de ofertas ===\n")
        perfil = solicitar_perfil()
        limite = solicitar_limite()
        palabras = None
        print()

    if perfil:
        extras_txt = f", extras: {', '.join(perfil.extras)}" if perfil.extras else ""
        print(
            f"Perfil: {perfil.rol} ({perfil.nivel}){extras_txt} | "
            f"{limite} ofertas por portal\n",
            flush=True,
        )
    elif palabras:
        print(f"Filtros: {', '.join(palabras)} | {limite} ofertas por portal\n", flush=True)

    orchestrator = ScraperOrchestrator(limite_por_fuente=limite)
    resultados = orchestrator.buscar(perfil=perfil, palabras=palabras)

    ScraperOrchestrator.imprimir_resultados(
        resultados,
        perfil=perfil,
        palabras=palabras,
        limite_por_fuente=limite,
    )
    
    print("--- Guardando ofertas en la base de datos ---")
    for fuente, ofertas in resultados.items():
        for oferta in ofertas:
            print("saltado")
            ##insertar_fila_trabajo(
            ##    titulo=oferta.titulo,
            ##    compania="Desconocida",
            ##    ubicacion="",
            ##    rango_salarial="",
            ##    descripcion=oferta.descripcion,
            ##    url=oferta.url,
            ##    estado=0,
            ##    fecha_creacion="",
            ##    id_fuente=0,
            ##)


    
    enviar_a_n8n(resultados)
