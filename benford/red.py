"""Descarga la lista de seguidos (o seguidores) de una cuenta con paginación
y los números de seguidores y seguidos de cada cuenta de esa lista."""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

from config import BASE, LISTA_BENFORD, N_CUENTAS, OUTPUT_DIR
from cookies import cookies_loader
from scraping.utilidades import NUM, a_numero, abrir_navegador, buscar, meta, pausa

SEGUIDORES = re.compile(NUM + r"\s+followers", re.I)
SEGUIDOS = re.compile(NUM + r"\s+following", re.I)
EN_INGLES = {"seguidos": "following", "seguidores": "followers"}
ENLACE_PERFIL = re.compile(r"/([A-Za-z0-9._]+)/")

# JavaScript: baja hasta el final la parte de la ventana que tiene scroll
BAJAR_LISTA = """() => {
    const ventana = document.querySelector("div[role='dialog']");
    if (!ventana) return;
    const cajas = [...ventana.querySelectorAll("div")].filter(e => e.scrollHeight > e.clientHeight + 10);
    if (cajas.length) cajas[cajas.length - 1].scrollTop = 1e9;
}"""


def contadores(page: Page, usuario: str) -> dict:
    """Abre el perfil y lee sus seguidores y seguidos."""
    page.goto(f"{BASE}/{usuario}/")
    pausa(page)
    if "/accounts/login" in page.url:
        raise RuntimeError("Instagram pidió iniciar sesión: las cookies expiraron.")
    desc = meta(page, "meta[property='og:description']")
    return {"usuario": usuario,
            "seguidores": a_numero(buscar(SEGUIDORES, desc)),
            "seguidos": a_numero(buscar(SEGUIDOS, desc))}


def descargar_lista(page: Page, usuario: str) -> list[str]:
    """Abre la ventana de seguidos/seguidores y la baja página por página."""
    tipo = EN_INGLES[LISTA_BENFORD]
    page.click(f"a[href='/{usuario}/{tipo}/']")
    page.wait_for_selector("div[role='dialog']")
    pausa(page)

    nombres, pagina, rondas_sin_nuevos = [], 0, 0
    while len(nombres) < N_CUENTAS and rondas_sin_nuevos < 3:
        antes = len(nombres)
        enlaces = page.eval_on_selector_all("div[role='dialog'] a[href]",
                                            "els => els.map(a => a.getAttribute('href'))")
        for enlace in enlaces:
            m = ENLACE_PERFIL.fullmatch(enlace)
            if m and m.group(1) != usuario and m.group(1) not in nombres:
                nombres.append(m.group(1))
        pagina += 1
        print(f"Página {pagina}: {len(nombres)} cuentas")
        rondas_sin_nuevos = rondas_sin_nuevos + 1 if len(nombres) == antes else 0
        page.evaluate(BAJAR_LISTA)   # bajar = Instagram carga la siguiente página
        pausa(page)

    page.keyboard.press("Escape")
    return nombres[:N_CUENTAS]


def descargar_red(usuario: str) -> Path | None:
    """Fase 1: lista con paginación. Fase 2: números de cada cuenta. Guarda un JSON."""
    cookies = cookies_loader.preparar()
    if cookies is None:
        return None

    with sync_playwright() as p:
        browser, page = abrir_navegador(p, cookies)
        principal = contadores(page, usuario)   # también deja abierta la página de la cuenta
        print(f"@{usuario}: {principal['seguidores']} seguidores, {principal['seguidos']} seguidos")

        nombres = descargar_lista(page, usuario)
        cuentas = []
        for i, nombre in enumerate(nombres, 1):
            c = contadores(page, nombre)
            cuentas.append(c)
            print(f"[{i}/{len(nombres)}] @{nombre}: {c['seguidores']} seguidores, {c['seguidos']} seguidos")
        browser.close()

    datos = {"cuenta": usuario, "lista": LISTA_BENFORD,
             "fecha": datetime.now(timezone.utc).isoformat(),
             "principal": principal, "cuentas": cuentas}
    OUTPUT_DIR.mkdir(exist_ok=True)
    salida = OUTPUT_DIR / f"benford_{usuario}.json"
    salida.write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Guardado en {salida.resolve()}")
    return salida