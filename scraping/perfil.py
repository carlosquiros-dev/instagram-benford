"""Big Five, parte 1: datos del perfil y sus publicaciones."""
import json
import re
from datetime import datetime
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

from config import BASE, MAX_POSTS, OUTPUT_DIR
from cookies import cookies_loader
from scraping.utilidades import NUM, a_numero, abrir_navegador, buscar, meta, pausa

SEGUIDORES = re.compile(NUM + r"\s+followers", re.I)
SEGUIDOS = re.compile(NUM + r"\s+following", re.I)
PUBLICACIONES = re.compile(NUM + r"\s+posts", re.I)
LIKES = re.compile(NUM + r"\s+likes?", re.I)
COMENTARIOS = re.compile(NUM + r"\s+comments?", re.I)
TEXTO = re.compile(r':\s*"(.*)"\s*\.?\s*$', re.S)
FECHA = re.compile(r"on ([A-Z][a-z]+ \d{1,2}, \d{4}):")
ENLACE_POST = re.compile(r"/(p|reel)/([A-Za-z0-9_-]+)")
BOTONES = {"Follow", "Following", "Message"}


def extraer_bio(cabecera: str, nombre: str, usuario: str) -> str:
    """La bio son las líneas de la cabecera entre los contadores y los botones."""
    lineas = [l.strip() for l in cabecera.splitlines() if l.strip()]
    inicio = next((i + 1 for i, l in enumerate(lineas) if l.lower().endswith("following")), None)
    if inicio is None:
        return ""
    bio = []
    for l in lineas[inicio:]:
        if l == nombre:
            continue
        if l == usuario or l in BOTONES or l.startswith("Followed by"):
            break
        bio.append(l)
    return "\n".join(bio)


def extraer_perfil(page: Page, usuario: str) -> dict:
    """Abre el perfil y lee nombre, biografía y contadores."""
    page.goto(f"{BASE}/{usuario}/")
    pausa(page)
    if "/accounts/login" in page.url:
        raise RuntimeError("Instagram pidió iniciar sesión: las cookies expiraron.")
    desc = meta(page, "meta[property='og:description']")
    titulo = meta(page, "meta[property='og:title']")        # "Nombre (@usuario) • Instagram..."
    nombre = titulo.split(" (@")[0] if " (@" in titulo else ""
    try:
        cabecera = page.locator("header").first.inner_text(timeout=5000)
    except Exception:
        cabecera = ""
    return {"username": usuario,
            "fullName": nombre,
            "biography": extraer_bio(cabecera, nombre, usuario),
            "followers": a_numero(buscar(SEGUIDORES, desc)),
            "following": a_numero(buscar(SEGUIDOS, desc)),
            "postsCount": a_numero(buscar(PUBLICACIONES, desc)),
            "isPrivate": "This account is private" in page.content()}


def enlaces_publicaciones(page: Page) -> list[str]:
    """Baja por la cuadrícula del perfil y junta los enlaces de las publicaciones."""
    urls, rondas_sin_nuevos = [], 0
    while len(urls) < MAX_POSTS and rondas_sin_nuevos < 3:
        antes = len(urls)
        for href in page.eval_on_selector_all("a[href]", "els => els.map(a => a.href)"):
            m = ENLACE_POST.search(href)
            url = f"{BASE}/{m.group(1)}/{m.group(2)}/" if m else None
            if url and url not in urls and len(urls) < MAX_POSTS:
                urls.append(url)
        rondas_sin_nuevos = rondas_sin_nuevos + 1 if len(urls) == antes else 0
        page.mouse.wheel(0, 2500)
        pausa(page)
    return urls


def extraer_post(page: Page, url: str) -> dict:
    """Abre una publicación y lee likes, comentarios, fecha y texto."""
    page.goto(url)
    pausa(page)
    desc = meta(page, "meta[property='og:description']")
    try:
        fecha = page.locator("time[datetime]").first.get_attribute("datetime", timeout=3000) or ""
    except Exception:
        fecha = ""
    if not fecha and buscar(FECHA, desc):            # los reels no tienen <time>
        fecha = datetime.strptime(buscar(FECHA, desc), "%B %d, %Y").date().isoformat()
    return {"url": url,
            "type": "reel" if "/reel/" in url else "post",
            "likes": a_numero(buscar(LIKES, desc)),
            "comments": a_numero(buscar(COMENTARIOS, desc)),
            "date": fecha,
            "caption": buscar(TEXTO, desc)}


def scrapear_perfil(usuario: str) -> Path | None:
    """Saca el perfil y sus publicaciones y los guarda en output/<usuario>.json."""
    cookies = cookies_loader.preparar()
    if cookies is None:
        return None
    with sync_playwright() as p:
        browser, page = abrir_navegador(p, cookies)
        perfil = extraer_perfil(page, usuario)
        perfil["posts"] = []
        if not perfil["isPrivate"]:
            for i, url in enumerate(enlaces_publicaciones(page), 1):
                perfil["posts"].append(extraer_post(page, url))
                print(f"[{i}] {url}")
        browser.close()

    OUTPUT_DIR.mkdir(exist_ok=True)
    salida = OUTPUT_DIR / f"{usuario}.json"
    salida.write_text(json.dumps(perfil, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Perfil: @{usuario} ({perfil['fullName']}) - {len(perfil['posts'])} publicaciones")
    return salida