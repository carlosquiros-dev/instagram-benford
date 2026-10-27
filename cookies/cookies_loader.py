"""Busca el archivo de cookies en la carpeta del proyecto, lo valida
y lo convierte en cookies que Playwright puede inyectar en el navegador."""
import json
import re
from pathlib import Path

from cookies.generar_plantilla import COOKIE_NAMES

PATRON_ARCHIVO = re.compile(r"cookies(\d*)\.json")


def _numero(archivo: Path) -> int:
    m = PATRON_ARCHIVO.fullmatch(archivo.name)
    return int(m.group(1)) if m and m.group(1) else 0


def encontrar_archivo(carpeta: Path = Path(".")) -> Path | None:
    """Devuelve el cookies*.json con el número más alto (el más reciente)."""
    archivos = [p for p in carpeta.iterdir() if PATRON_ARCHIVO.fullmatch(p.name)]
    return max(archivos, key=_numero, default=None)


def cargar(archivo: Path) -> list[dict]:
    """Lee el archivo y arma las cookies. Lanza ValueError si falta alguna."""
    datos = json.loads(archivo.read_text(encoding="utf-8"))

    faltan = [n for n in COOKIE_NAMES if not str(datos.get(n, "")).strip()]
    if faltan:
        raise ValueError(f"Faltan valores en {archivo.name}: {faltan}")


    # ¿Cómo sabe qué datos agregar a cada cookie?
    # No lo deduce: están escritos aquí mismo, a mano.
    # Esta parte funciona como una receta que se repite para cada nombre de COOKIE_NAMES.
    # En cada vuelta, "n" es el nombre de la cookie (por ejemplo, sessionid).
    #   - name: es "n", el nombre de la cookie.
    #   - value: se busca en cookies1.json con datos[n] (lo que copiaste de DevTools).
    #   - domain, path y secure: se copian tal cual porque son iguales para las 5 cookies:
    #       domain ".instagram.com" -> la cookie solo se envía a Instagram
    #       path "/"                -> vale para todas las páginas del sitio
    #       secure True             -> solo viaja por conexiones seguras (https)
    # Es como un formulario con tres casillas ya impresas: solo se rellenan el nombre y el valor.


    return [
        {"name": n, "value": str(datos[n]).strip(),
         "domain": ".instagram.com", "path": "/", "secure": True}
        for n in COOKIE_NAMES
    ]


def preparar() -> list[dict] | None:
    """Busca y carga las cookies. Si algo falla, explica qué hacer y devuelve None."""
    archivo = encontrar_archivo()
    if archivo is None:
        print("No hay ningún cookies*.json en el proyecto. Créalo con la plantilla y llénalo.")
        return None
    try:
        cookies = cargar(archivo)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"Error en {archivo.name}: {e}")
        return None
    print(f"Usando cookies de: {archivo.name}")
    return cookies