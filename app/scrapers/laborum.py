import sys
from pathlib import Path

# Permite ejecutar: python app/scrapers/laborum.py
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import requests

from app.scrapers.base import BaseScraper
from app.scrapers.models import OfertaLaboral
from app.scrapers.preguntas import completar_preguntas


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

    @staticmethod
    def _oferta_desde_item(item: dict) -> OfertaLaboral | None:
        titulo = item.get("titulo", "").strip()
        if not titulo:
            return None

        aviso_id = item.get("id")
        url = f"https://www.laborum.cl/empleos/{aviso_id}.html" if aviso_id else ""
        descripcion = item.get("detalle", "").strip()
        preguntas = completar_preguntas(
            [],
            descripcion,
            incluye_preguntas_portal=bool(item.get("tienePreguntas")),
        )

        return OfertaLaboral(
            titulo=titulo,
            descripcion=descripcion,
            url=url,
            preguntas=preguntas,
        )

    def extraer_ofertas(
        self,
        query: str = "",
        filtros: list | None = None,
        sort: str = "RECIENTES",
        max_resultados: int | None = None,
    ) -> list[OfertaLaboral]:
        """Devuelve ofertas con titulo y descripcion para la consulta."""
        url = f"{self.url_base}/api/avisos/searchV2"
        ofertas: list[OfertaLaboral] = []
        pagina = 0

        while True:
            if max_resultados is not None and len(ofertas) >= max_resultados:
                break

            page_size = self.PAGE_SIZE
            if max_resultados is not None:
                page_size = min(self.PAGE_SIZE, max_resultados - len(ofertas))

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

            items = data.get("content", [])
            if not items:
                break

            for item in items:
                oferta = self._oferta_desde_item(item)
                if oferta:
                    ofertas.append(oferta)
                if max_resultados is not None and len(ofertas) >= max_resultados:
                    break

            if max_resultados is not None and len(ofertas) >= max_resultados:
                break
            if len(items) < page_size:
                break
            pagina += 1

        if max_resultados is not None:
            return ofertas[:max_resultados]
        return ofertas

    def extraer_titulos(
        self,
        query: str = "",
        filtros: list | None = None,
        sort: str = "RECIENTES",
        max_resultados: int | None = None,
    ) -> list[str]:
        return [
            o.titulo
            for o in self.extraer_ofertas(
                query=query,
                filtros=filtros,
                sort=sort,
                max_resultados=max_resultados,
            )
        ]

    def extraer_datos(self, endpoint: str = "") -> list[str]:
        return self.extraer_titulos(query=endpoint)


if __name__ == "__main__":
    print("Usa el orquestador: python app/scrapers/base.py")
