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
            print(f"❌ Error al conectar con {url_completa}: {e}")
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


if __name__ == "__main__":
    print("--- Probando el Scraper Base ---")

    mi_scraper = BaseScraper("https://news.ycombinator.com/")

    sopa_prueba = mi_scraper.obtener_sopa()
    if sopa_prueba:
        enlaces = sopa_prueba.find_all("span", class_="sitestr")
        for e in enlaces:
            print(f"👉 {e.text}")
