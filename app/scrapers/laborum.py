import sys
from pathlib import Path

# Permite ejecutar: python app/scrapers/laborum.py
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import requests

from app.scrapers.base import BaseScraper


class LaborumScraper(BaseScraper):
    """Scraper de ofertas de Laborum Chile vía API interna searchV2."""

    SITE_ID = "BMCL"
    LIMITE_DEFAULT = 15

    def __init__(self, url_base: str = "https://www.laborum.cl"):
        super().__init__(url_base)
        self.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "x-site-id": self.SITE_ID,
                "Origin": self.url_base,
                "Referer": f"{self.url_base}/empleos.html",
            }
        )

    def extraer_titulos(
        self,
        limite: int = LIMITE_DEFAULT,
        query: str = "",
        filtros: list | None = None,
        sort: str = "RECIENTES",
    ) -> list[str]:
        """Devuelve hasta `limite` títulos de ofertas publicadas en Laborum."""
        if limite < 1:
            return []

        url = f"{self.url_base}/api/avisos/searchV2"
        params = {"pageSize": limite, "page": 0, "sort": sort}
        body = {
            "filtros": filtros or [],
            "query": query,
            "internacional": False,
        }

        try:
            respuesta = requests.post(
                url,
                headers=self.headers,
                params=params,
                json=body,
                timeout=15,
            )
            respuesta.raise_for_status()
            data = respuesta.json()
        except requests.exceptions.RequestException as e:
            print(f"Error al consultar Laborum: {e}")
            return []
        except ValueError:
            print("Error: Laborum devolvio una respuesta no JSON.")
            return []

        ofertas = data.get("content", [])
        titulos: list[str] = []
        for oferta in ofertas:
            titulo = oferta.get("titulo", "").strip()
            if titulo:
                titulos.append(titulo)
            if len(titulos) >= limite:
                break

        return titulos

    def extraer_datos(self, endpoint: str = "") -> list[str]:
        return self.extraer_titulos()


if __name__ == "__main__":
    print("--- Scraper Laborum (15 ofertas) ---")

    scraper = LaborumScraper()
    titulos = scraper.extraer_titulos(limite=15)

    if not titulos:
        print("No se encontraron ofertas.")
    else:
        for i, titulo in enumerate(titulos, start=1):
            print(f"{i:2}. {titulo}")
