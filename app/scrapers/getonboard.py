import sys
from pathlib import Path

# Permite ejecutar: python app/scrapers/getonboard.py
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import requests

from app.scrapers.base import BaseScraper
from app.scrapers.models import OfertaLaboral


class GetOnBoardScraper(BaseScraper):
    """Scraper de ofertas de Get on Board vía API pública v0."""

    API_PREFIX = "/api/v0"
    PER_PAGE_MAX = 120

    CAMPOS_DESCRIPCION = (
        "projects",
        "description_headline",
        "description",
        "functions_headline",
        "functions",
        "benefits_headline",
        "benefits",
        "desirable_headline",
        "desirable",
    )

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

    @classmethod
    def _descripcion_desde_attributes(cls, attrs: dict) -> str:
        partes: list[str] = []
        for campo in cls.CAMPOS_DESCRIPCION:
            texto = OfertaLaboral.limpiar_html(attrs.get(campo, ""))
            if texto:
                partes.append(texto)
        return "\n\n".join(partes)

    def _oferta_desde_item(self, item: dict) -> OfertaLaboral | None:
        attrs = item.get("attributes", {})
        titulo = attrs.get("title", "").strip()
        if not titulo:
            return None

        job_id = item.get("id", "")
        url = f"{self.url_base}/jobs/{job_id}" if job_id else ""
        descripcion = self._descripcion_desde_attributes(attrs)
        preguntas: list[str] = []

        return OfertaLaboral(
            titulo=titulo,
            descripcion=descripcion,
            url=url,
            preguntas=preguntas,
        )

    def _ofertas_desde_data(self, data: list) -> list[OfertaLaboral]:
        ofertas: list[OfertaLaboral] = []
        for item in data:
            oferta = self._oferta_desde_item(item)
            if oferta:
                ofertas.append(oferta)
        return ofertas

    def extraer_ofertas(
        self,
        categoria: str | None = None,
        query: str | None = None,
        page: int = 1,
        max_resultados: int | None = None,
    ) -> list[OfertaLaboral]:
        """Devuelve ofertas con titulo y descripcion para la consulta."""
        if not query and not categoria:
            print("Error: debes indicar `categoria` o `query`.")
            return []

        ofertas: list[OfertaLaboral] = []
        pagina = max(page, 1)

        while True:
            if max_resultados is not None and len(ofertas) >= max_resultados:
                break

            faltantes = (
                self.PER_PAGE_MAX
                if max_resultados is None
                else max_resultados - len(ofertas)
            )
            per_page = min(self.PER_PAGE_MAX, faltantes)

            if query:
                params = {
                    "query": query,
                    "page": pagina,
                    "per_page": per_page,
                    "lang": self.lang,
                }
                payload = self._get_json("/search/jobs", params)
            else:
                params = {
                    "page": pagina,
                    "per_page": per_page,
                    "lang": self.lang,
                }
                payload = self._get_json(f"/categories/{categoria}/jobs", params)

            if not payload:
                break

            data = payload.get("data", [])
            if not data:
                break

            for oferta in self._ofertas_desde_data(data):
                ofertas.append(oferta)
                if max_resultados is not None and len(ofertas) >= max_resultados:
                    break

            if max_resultados is not None and len(ofertas) >= max_resultados:
                break

            meta = payload.get("meta", {})
            total_pages = meta.get("total_pages", pagina)
            if pagina >= total_pages:
                break
            pagina += 1

        if max_resultados is not None:
            return ofertas[:max_resultados]
        return ofertas

    def extraer_titulos(
        self,
        categoria: str | None = None,
        query: str | None = None,
        page: int = 1,
        max_resultados: int | None = None,
    ) -> list[str]:
        return [
            o.titulo
            for o in self.extraer_ofertas(
                categoria=categoria,
                query=query,
                page=page,
                max_resultados=max_resultados,
            )
        ]

    def extraer_datos(self, endpoint: str = "") -> list[str]:
        if endpoint.startswith("search:"):
            query = endpoint.removeprefix("search:").strip()
            return self.extraer_titulos(query=query, categoria=None)
        if endpoint:
            return self.extraer_titulos(categoria=endpoint)
        return []


if __name__ == "__main__":
    print("Usa el orquestador: python app/scrapers/base.py")
