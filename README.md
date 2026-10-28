# Instagram Benford

Sistema en **Python** que determina si una cuenta de Instagram se comporta como **humano o como bot** aplicando la **ley de Benford** a los números de seguidores y seguidos de las cuentas que sigue. Si el resultado es "Humano", continúa con un **análisis de personalidad Big Five (OCEAN)** de sus publicaciones usando **Gemini**.

Proyecto académico de la materia **Arquitectura de Software** — Universidad Central del Ecuador, Facultad de Ingeniería y Ciencias Aplicadas, carrera de Sistemas de Información.

> ⚠️ **Uso académico.** Los términos de uso de Instagram prohíben la recolección automatizada de datos. El proyecto se probó con una cuenta de prueba, pocas peticiones y pausas entre acciones. El análisis de personalidad solo debe hacerse con autorización del titular de la cuenta y es una aproximación, no un diagnóstico psicológico.

## ¿Qué hace?

1. **Inyecta las cookies de sesión** copiadas a mano en Chromium con Playwright (sin automatizar el inicio de sesión).
2. Abre la lista de **seguidos** de la cuenta y la recorre con **paginación** (Instagram entrega ~12 cuentas por página).
3. Lee los seguidores y seguidos de cada cuenta desde su **popover** (la tarjeta que aparece al pasar el cursor), usando el cursor virtual de Playwright, sin abrir cada perfil.
4. Toma el **primer dígito** de cada número, cuenta cuántos empiezan con 1, 2 … 9 y lo compara con la **ley de Benford** mediante **chi-cuadrado**.
5. Genera un **Excel** con los datos, el conteo, un gráfico (barras = Benford, línea = datos reales) y la clasificación.
6. Si la cuenta resulta **Humano**, extrae sus publicaciones, las analiza con **Gemini** y genera una **imagen** con los puntajes Big Five.

## Método

**Ley de Benford.** En muchos conjuntos de números reales, la probabilidad de que un número empiece con el dígito *d* es:

```
P(d) = log10(1 + 1/d)      →   1: 30,1 %   2: 17,6 %   3: 12,5 %  ...  9: 4,6 %
```

**¿Por qué los seguidos?** Los elige la propia cuenta: un usuario real sigue a amigos, marcas y figuras públicas con números muy variados, mientras que un bot sigue cuentas de forma automática (criterio propuesto por Jennifer Golbeck, 2015). Con `LISTA_BENFORD = "seguidores"` se puede analizar en cambio si la cuenta tiene seguidores falsos.

**Chi-cuadrado** (8 grados de libertad, porque hay 9 dígitos):

```
chi² = Σ (observado_d − esperado_d)² / esperado_d          d = 1 ... 9
```

| Chi-cuadrado | Clasificación |
|---|---|
| menor que 15,51 | **Humano** (sigue Benford, 95 % de confianza) |
| entre 15,51 y 20,09 | **Posible bot** |
| mayor que 20,09 | **Bot** (99 % de confianza) |

Benford evalúa el **conjunto** de números (la red de la cuenta), no a cada cuenta seguida por separado. Con 200 cuentas (400 números) el resultado es más confiable que con 20.

## Tecnologías

