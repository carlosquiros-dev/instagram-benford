"""Configuración del proyecto: todo lo que se puede cambiar está aquí."""

from pathlib import Path

# --- Scraping ---
USUARIO = "usuario_ejemplo" # cuenta a estudiar (sin @)
MAX_POSTS = 12  # máximo de publicaciones a extraer
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
N_CUENTAS = 20             # cuentas de esa lista que se revisan (con paginación)
CHI_POSIBLE_BOT = 15.51      # chi-cuadrado mayor a esto: posible bot (95 %)
CHI_BOT = 20.09              # chi-cuadrado mayor a esto: bot (99 %)
BIGFIVE_SI_HUMANO = True     # si sale "Humano", hacer el Big Five (solo con permiso del titular)

# --- Rutas ---
BASE = "https://www.instagram.com"
OUTPUT_DIR = Path("output")

"""Devuelve la carpeta del Escritorio del usuario actual."""
def escritorio() -> Path:
    return Path.home() / "Desktop"