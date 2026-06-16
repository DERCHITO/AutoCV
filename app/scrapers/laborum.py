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
    PAGE_SIZE = 50

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
        query: str = "",
        filtros: list | None = None,
        sort: str = "RECIENTES",
        max_resultados: int | None = None,
    ) -> list[str]:
        """Devuelve titulos para la consulta. Pagina hasta agotar o alcanzar max_resultados."""
        url = f"{self.url_base}/api/avisos/searchV2"
        titulos: list[str] = []
        pagina = 0

        while True:
            if max_resultados is not None and len(titulos) >= max_resultados:
                break

            page_size = self.PAGE_SIZE
            if max_resultados is not None:
                page_size = min(self.PAGE_SIZE, max_resultados - len(titulos))

            params = {"pageSize": page_size, "page": pagina, "sort": sort}
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
                break
            except ValueError:
                print("Error: Laborum devolvio una respuesta no JSON.")
                break

            ofertas = data.get("content", [])
            if not ofertas:
                break

            for oferta in ofertas:
                titulo = oferta.get("titulo", "").strip()
                if titulo:
                    titulos.append(titulo)
                if max_resultados is not None and len(titulos) >= max_resultados:
                    break

            if max_resultados is not None and len(titulos) >= max_resultados:
                break
            if len(ofertas) < page_size:
                break
            pagina += 1

        if max_resultados is not None:
            return titulos[:max_resultados]
        return titulos

    def extraer_datos(self, endpoint: str = "") -> list[str]:
        return self.extraer_titulos(query=endpoint)


if __name__ == "__main__":
    print("Usa el orquestador: python app/scrapers/base.py")
