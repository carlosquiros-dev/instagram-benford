"""Descarga la lista de seguidos (o seguidores) de una cuenta con paginación y lee
los seguidores y seguidos de cada cuenta desde su popover (la tarjeta que aparece
al pasar el cursor), sin abrir cada perfil."""
import json
import random
import re
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

from config import BASE, LISTA_BENFORD, N_CUENTAS, OUTPUT_DIR
from cookies import cookies_loader
from scraping.utilidades import NUM, a_numero, abrir_navegador, buscar, meta, pausa

# \s* = cero o más espacios: el popover a veces entrega "679Mfollowers" todo pegado
SEGUIDORES = re.compile(NUM + r"\s*followers", re.I)
SEGUIDOS = re.compile(NUM + r"\s*following", re.I)
EN_INGLES = {"seguidos": "following", "seguidores": "followers"}
ENLACE_PERFIL = re.compile(r"/([A-Za-z0-9._]+)/")

# JavaScript: baja hasta el final la parte de la ventana que tiene scroll
BAJAR_LISTA = """() => {
    const ventana = document.querySelector("[role='dialog']");
    if (!ventana) return;
    const cajas = [...ventana.querySelectorAll("div")].filter(e => e.scrollHeight > e.clientHeight + 10);
    if (cajas.length) cajas[cajas.length - 1].scrollTop = 1e9;
}"""

# JavaScript: devuelve el texto del popover de una cuenta (está fuera de la ventana de la lista)
LEER_POPOVER = """(usuario) => {
    const tarjetas = [...document.querySelectorAll("div")].filter(d =>
        !d.closest("[role='dialog']") && (d.innerText || "").startsWith(usuario)
        && /followers/i.test(d.innerText) && /following/i.test(d.innerText));
    if (!tarjetas.length) return null;
    tarjetas.sort((a, b) => a.innerText.length - b.innerText.length);
    return tarjetas[0].innerText;
}"""


def contadores(page: Page, usuario: str) -> dict:
    """Plan B: abre el perfil completo y lee sus seguidores y seguidos."""
    page.goto(f"{BASE}/{usuario}/")
    pausa(page)
    if "/accounts/login" in page.url:
        raise RuntimeError("Instagram pidió iniciar sesión: las cookies expiraron.")
    desc = meta(page, "meta[property='og:description']")
    return {"usuario": usuario,
            "seguidores": a_numero(buscar(SEGUIDORES, desc)),
            "seguidos": a_numero(buscar(SEGUIDOS, desc))}


def leer_popover(page: Page, enlace, usuario: str) -> dict | None:
    """Pasa el cursor VIRTUAL sobre el nombre y lee los números del popover."""
    try:
        enlace.hover()                                   # no mueve el mouse real
        page.wait_for_function(f"u => ({LEER_POPOVER})(u) !== null", arg=usuario, timeout=5000)
        texto = page.evaluate(LEER_POPOVER, usuario)
    except Exception:
        return None                                      # no apareció: se usará el plan B
    finally:
        page.mouse.move(5, 5)                            # quitar el cursor para cerrar el popover
    return {"usuario": usuario,
            "seguidores": a_numero(buscar(SEGUIDORES, texto)),
            "seguidos": a_numero(buscar(SEGUIDOS, texto))}


def recorrer_lista(page: Page, usuario: str) -> tuple[list[dict], list[str]]:
    """Abre la lista, la baja página por página y lee el popover de cada cuenta.
    Devuelve (cuentas leídas, nombres cuyo popover no apareció)."""
    tipo = EN_INGLES[LISTA_BENFORD]
    # El botón "2,451 following" no tiene dirección (href="#"): se busca por su texto
    page.locator("header a", has_text=re.compile(tipo, re.I)).first.click()
    page.wait_for_selector("[role='dialog']")
    pausa(page)

    cuentas, sin_popover, vistos = [], [], set()
    pagina, rondas_sin_nuevos = 0, 0
    while len(cuentas) + len(sin_popover) < N_CUENTAS and rondas_sin_nuevos < 3:
        pagina += 1
        nuevos = 0
        enlaces = page.locator("[role='dialog'] a[href]").filter(has_text=re.compile(r"\w"))
        for i in range(enlaces.count()):
            if len(cuentas) + len(sin_popover) >= N_CUENTAS:
                break
            m = ENLACE_PERFIL.fullmatch(enlaces.nth(i).get_attribute("href") or "")
            if not m or m.group(1) == usuario or m.group(1) in vistos:
                continue
            nombre = m.group(1)
            vistos.add(nombre)
            nuevos += 1
            c = leer_popover(page, enlaces.nth(i), nombre)
            if c:
                cuentas.append(c)
                print(f"[{len(cuentas)}] @{nombre}: {c['seguidores']} seguidores, {c['seguidos']} seguidos")
            else:
                sin_popover.append(nombre)
            page.wait_for_timeout(random.uniform(500, 1200))   # pausa corta entre tarjetas
        print(f"Página {pagina}: {len(cuentas)} cuentas leídas")
        rondas_sin_nuevos = rondas_sin_nuevos + 1 if nuevos == 0 else 0
        page.evaluate(BAJAR_LISTA)        # bajar = Instagram carga la siguiente página
        pausa(page)

    page.keyboard.press("Escape")
    return cuentas, sin_popover


def descargar_red(usuario: str) -> Path | None:
    """Recorre la lista leyendo los popovers y guarda un JSON con los números."""
    cookies = cookies_loader.preparar()
    if cookies is None:
        return None

    with sync_playwright() as p:
        browser, page = abrir_navegador(p, cookies)
        principal = contadores(page, usuario)   # también deja abierta la página de la cuenta
        print(f"@{usuario}: {principal['seguidores']} seguidores, {principal['seguidos']} seguidos")

        cuentas, sin_popover = recorrer_lista(page, usuario)
        for nombre in sin_popover:              # plan B: abrir el perfil de las que faltaron
            c = contadores(page, nombre)
            cuentas.append(c)
            print(f"[plan B] @{nombre}: {c['seguidores']} seguidores, {c['seguidos']} seguidos")
        browser.close()

    datos = {"cuenta": usuario, "lista": LISTA_BENFORD,
             "fecha": datetime.now(timezone.utc).isoformat(),
             "principal": principal, "cuentas": cuentas}
    OUTPUT_DIR.mkdir(exist_ok=True)
    salida = OUTPUT_DIR / f"benford_{usuario}.json"
    salida.write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Guardado en {salida.resolve()}")
    return salida
