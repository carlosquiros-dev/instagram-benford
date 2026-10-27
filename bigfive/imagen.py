"""Big Five, parte 3: imagen con el resultado en una carpeta del Escritorio."""
import textwrap
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # dibuja sin abrir ventanas
import matplotlib.pyplot as plt

from bigfive.analisis import RASGOS
from config import escritorio

COLOR_BARRA = "#3b6ea5"
COLOR_TEXTO = "#222222"
COLOR_SUAVE = "#666666"


def _escribir(fig, y: float, texto: str, ancho: int, tamano: float, color: str = COLOR_TEXTO) -> float:
    """Escribe un texto largo en varias líneas y devuelve la altura donde terminó."""
    for linea in textwrap.wrap(texto, ancho) or [""]:
        fig.text(0.07, y, linea, fontsize=tamano, color=color)
        y -= tamano * 0.0021
    return y


def generar_imagen(perfil: dict, resultado: dict) -> Path:
    usuario = perfil["username"]
    carpeta = escritorio() / f"BigFive_{usuario}"
    carpeta.mkdir(exist_ok=True)
    archivo = carpeta / f"bigfive_{usuario}.png"
    meta = resultado["meta"]

    fig = plt.figure(figsize=(10, 13), dpi=150)
    fig.text(0.07, 0.955, "Análisis de personalidad Big Five (OCEAN)", fontsize=20, fontweight="bold")
    fig.text(0.07, 0.928, f"{perfil['fullName']} (@{usuario})  ·  {meta['postsAnalizados']} publicaciones "
             f"analizadas  ·  {date.today().strftime('%d/%m/%Y')}", fontsize=11, color=COLOR_SUAVE)

    # Gráfico de barras: de arriba hacia abajo O, C, E, A, N
    ax = fig.add_axes([0.33, 0.66, 0.60, 0.24])
    claves = list(RASGOS)[::-1]
    barras = ax.barh([f"{RASGOS[c][0]}  {RASGOS[c][1]}" for c in claves],
                     [resultado["rasgos"][c]["puntaje"] for c in claves], color=COLOR_BARRA, height=0.55)
    for barra, c in zip(barras, claves):
        r = resultado["rasgos"][c]
        ax.text(barra.get_width() + 1.5, barra.get_y() + barra.get_height() / 2,
                f"{r['puntaje']}  ({r['nivel']})", va="center", fontsize=10)
    ax.set_xlim(0, 115)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.grid(axis="x", color="#e5e5e5")
    ax.set_axisbelow(True)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)

    # Justificación de cada rasgo
    y = 0.615
    for c, (letra, nombre) in RASGOS.items():
        r = resultado["rasgos"][c]
        fig.text(0.07, y, f"{letra} · {nombre}: {r['nivel']}", fontsize=11, fontweight="bold")
        y = _escribir(fig, y - 0.022, r.get("justificacion", ""), 105, 10, COLOR_SUAVE) - 0.012

    # Conclusión y nota final
    fig.text(0.07, y - 0.02, "Conclusión", fontsize=14, fontweight="bold")
    fig.text(0.07, y - 0.05, f"Tipo de personalidad: {resultado.get('tipo_personalidad', '')}",
             fontsize=13, fontweight="bold", color=COLOR_BARRA)
    y = _escribir(fig, y - 0.078, resultado.get("conclusion", ""), 95, 11)
    y = _escribir(fig, y - 0.015, f"Confianza: {resultado.get('confianza', '?')}. "
                                  f"{resultado.get('limitaciones', '')}", 115, 9, COLOR_SUAVE)
    _escribir(fig, y - 0.004, f"{meta['consentimiento']} Generado con {meta['modelo']}; "
                              "es una aproximación académica, no un diagnóstico psicológico.", 115, 9, COLOR_SUAVE)

    # bbox_inches="tight": la imagen crece si el texto de Gemini es largo
    fig.savefig(archivo, facecolor="white", bbox_inches="tight", pad_inches=0.5)
    plt.close(fig)
    print(f"Imagen guardada en: {archivo}")
    return archivo
