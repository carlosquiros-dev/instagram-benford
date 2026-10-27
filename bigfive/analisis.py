"""Big Five, parte 2: envía las publicaciones a Gemini y obtiene los puntajes OCEAN."""
import json
import os
import time
from datetime import datetime, timezone

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

from config import CONSENTIMIENTO, MODELO_GEMINI, N_POSTS_ANALISIS, OUTPUT_DIR

# clave en el JSON -> (letra OCEAN, nombre en español)
RASGOS = {
    "apertura": ("O", "Apertura a la experiencia"),
    "responsabilidad": ("C", "Responsabilidad"),
    "extraversion": ("E", "Extraversión"),
    "amabilidad": ("A", "Amabilidad"),
    "neuroticismo": ("N", "Neuroticismo"),
}
REINTENTOS = 4


def preguntar_a_gemini(prompt: str) -> tuple[dict, dict]:
    """Envía el prompt y devuelve (respuesta como diccionario, tokens usados).
    Si Gemini está saturado o tarda demasiado (429/500/503/504), espera y reintenta."""
    load_dotenv()                                   # lee la API key del archivo .env
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Falta GEMINI_API_KEY en el archivo .env")
    # timeout: si Gemini no responde en 120 s (en milisegundos), da error en vez de esperar para siempre
    cliente = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=120_000))

    for intento in range(REINTENTOS + 1):
        try:
            respuesta = cliente.models.generate_content(
                model=MODELO_GEMINI,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",   # obliga a responder en JSON
                    temperature=0.2,                         # respuestas consistentes
                ),
            )
            uso = respuesta.usage_metadata
            tokens = {"entrada": getattr(uso, "prompt_token_count", 0) or 0,
                      "salida": getattr(uso, "candidates_token_count", 0) or 0}
            return json.loads(respuesta.text), tokens
        except errors.APIError as e:
            if e.code not in (429, 500, 503, 504) or intento == REINTENTOS:
                raise
            espera = 10 * 2 ** intento                       # 10, 20, 40, 80 segundos
            print(f"Gemini respondió {e.code}. Reintento {intento + 1}/{REINTENTOS} en {espera} s...")
            time.sleep(espera)


def construir_prompt(perfil: dict, posts: list[dict]) -> str:
    return f"""Eres un psicólogo experto en el modelo de personalidad Big Five (OCEAN).
Analiza la personalidad que proyecta públicamente este perfil de Instagram,
basándote ÚNICAMENTE en la información dada. Es un ejercicio académico: una
aproximación, no un diagnóstico clínico.

PERFIL
- Nombre: {perfil["fullName"]}
- Biografía: {perfil["biography"]}
- Seguidores: {perfil["followers"]} | Seguidos: {perfil["following"]} | Publicaciones: {perfil["postsCount"]}

ÚLTIMAS {len(posts)} PUBLICACIONES
{json.dumps(posts, ensure_ascii=False, indent=2)}

Responde SOLO con un JSON con esta estructura:
{{
  "rasgos": {{
    "<rasgo>": {{"puntaje": <entero de 0 a 100>, "nivel": "bajo" | "medio" | "alto",
                 "justificacion": "<1-2 frases basadas en las publicaciones>"}}
  }},
  "tipo_personalidad": "<etiqueta corta, máximo 6 palabras>",
  "conclusion": "<2-3 frases que expliquen el tipo de personalidad>",
  "confianza": "baja" | "media" | "alta",
  "limitaciones": "<1 frase sobre por qué puede no ser exacto>"
}}
Los rasgos deben ser exactamente: {", ".join(RASGOS)}."""


def analizar(perfil: dict) -> dict:
    """Envía las publicaciones a Gemini, valida la respuesta y la guarda."""
    posts = [{"fecha": p["date"], "tipo": p["type"], "likes": p["likes"],
              "comentarios": p["comments"], "texto": p["caption"]}
             for p in perfil["posts"] if p.get("caption")][:N_POSTS_ANALISIS]
    if not posts:
        raise ValueError("No hay publicaciones con texto para analizar.")
    print(f"Analizando @{perfil['username']} con {len(posts)} publicaciones usando {MODELO_GEMINI}...")

    resultado, tokens = preguntar_a_gemini(construir_prompt(perfil, posts))

    # No se confía ciegamente en la IA: deben venir los 5 rasgos y puntajes de 0 a 100
    faltan = [r for r in RASGOS if r not in resultado.get("rasgos", {})]
    if faltan:
        raise ValueError(f"Gemini no devolvió estos rasgos: {faltan}")
    for r in RASGOS:
        resultado["rasgos"][r]["puntaje"] = max(0, min(100, int(resultado["rasgos"][r].get("puntaje", 0))))

    resultado["meta"] = {"usuario": perfil["username"], "modelo": MODELO_GEMINI,
                         "postsAnalizados": len(posts), "tokens": tokens,
                         "fecha": datetime.now(timezone.utc).isoformat(),
                         "consentimiento": CONSENTIMIENTO}
    salida = OUTPUT_DIR / f"{perfil['username']}_bigfive.json"
    salida.write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")

    for clave, (letra, nombre) in RASGOS.items():
        r = resultado["rasgos"][clave]
        print(f"  {letra} {nombre:<27} {r['puntaje']:>3}/100 ({r['nivel']})")
    print(f"Tipo de personalidad: {resultado.get('tipo_personalidad', '')}")
    print(f"Tokens usados: {tokens['entrada']} entrada + {tokens['salida']} salida")
    return resultado
