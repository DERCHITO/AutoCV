from dataclasses import dataclass, field

from bs4 import BeautifulSoup


@dataclass
class OfertaLaboral:
    titulo: str
    descripcion: str = ""
    url: str = ""
    preguntas: list[str] = field(default_factory=list)

    @staticmethod
    def limpiar_html(texto: str) -> str:
        if not texto:
            return ""
        if "<" not in texto:
            return texto.strip()
        return BeautifulSoup(texto, "html.parser").get_text("\n", strip=True)
