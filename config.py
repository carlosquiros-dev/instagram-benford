"""Configuración del proyecto: todo lo que se puede cambiar está aquí."""

from pathlib import Path

# --- Scraping ---
USUARIO = "alondra_cgp"  # cuenta a estudiar (sin @)
MAX_POSTS = 50  # máximo de publicaciones a extraer
DELAY = 3  # pausa base entre acciones (segundos)
#el tiempo del DELAY se aumenta cuando los post se aumentan también
HEADLESS = False  # False = se ve el navegador y si es true no se ve lo que hace
#en el navegador.


# --- Big Five ---
N_POSTS_ANALISIS = 10                 # publicaciones que se envían a Gemini
MODELO_GEMINI = "gemini-3.8-flash"     # modelo de IA
CONSENTIMIENTO = "Análisis realizado con autorización de la titular de la cuenta." #Nota ética xd no hace nada
#pero


# --- Ley de Benford ---
LISTA_BENFORD = "seguidos"   # "seguidos" o "seguidores": qué lista se analiza
N_CUENTAS = 200              # cuentas de esa lista que se revisan (con paginación)
CHI_POSIBLE_BOT = 15.51      # chi-cuadrado mayor a esto: posible bot (95 %)
CHI_BOT = 20.09              # chi-cuadrado mayor a esto: bot (99 %)
BIGFIVE_SI_HUMANO = True     # si sale "Humano", hacer el Big Five (solo con permiso del titular)

# --- Rutas ---
BASE = "https://www.instagram.com"
OUTPUT_DIR = Path("output")




def escritorio() -> Path:
    """Devuelve la carpeta del Escritorio (con o sin OneDrive, en inglés o español)."""
    home = Path.home()
    for carpeta in [home / "Desktop", home / "OneDrive" / "Desktop",
                    home / "Escritorio", home / "OneDrive" / "Escritorio"]:
        if carpeta.is_dir():
            return carpeta
    return home