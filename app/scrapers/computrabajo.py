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


class CompuTrabajoScraper(BaseScraper):
    """Scraper de ofertas de CompuTrabajo Chile vía listados HTML."""

    LIMITE_DEFAULT = 15
    QUERY_DEFAULT = "desarrollador"
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
    ) -> str:
        if categoria and ciudad:
            return f"/empleos-de-{self._slug(categoria)}-en-{self._slug(ciudad)}"
        if categoria:
            return f"/empleos-de-{self._slug(categoria)}"
        if query and ciudad:
            return f"/trabajo-de-{self._slug(query)}-en-{self._slug(ciudad)}"
        if query:
            return f"/trabajo-de-{self._slug(query)}"
        return f"/trabajo-de-{self._slug(self.QUERY_DEFAULT)}"

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

    def _titulos_desde_html(self, html: str, limite: int) -> list[str]:
        sopa = BeautifulSoup(html, "html.parser")
        titulos: list[str] = []
        vistos: set[str] = set()

        for enlace in sopa.select("h2 a"):
            titulo = enlace.get_text(strip=True)
            if not titulo or titulo in vistos:
                continue
            vistos.add(titulo)
            titulos.append(titulo)
            if len(titulos) >= limite:
                break

        return titulos

    def extraer_titulos(
        self,
        limite: int = LIMITE_DEFAULT,
        query: str | None = QUERY_DEFAULT,
        categoria: str | None = None,
        ciudad: str | None = None,
        page: int = 1,
    ) -> list[str]:
        """Devuelve hasta `limite` títulos de ofertas publicadas en CompuTrabajo."""
        if limite < 1:
            return []

        ruta = self._construir_ruta(query, categoria, ciudad)
        titulos: list[str] = []
        pagina = max(page, 1)

        while len(titulos) < limite:
            html = self._obtener_html(ruta, pagina)
            if not html:
                break

            nuevos = self._titulos_desde_html(html, limite - len(titulos))
            if not nuevos:
                break

            titulos.extend(nuevos)

            if len(nuevos) < self.OFERTAS_POR_PAGINA:
                break
            pagina += 1

        return titulos[:limite]

    def extraer_datos(self, endpoint: str = "") -> list[str]:
        if endpoint.startswith("categoria:"):
            categoria = endpoint.removeprefix("categoria:").strip()
            return self.extraer_titulos(categoria=categoria, query=None)
        if endpoint.startswith("query:"):
            query = endpoint.removeprefix("query:").strip()
            return self.extraer_titulos(query=query, categoria=None)
        if endpoint:
            return self.extraer_titulos(query=endpoint, categoria=None)
        return self.extraer_titulos()


if __name__ == "__main__":
    print("--- Scraper CompuTrabajo (15 ofertas, query desarrollador) ---")

    scraper = CompuTrabajoScraper()
    titulos = scraper.extraer_titulos(limite=15, query="desarrollador")

    if not titulos:
        print("No se encontraron ofertas.")
    else:
        for i, titulo in enumerate(titulos, start=1):
            print(f"{i:2}. {titulo}")