| Herramienta | Uso |
|---|---|
| Python 3.10+ | Lenguaje |
| [Playwright](https://playwright.dev/python/) + Chromium | Navegador controlado, inyección de cookies y cursor virtual |
| google-genai (Gemini) | Análisis Big Five |
| python-dotenv | Leer la API key desde `.env` |
| openpyxl | Excel con hojas y gráfico |
| matplotlib | Imagen del Big Five |

## Estructura

```
instagram-benford/
├── main.py                  # punto de entrada (comandos)
├── config.py                # todos los ajustes
├── cookies/
│   ├── generar_plantilla.py # crea cookiesN.json en el proyecto
│   └── cookies_loader.py    # busca, valida y prepara las cookies
├── scraping/
│   ├── utilidades.py        # navegador con cookies, pausas, números
│   └── perfil.py            # perfil y publicaciones (Big Five)
├── benford/
│   ├── red.py               # lista de seguidos con paginación y popovers
│   ├── ley.py               # primer dígito, conteo y chi-cuadrado
│   └── excel.py             # Excel con datos, conteo, gráfico y resultado
├── bigfive/
│   ├── analisis.py          # consulta a Gemini y validación
│   └── imagen.py            # imagen con el resultado
├── requirements.txt
└── .gitignore
```

Cada carpeta es un paquete con una sola responsabilidad. Benford y Big Five son independientes; `main.py` decide cuándo se ejecuta cada uno.

```
python main.py benford --usuario X
   ├─ cookies → Chromium + cookies inyectadas
   ├─ benford/red.py   → lista con paginación + popovers → output/benford_X.json
   ├─ benford/excel.py → primer dígito, conteo, chi² → Escritorio/Benford_X/benford_X.xlsx
   └─ ¿Humano? ── sí → scraping/perfil.py → bigfive/analisis.py → bigfive/imagen.py
                 └─ no → termina
```

## Instalación

```bash
git clone https://github.com/carlosquiros-dev/instagram-benford.git
cd instagram-benford
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows (PowerShell)
pip install -r requirements.txt
playwright install chromium
```

Crear un archivo **`.env`** en la raíz con la API key de Gemini ([Google AI Studio](https://aistudio.google.com/)):

```
GEMINI_API_KEY=tu_clave
```

## Uso

**1. Cookies de sesión**

```bash
python main.py plantilla
```

Se crea `cookies1.json` en el proyecto. Inicia sesión en Instagram en el navegador con una **cuenta de prueba**, abre **F12 → Application → Cookies → https://www.instagram.com** y copia el *Value* de cada cookie:

```json
{
  "sessionid": "",
  "csrftoken": "",
  "ds_user_id": "",
  "ig_did": "",
  "mid": ""
}
```

**2. Comandos**

| Comando | Qué hace |
|---|---|
| `python main.py benford --usuario X` | Descarga la lista, arma el Excel y clasifica; si es Humano, sigue con el Big Five |
| `python main.py excel --usuario X` | Rehace el Excel con los datos ya descargados |
| `python main.py bigfive --usuario X` | Solo el análisis Big Five |

## Configuración (`config.py`)

| Ajuste | Por defecto | Descripción |
|---|---|---|
| `USUARIO` | `usuario_ejemplo` | Cuenta por defecto (se puede cambiar con `--usuario`) |
| `LISTA_BENFORD` | `seguidos` | `seguidos` o `seguidores` |
| `N_CUENTAS` | `20` | Cuentas de la lista que se revisan (200 para un resultado confiable) |
| `CHI_POSIBLE_BOT` / `CHI_BOT` | `15.51` / `20.09` | Valores críticos del chi-cuadrado |
| `BIGFIVE_SI_HUMANO` | `True` | Hacer el Big Five solo si sale Humano |
| `MAX_POSTS` / `N_POSTS_ANALISIS` | `12` / `10` | Publicaciones extraídas / enviadas a Gemini |
| `MODELO_GEMINI` | `gemini-3.8-flash` | Modelo de IA |
| `DELAY` | `3` | Pausa base en segundos (3 a 5 s al azar) |
| `HEADLESS` | `False` | `True` para no mostrar el navegador |

## Resultados que genera

- `output/benford_<usuario>.json` y `Escritorio/Benford_<usuario>/benford_<usuario>.xlsx` (hojas **Datos**, **Conteo** con gráfico y **Resultado**).
- Si es Humano: `output/<usuario>.json`, `output/<usuario>_bigfive.json` y `Escritorio/BigFive_<usuario>/bigfive_<usuario>.png`.

La carpeta `output/`, el archivo `.env` y los `cookies*.json` están en `.gitignore`: nunca se suben al repositorio.

## Consideraciones

- **Riesgo de bloqueo:** Instagram no publica sus límites. Usa una cuenta de prueba, pocas ejecuciones por día y pausas de 2 a 4 s entre popovers para listas grandes.
- **Gemini:** el plan gratuito tiene un límite de solicitudes diarias. Ante errores 429, 500, 503 o 504 el programa reintenta con espera exponencial (10, 20, 40 y 80 s) y cada llamada tiene un límite de 120 s.
- **Cookies:** si Instagram redirige al login, la sesión expiró. Genera una plantilla nueva y copia cookies actuales.
- Instagram cambia su página con frecuencia; los selectores de `benford/red.py` pueden necesitar ajustes.

## Autor

Daniel Quiroz — [@carlosquiros-dev](https://github.com/carlosquiros-dev) · Arquitectura de Software, séptimo semestre.
