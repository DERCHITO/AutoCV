import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup


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


class ScraperOrchestrator:
    """Ejecuta Laborum, Get on Board y CompuTrabajo y agrupa los resultados."""

    FUENTES = ("laborum", "getonboard", "computrabajo")

    def __init__(self, limite_por_fuente: int = 15):
        from app.scrapers.computrabajo import CompuTrabajoScraper
        from app.scrapers.getonboard import GetOnBoardScraper
        from app.scrapers.laborum import LaborumScraper

        self.limite_por_fuente = limite_por_fuente
        self._scrapers = {
            "laborum": LaborumScraper(),
            "getonboard": GetOnBoardScraper(),
            "computrabajo": CompuTrabajoScraper(),
        }

    def extraer_de_fuente(self, fuente: str, query: str = "") -> list[str]:
        if fuente not in self._scrapers:
            raise ValueError(f"Fuente desconocida: {fuente}. Usa: {', '.join(self.FUENTES)}")

        limite = self.limite_por_fuente
        scraper = self._scrapers[fuente]

        if fuente == "laborum":
            return scraper.extraer_titulos(limite=limite, query=query)
        if fuente == "getonboard":
            if query:
                return scraper.extraer_titulos(limite=limite, query=query, categoria=None)
            return scraper.extraer_titulos(limite=limite)
        if query:
            return scraper.extraer_titulos(limite=limite, query=query, categoria=None)
        return scraper.extraer_titulos(limite=limite)

    def buscar(self, query: str = "") -> dict[str, list[str]]:
        """Consulta las tres fuentes y devuelve titulos agrupados por portal."""
        return {fuente: self.extraer_de_fuente(fuente, query=query) for fuente in self.FUENTES}

    @staticmethod
    def imprimir_resultados(resultados: dict[str, list[str]], query: str = "") -> None:
        titulo_busqueda = f" (query: {query})" if query else ""
        print(f"--- Busqueda en portales de empleo{titulo_busqueda} ---\n")

        etiquetas = {
            "laborum": "Laborum",
            "getonboard": "Get on Board",
            "computrabajo": "CompuTrabajo",
        }

        for fuente in ScraperOrchestrator.FUENTES:
            titulos = resultados.get(fuente, [])
            print(f"## {etiquetas[fuente]} ({len(titulos)} ofertas)")

            if not titulos:
                print("   No se encontraron ofertas.\n")
                continue

            for i, titulo in enumerate(titulos, start=1):
                print(f"  {i:2}. {titulo}")
            print()


if __name__ == "__main__":
    if __package__ in (None, ""):
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

    query = sys.argv[1] if len(sys.argv) > 1 else ""
    limite = int(sys.argv[2]) if len(sys.argv) > 2 else 15

    orchestrator = ScraperOrchestrator(limite_por_fuente=limite)
    resultados = orchestrator.buscar(query=query)
    ScraperOrchestrator.imprimir_resultados(resultados, query=query)
