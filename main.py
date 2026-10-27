"""Punto de entrada del proyecto.

  python main.py plantilla               -> crea cookiesN.json en el proyecto
  python main.py benford --usuario X     -> descarga la lista, arma el Excel y clasifica
                                            (si sale "Humano", sigue con el Big Five)
  python main.py excel --usuario X       -> rehace el Excel con los datos ya descargados
  python main.py bigfive --usuario X     -> solo el Big Five: perfil + Gemini + imagen
"""
import argparse
import json

from config import BIGFIVE_SI_HUMANO, OUTPUT_DIR, USUARIO


def analizar_benford(usuario: str, descargar: bool):
    from benford.excel import generar_excel
    from benford.red import descargar_red

    archivo = OUTPUT_DIR / f"benford_{usuario}.json"
    if descargar:
        try:
            archivo = descargar_red(usuario)
        except Exception as e:
            print(f"Error durante la descarga: {e}")
            return
        if archivo is None:
            return
    elif not archivo.exists():
        print(f"No existe {archivo}. Ejecuta primero: python main.py benford --usuario {usuario}")
        return

    datos = json.loads(archivo.read_text(encoding="utf-8"))
    resultado = generar_excel(datos)

    if resultado == "Humano" and BIGFIVE_SI_HUMANO:
        print("Resultado: Humano -> se continúa con el análisis Big Five.")
        analizar_bigfive(usuario)


def analizar_bigfive(usuario: str):
    from bigfive.analisis import analizar
    from bigfive.imagen import generar_imagen
    from scraping.perfil import scrapear_perfil

    try:
        archivo = scrapear_perfil(usuario)
        if archivo is None:
            return
        perfil = json.loads(archivo.read_text(encoding="utf-8"))
        resultado = analizar(perfil)
    except Exception as e:
        print(f"Error en el Big Five: {e}")
        return
    generar_imagen(perfil, resultado)


def main():
    parser = argparse.ArgumentParser(description="Detección de bots con Benford y análisis Big Five")
    parser.add_argument("accion", choices=["plantilla", "benford", "excel", "bigfive"])
    parser.add_argument("--usuario", default=USUARIO, help="cuenta a analizar (sin @)")
    args = parser.parse_args()

    if args.accion == "plantilla":
        from cookies.generar_plantilla import generar
        generar()
    elif args.accion == "benford":
        analizar_benford(args.usuario, descargar=True)
    elif args.accion == "excel":
        analizar_benford(args.usuario, descargar=False)
    elif args.accion == "bigfive":
        analizar_bigfive(args.usuario)


if __name__ == "__main__":
    main()
