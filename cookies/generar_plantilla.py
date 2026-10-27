"""Crea en la carpeta del proyecto una plantilla vacía cookies1.json, cookies2.json, ...
Para copiar a mano las cookies desde DevTools."""

import json  #es una libreria estándar de python
#Lo entienden personas y programas. Se lee fácil a simple vista y
# lo entienden casi todos los lenguajes: Python
from pathlib import Path

# Las 5 cookies de sesión de Instagram
COOKIE_NAMES = ["sessionid", "csrftoken", "ds_user_id", "ig_did", "mid"]


def generar() -> Path:
    carpeta = Path(".")  # "." = la carpeta del proyecto (desde donde se ejecuta)

    # Siguiente número libre: cookies1.json, cookies2.json, ...
    n = 1
    while (carpeta / f"cookies{n}.json").exists():
        n += 1
    archivo = carpeta / f"cookies{n}.json"

    plantilla = {nombre: "" for nombre in COOKIE_NAMES}
    archivo.write_text(json.dumps(plantilla, indent=2), encoding="utf-8")

    print(f"Plantilla creada en: {archivo.resolve()}")
    print("Copia el Value de cada cookie (F12 -> Application -> Cookies) en el archivo.")
    return archivo