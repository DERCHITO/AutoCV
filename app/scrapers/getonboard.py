import sys
from pathlib import Path

# Permite ejecutar: python app/scrapers/getonboard.py
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import requests

from app.scrapers.base import BaseScraper


class GetOnBoardScraper(BaseScraper):
    """Scraper de ofertas de Get on Board vía API pública v0."""

    API_PREFIX = "/api/v0"
    LIMITE_DEFAULT = 15
    CATEGORIA_DEFAULT = "programacion"
    PER_PAGE_MAX = 120

    def __init__(self, url_base: str = "https://www.getonbrd.com", lang: str = "es"):
        super().__init__(url_base)
        self.lang = lang
        self.headers.update(
            {
                "Accept": "application/json",
                "Accept-Language": lang,
            }
        )

    def _get_json(self, endpoint: str, params: dict | None = None) -> dict | None:
        url = f"{self.url_base}{self.API_PREFIX}{endpoint}"
        try:
            respuesta = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=20,
            )
            respuesta.raise_for_status()
            return respuesta.json()
        except requests.exceptions.RequestException as e:
            print(f"Error al consultar Get on Board: {e}")
            return None
        except ValueError:
            print("Error: Get on Board devolvio una respuesta no JSON.")
            return None

    def _titulos_desde_data(self, data: list, limite: int) -> list[str]:
        titulos: list[str] = []
        for oferta in data:
            titulo = oferta.get("attributes", {}).get("title", "").strip()
            if titulo:
                titulos.append(titulo)
            if len(titulos) >= limite:
                break
        return titulos

    def extraer_titulos(
        self,
        limite: int = LIMITE_DEFAULT,
        categoria: str | None = CATEGORIA_DEFAULT,
        query: str | None = None,
        page: int = 1,
    ) -> list[str]:
        """Devuelve hasta `limite` títulos de ofertas publicadas en Get on Board."""
        if limite < 1:
            return []

        titulos: list[str] = []
        pagina = max(page, 1)

        while len(titulos) < limite:
            faltantes = limite - len(titulos)
            per_page = min(faltantes, self.PER_PAGE_MAX)

            if query:
                params = {
                    "query": query,
                    "page": pagina,
                    "per_page": per_page,
                    "lang": self.lang,
                }
                payload = self._get_json("/search/jobs", params)
            elif categoria:
                params = {
                    "page": pagina,
                    "per_page": per_page,
                    "lang": self.lang,
                }
                payload = self._get_json(f"/categories/{categoria}/jobs", params)
            else:
                print("Error: debes indicar `categoria` o `query`.")
                return titulos

            if not payload:
                break

            data = payload.get("data", [])
            if not data:
                break

            titulos.extend(self._titulos_desde_data(data, limite))

            meta = payload.get("meta", {})
            total_pages = meta.get("total_pages", pagina)
            if pagina >= total_pages:
                break
            pagina += 1

        return titulos[:limite]

    def extraer_datos(self, endpoint: str = "") -> list[str]:
        if endpoint.startswith("search:"):
            query = endpoint.removeprefix("search:").strip()
            return self.extraer_titulos(query=query, categoria=None)
        if endpoint:
            return self.extraer_titulos(categoria=endpoint)
        return self.extraer_titulos()


if __name__ == "__main__":
    print("--- Scraper Get on Board (15 ofertas, categoria programacion) ---")

    scraper = GetOnBoardScraper()
    titulos = scraper.extraer_titulos(limite=15, categoria="programacion")

    if not titulos:
        print("No se encontraron ofertas.")
    else:
        for i, titulo in enumerate(titulos, start=1):
            print(f"{i:2}. {titulo}")
