"""Herramientas pequeñas que usan Benford y el Big Five."""
import random
import re

from playwright.sync_api import Page, Playwright

from config import DELAY, HEADLESS

# Número como aparece en Instagram: "1,234", "1.2K", "3M"
NUM = r"([\d.,]+[KkMm]?)"


def abrir_navegador(p: Playwright, cookies: list[dict]):
    """Abre Chromium, inyecta las cookies y devuelve (navegador, pestaña)."""
    browser = p.chromium.launch(headless=HEADLESS)
    context = browser.new_context(locale="en-US")  # idioma fijo: textos predecibles
    context.add_cookies(cookies)                   # <- INYECCIÓN DE COOKIES
    return browser, context.new_page()


def pausa(page: Page):
    """Espera entre 3 y 5 segundos, distinto cada vez."""
    page.wait_for_timeout((DELAY + random.uniform(0, 2)) * 1000)


def meta(page: Page, selector: str) -> str:
    """Lee el atributo content de una etiqueta <meta>."""
    loc = page.locator(selector)
    return (loc.first.get_attribute("content") or "") if loc.count() else ""


def buscar(patron: re.Pattern, texto: str) -> str:
    """Aplica un patrón al texto y devuelve lo que encontró, o texto vacío."""
    m = patron.search(texto)
    return m.group(1) if m else ""


def a_numero(s: str) -> int:
    """'1,234' -> 1234 ; '1.2K' -> 1200 ; '3M' -> 3000000"""
    if not s:
        return 0
    multiplicador = {"K": 1_000, "M": 1_000_000}.get(s[-1].upper(), 1)
    if multiplicador > 1:
        return round(float(s[:-1].replace(",", ".")) * multiplicador)
    return int(re.sub(r"[.,]", "", s))