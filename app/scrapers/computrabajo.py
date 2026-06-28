import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlencode

# Permite ejecutar: python app/scrapers/computrabajo.py
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import requests
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper
from app.scrapers.computrabajo_seleccion import (
    extraer_apply_url_desde_listado,
    obtener_preguntas_seleccion,
)
from app.scrapers.models import OfertaLaboral


class CompuTrabajoScraper(BaseScraper):
    """Scraper de ofertas de CompuTrabajo Chile vía listados HTML."""

    OFERTAS_POR_PAGINA = 20

    def __init__(self, url_base: str = "https://cl.computrabajo.com"):
        super().__init__(url_base)
        self.headers.update(
            {
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "es-CL,es;q=0.9",
            }
        )

    @staticmethod
    def _slug(texto: str) -> str:
        normalizado = unicodedata.normalize("NFKD", texto)
        ascii_text = normalizado.encode("ascii", "ignore").decode("ascii")
        ascii_text = ascii_text.lower().strip()
        return re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")

    def _construir_ruta(
        self,
        query: str | None,
        categoria: str | None,
        ciudad: str | None,
    ) -> str | None:
        if categoria and ciudad:
            return f"/empleos-de-{self._slug(categoria)}-en-{self._slug(ciudad)}"
        if categoria:
            return f"/empleos-de-{self._slug(categoria)}"
        if query and ciudad:
            return f"/trabajo-de-{self._slug(query)}-en-{self._slug(ciudad)}"
        if query:
            return f"/trabajo-de-{self._slug(query)}"
        return None

    def _obtener_html(self, ruta: str, pagina: int) -> str | None:
        params = {"p": pagina} if pagina > 1 else None
        url = f"{self.url_base}{ruta}"
        if params:
            url = f"{url}?{urlencode(params)}"

        try:
            respuesta = requests.get(url, headers=self.headers, timeout=20)
            respuesta.raise_for_status()
            return respuesta.text
        except requests.exceptions.RequestException as e:
            print(f"Error al consultar CompuTrabajo: {e}")
            return None

    def _ofertas_desde_listado(self, html: str) -> list[OfertaLaboral]:
        sopa = BeautifulSoup(html, "html.parser")
        ofertas: list[OfertaLaboral] = []

        for enlace in sopa.select("h2 a"):
            titulo = enlace.get_text(strip=True)
            href = enlace.get("href", "").split("#")[0]
            if not titulo or not href:
                continue
            url = href if href.startswith("http") else f"{self.url_base}{href}"
            ofertas.append(OfertaLaboral(titulo=titulo, url=url))

        return ofertas

    def _obtener_descripcion(self, url: str) -> str:
        try:
            respuesta = requests.get(url, headers=self.headers, timeout=20)
            respuesta.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener detalle CompuTrabajo: {e}")
            return ""

        sopa = BeautifulSoup(respuesta.text, "html.parser")

        for heading in sopa.find_all(["h2", "h3", "strong"]):
            texto = heading.get_text(strip=True).lower()
            if "descripci" in texto and "oferta" in texto:
                contenedor = heading.find_parent("div")
                if contenedor:
                    return contenedor.get_text("\n", strip=True)

        for selector in (".bWord", ".box_detail"):
            elementos = sopa.select(selector)
            for elemento in elementos:
                texto = elemento.get_text("\n", strip=True)
                if len(texto) > 120 and "Buscar empresas" not in texto:
                    return texto

        return ""

    def extraer_ofertas(
        self,
        query: str | None = None,
        categoria: str | None = None,
        ciudad: str | None = None,
        page: int = 1,
        max_resultados: int | None = None,
    ) -> list[OfertaLaboral]:
        """Devuelve ofertas con titulo y descripcion para la consulta."""
        ruta = self._construir_ruta(query, categoria, ciudad)
        if not ruta:
            print("Error: debes indicar `query` o `categoria`.")
            return []

        ofertas: list[OfertaLaboral] = []
        vistos: set[str] = set()
        pagina = max(page, 1)

        while True:
            if max_resultados is not None and len(ofertas) >= max_resultados:
                break

            html = self._obtener_html(ruta, pagina)
            if not html:
                break

            candidatos = self._ofertas_desde_listado(html)
            if not candidatos:
                break

            agregados = 0
            for candidato in candidatos:
                if candidato.titulo in vistos:
                    continue
                vistos.add(candidato.titulo)

                descripcion = self._obtener_descripcion(candidato.url) if candidato.url else ""
                apply_url = extraer_apply_url_desde_listado(html, candidato.titulo)
                preguntas = obtener_preguntas_seleccion(
                    apply_url,
                    titulo=candidato.titulo,
                    referer=f"{self.url_base}{ruta}",
                )
                ofertas.append(
                    OfertaLaboral(
                        titulo=candidato.titulo,
                        descripcion=descripcion,
                        url=candidato.url,
                        preguntas=preguntas,
                    )
                )
                agregados += 1

                if max_resultados is not None and len(ofertas) >= max_resultados:
                    break

            if max_resultados is not None and len(ofertas) >= max_resultados:
                break
            if agregados == 0 or len(candidatos) < self.OFERTAS_POR_PAGINA:
                break
            pagina += 1

        if max_resultados is not None:
            return ofertas[:max_resultados]
        return ofertas

    def extraer_titulos(
        self,
        query: str | None = None,
        categoria: str | None = None,
        ciudad: str | None = None,
        page: int = 1,
        max_resultados: int | None = None,
    ) -> list[str]:
        return [
            o.titulo
            for o in self.extraer_ofertas(
                query=query,
                categoria=categoria,
                ciudad=ciudad,
                page=page,
                max_resultados=max_resultados,
            )
        ]

    def extraer_datos(self, endpoint: str = "") -> list[str]:
        if endpoint.startswith("categoria:"):
            categoria = endpoint.removeprefix("categoria:").strip()
            return self.extraer_titulos(categoria=categoria, query=None)
        if endpoint.startswith("query:"):
            query = endpoint.removeprefix("query:").strip()
            return self.extraer_titulos(query=query, categoria=None)
        if endpoint:
            return self.extraer_titulos(query=endpoint, categoria=None)
        return []


if __name__ == "__main__":
    print("Usa el orquestador: python app/scrapers/base.py")
