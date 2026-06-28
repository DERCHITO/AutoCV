"""Extrae preguntas de seleccion (Killer Questions) de CompuTrabajo."""

from __future__ import annotations

import html
import os
import re
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

MSG_REQUIERE_SESION = (
    "Esta oferta tiene preguntas de seleccion en CompuTrabajo "
    "(requiere iniciar sesion; configure COMPUTRABAJO_EMAIL y "
    "COMPUTRABAJO_PASSWORD en .env)."
)
MSG_SIN_PREGUNTAS_SELECCION = "(sin preguntas de seleccion para esta oferta)"


class _ExtractorTitulosKQ(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.preguntas: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "input":
            return
        attrs_dict = dict(attrs)
        input_id = attrs_dict.get("id", "")
        if input_id.endswith("__Title"):
            valor = (attrs_dict.get("value") or "").strip()
            if valor:
                self.preguntas.append(valor)


def _deduplicar(preguntas: list[str]) -> list[str]:
    vistas: set[str] = set()
    unicas: list[str] = []
    for pregunta in preguntas:
        limpia = " ".join(pregunta.split())
        clave = limpia.lower()
        if clave in vistas:
            continue
        vistas.add(clave)
        unicas.append(limpia)
    return unicas


def extraer_preguntas_de_html_kq(html_fragment: str) -> list[str]:
    if not html_fragment:
        return []

    sopa = BeautifulSoup(html_fragment, "html.parser")
    preguntas: list[str] = []

    for div in sopa.select("[div-kq]"):
        kq_id = div.get("data-div-kq-id", "")
        if kq_id:
            titulo = sopa.select_one(f"#KillerQuestions_{kq_id}__Title")
            if titulo and titulo.get("value"):
                preguntas.append(titulo["value"].strip())
                continue

        for etiqueta in div.select("label"):
            texto = etiqueta.get_text(" ", strip=True)
            if len(texto) >= 10:
                preguntas.append(texto)

    if not preguntas:
        parser = _ExtractorTitulosKQ()
        parser.feed(html_fragment)
        preguntas.extend(parser.preguntas)

    return _deduplicar(preguntas)


def _headers_ajax(base_headers: dict[str, str], referer: str) -> dict[str, str]:
    return {
        **base_headers,
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": referer,
        "Origin": "https://cl.computrabajo.com",
    }


def _iniciar_sesion_candidato(
    session: requests.Session,
    email: str,
    password: str,
) -> bool:
    candidato = "https://candidato.cl.computrabajo.com"
    session.get(candidato, timeout=20)

    popup = session.get(
        f"{candidato}/ajax/showpopupaccess?idapp=1&v=8&isp=1",
        headers={
            **session.headers,
            "Referer": "https://cl.computrabajo.com/",
            "X-Requested-With": "XMLHttpRequest",
        },
        timeout=20,
    )
    popup.raise_for_status()

    sopa = BeautifulSoup(popup.text, "html.parser")
    token_input = sopa.select_one('input[name="__RequestVerificationToken"]')
    token = token_input.get("value") if token_input else ""

    payload = {
        "__RequestVerificationToken": token,
        "LoginModel.Email": email,
        "LoginModel.Password": password,
        "ActiveForm": "2",
        "IsResponsive": "2",
    }

    headers = _headers_ajax(dict(session.headers), "https://cl.computrabajo.com/")
    headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"

    for path in ("/ajax/login", "/Ajax/Login", "/Account/Login"):
        respuesta = session.post(
            f"{candidato}{path}",
            headers=headers,
            data=payload,
            timeout=20,
        )
        if respuesta.status_code >= 500:
            continue
        try:
            data = respuesta.json()
        except ValueError:
            if session.cookies.get("lout") == "false":
                return True
            continue
        if data.get("Success") or data.get("success"):
            return True

    return session.cookies.get("lout") == "false"


def _postular_y_obtener_html(
    session: requests.Session,
    apply_url: str,
    referer: str,
) -> str:
    headers = _headers_ajax(dict(session.headers), referer)
    headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"

    params = {k: v[0] for k, v in parse_qs(urlparse(apply_url).query).items()}
    try:
        respuesta = session.post(apply_url, headers=headers, data=params, timeout=25)
    except requests.exceptions.RequestException:
        return ""
    if respuesta.status_code >= 400:
        return ""

    try:
        data = respuesta.json()
    except ValueError:
        return respuesta.text

    if data.get("result") == "NotLogged":
        return ""

    for clave in ("html", "htmlpopup"):
        fragmento = data.get(clave) or ""
        if fragmento:
            return fragmento

    return ""


def _obtener_preguntas_playwright(
    listado_url: str,
    titulo: str,
    email: str,
    password: str,
) -> list[str]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return []

    busqueda = listado_url
    preguntas: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            locale="es-CL",
            viewport={"width": 1400, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        page.goto(busqueda, wait_until="networkidle", timeout=90000)

        for sel in ("#onetrust-accept-btn-handler", "button:has-text('Aceptar')"):
            btn = page.locator(sel)
            if btn.count() and btn.first.is_visible():
                btn.first.click()
                page.wait_for_timeout(800)
                break

        oferta = page.locator("h2 a", has_text=re.compile(re.escape(titulo[:40]), re.I))
        if oferta.count() == 0:
            oferta = page.locator("h2 a").first
        oferta.first.click()
        page.wait_for_timeout(2500)

        page.locator("[data-apply-ac]").first.click()
        page.wait_for_timeout(2000)

        if page.locator("#LoginModel_Email").count():
            page.fill("#LoginModel_Email", email)
            page.fill("#LoginModel_Password", password)
            page.locator("#LoginFormButton, .LoginFormButton, button:has-text('Entrar')").first.click()
            page.wait_for_timeout(4000)
            page.locator("[data-apply-ac]").first.click()
            page.wait_for_timeout(5000)

        html_pagina = page.content()
        preguntas = extraer_preguntas_de_html_kq(html_pagina)
        browser.close()

    return preguntas


def obtener_preguntas_seleccion(
    apply_url: str,
    *,
    titulo: str = "",
    referer: str = "https://cl.computrabajo.com/",
    session: requests.Session | None = None,
) -> list[str]:
    if not apply_url:
        return []

    load_dotenv()

    sesion = session or requests.Session()
    sesion.headers.setdefault(
        "User-Agent",
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        ),
    )
    sesion.headers.setdefault("Accept-Language", "es-CL,es;q=0.9")

    email = os.environ.get("COMPUTRABAJO_EMAIL", "").strip()
    password = os.environ.get("COMPUTRABAJO_PASSWORD", "").strip()

    if email and password:
        if _iniciar_sesion_candidato(sesion, email, password):
            html_resp = _postular_y_obtener_html(sesion, apply_url, referer)
            preguntas = extraer_preguntas_de_html_kq(html_resp)
            if preguntas:
                return preguntas

        if titulo:
            preguntas = _obtener_preguntas_playwright(referer, titulo, email, password)
            if preguntas:
                return preguntas

        return [MSG_REQUIERE_SESION]

    sesion.get("https://candidato.cl.computrabajo.com/", timeout=20)
    html_resp = _postular_y_obtener_html(sesion, apply_url, referer)
    preguntas = extraer_preguntas_de_html_kq(html_resp)
    if preguntas:
        return preguntas
    return [MSG_REQUIERE_SESION]


def extraer_apply_url_desde_listado(html_listado: str, titulo: str) -> str:
    sopa = BeautifulSoup(html_listado, "html.parser")
    titulo_norm = " ".join(titulo.lower().split())

    for enlace in sopa.select("h2 a"):
        texto = enlace.get_text(" ", strip=True)
        if " ".join(texto.lower().split()) != titulo_norm:
            continue

        contenedor = enlace.find_parent("[data-offers-grid-offer-item-container]")
        if not contenedor:
            contenedor = enlace.find_parent("article") or enlace.find_parent("li")

        if contenedor:
            boton = contenedor.select_one("[data-href-offer-apply]")
            if boton and boton.get("data-href-offer-apply"):
                return html.unescape(boton["data-href-offer-apply"])

    titulos = [a.get_text(" ", strip=True) for a in sopa.select("h2 a")]
    apply_urls = [
        html.unescape(el["data-href-offer-apply"])
        for el in sopa.select("[data-href-offer-apply]")
        if el.get("data-href-offer-apply")
    ]
    for idx, titulo_item in enumerate(titulos):
        if " ".join(titulo_item.lower().split()) == titulo_norm and idx < len(apply_urls):
            return apply_urls[idx]

    return ""
