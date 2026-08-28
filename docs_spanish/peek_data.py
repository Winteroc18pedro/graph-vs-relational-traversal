########################################################################
# COPIA ANOTADA — solo con fines de aprendizaje.
#
# Este es un duplicado explicado línea por línea de scripts/peek_data.py.
# NO está pensado para ejecutarse como parte del pipeline del proyecto — vive en
# docs_spanish/ porque su propósito es enseñar, no ejecutarse. El script real y "limpio"
# (sin nada de este comentario) es scripts/peek_data.py.
#
# Este archivo asume que ya has leído docs_spanish/download_gharchive.py — los
# fundamentos explicados allí (docstrings, imports, Path, anotaciones de
# tipo, f-strings, argparse, main(), la protección __name__) NO se
# vuelven a explicar desde cero aquí. Este archivo se centra en lo que es
# NUEVO en peek_data.py.
########################################################################

"""Peek at the first few events in a downloaded GH Archive JSON Lines file.

Usage:
    python scripts/peek_data.py
    python scripts/peek_data.py --file data/2026-08-27-15.json --lines 10
"""

# argparse, Path: ya explicados en docs_spanish/download_gharchive.py.
import argparse

# json: el módulo de la biblioteca estándar para convertir entre texto
# JSON y objetos de Python. `json.loads(text)` ("load string", cargar
# desde cadena) analiza una cadena de texto con formato JSON y la
# convierte en valores de Python — un objeto JSON como {"a": 1} se
# convierte en un dict de Python, un array JSON se convierte en una lista
# de Python, y así sucesivamente. Esto es exactamente lo que necesitamos
# aquí: cada línea del archivo de datos es un objeto JSON como texto, y lo
# queremos como un dict de Python del que poder extraer campos.
#
# (Compara `json.loads` con `json.load` — sin la "s" — que lee
# directamente desde un archivo ya abierto en lugar de desde una cadena
# de texto. Aquí usamos `loads` porque estamos manejando una línea de
# texto ya leída a la vez, no un objeto de archivo entero.)
import json

from pathlib import Path

# ---------------------------------------------------------------------
# DEFAULT_FILE: la misma técnica de construcción de Path que DATA_DIR en
# download_gharchive.py — calculada a partir de la propia ubicación de
# este script (__file__), subiendo hasta la raíz del proyecto
# (.parent.parent), y luego bajando hasta data/2026-08-27-15.json. Esto
# fija de forma explícita el archivo de conjunto de datos específico que
# usa este proyecto como el objetivo por defecto a examinar, mientras que
# --file sigue permitiendo sobreescribirlo para una hora descargada
# diferente.
# ---------------------------------------------------------------------
DEFAULT_FILE = Path(__file__).resolve().parent.parent / "data" / "2026-08-27-15.json"

# Cuántos eventos imprimir si no se especifica --lines. Se mantiene
# pequeño (5) ya que esta función es para una comprobación rápida de
# sanidad, no para leer el archivo entero.
DEFAULT_LINES = 5


# ---------------------------------------------------------------------
# def peek(file_path: Path, num_lines: int) -> None:
# Dos parámetros, ambos obligatorios (sin valores por defecto aquí, a
# diferencia del data_dir de download()) — esta función siempre necesita
# que se le indique explícitamente qué archivo leer y cuántas líneas
# mostrar.
# ---------------------------------------------------------------------
def peek(file_path: Path, num_lines: int) -> None:
    # ---------------------------------------------------------------
    # open(file_path, "r", encoding="utf-8"):
    #   "r"                modo "read" (lectura), y — a diferencia de los
    #                      "rb"/"wb" de download_gharchive.py (modos
    #                      binarios) — el simple "r" aquí significa modo
    #                      TEXTO: Python decodifica automáticamente los
    #                      bytes crudos en disco a un str de Python a
    #                      medida que lees, usando la codificación
    #                      indicada. El modo binario era correcto para
    #                      download_gharchive.py porque simplemente
    #                      retransmitíamos bytes sin cambiarlos; aquí
    #                      realmente queremos interpretar el contenido
    #                      como texto (concretamente, como JSON), así que
    #                      el modo texto es lo correcto.
    #   encoding="utf-8"    los archivos JSON Lines (y JSON en general)
    #                      están casi universalmente codificados en
    #                      UTF-8. Ser explícito sobre la codificación, en
    #                      lugar de confiar en lo que sea que el sistema
    #                      operativo tenga por defecto, evita bugs
    #                      sutiles en los que el mismo archivo podría
    #                      leerse de forma diferente en distintas
    #                      máquinas (p. ej. Windows a veces usa por
    #                      defecto una codificación distinta a la de
    #                      macOS/Linux).
    #
    # Igual que en download_gharchive.py, esto usa un bloque `with` para
    # que el archivo se cierre automática y fiablemente una vez que
    # terminemos con él.
    # ---------------------------------------------------------------
    with open(file_path, "r", encoding="utf-8") as f:
        # ---------------------------------------------------------------
        # for i, line in enumerate(f):
        #
        # Un simple `for line in f:` ya recorrería el archivo línea por
        # línea (esta es una de las propiedades más útiles de un objeto
        # de archivo abierto en Python — es directamente iterable línea
        # por línea, así que nunca necesitas llamar manualmente a algo
        # como f.readline() dentro de un bucle). Pero también queremos
        # saber en QUÉ número de línea estamos, para poder imprimir algo
        # como "[0]", "[1]", "[2]" y saber cuándo detenernos.
        #
        # enumerate(f) envuelve esa misma iteración línea por línea,
        # pero en lugar de devolver simplemente cada `line`, devuelve un
        # par: (índice, línea) — empezando el índice en 0 por defecto.
        # Escribir `for i, line in enumerate(f):` desempaqueta ese par
        # directamente en dos variables separadas, `i` (la posición, 0,
        # 1, 2, ...) y `line` (el texto real de esa línea).
        # ---------------------------------------------------------------
        for i, line in enumerate(f):
            # Detenerse una vez que hemos impreso el número de líneas
            # solicitado. Sin esto, el bucle seguiría recorriendo el
            # archivo COMPLETO (que podría tener decenas de miles de
            # líneas) aunque solo quisiéramos echar un vistazo rápido a
            # unas pocas.
            if i >= num_lines:
                break

            # Analizar (parsear) esta única línea de texto (un solo
            # objeto JSON, p. ej. {"type": "PushEvent", "actor": {...},
            # ...}) convirtiéndola en un dict de Python, para poder
            # acceder a sus campos con búsquedas entre corchetes a
            # continuación.
            event = json.loads(line)

            # ---------------------------------------------------------------
            # Imprimiendo los campos que nos interesan.
            #
            # event['type']              una búsqueda de dict: 'type' es
            #                            una clave en el objeto JSON de
            #                            nivel superior, p. ej.
            #                            "PushEvent".
            # event['actor']['login']     una búsqueda ANIDADA: 'actor'
            #                            es en sí mismo un dict (un
            #                            objeto dentro del objeto), y
            #                            'login' es una clave dentro de
            #                            ESE dict anidado — esto refleja
            #                            la estructura JSON anidada
            #                            mostrada en gh-archive-guide.md
            #                            (la forma "actor": {"login":
            #                            ...}).
            # event['repo']['name']       la misma idea de búsqueda
            #                            anidada, entrando en el
            #                            subobjeto 'repo'.
            # event['created_at']         de nuevo una búsqueda simple de
            #                            nivel superior.
            #
            # El `!r` dentro de cada marcador de posición del f-string
            # (p. ej. {event['type']!r}) solicita el "repr"
            # (representación) del valor en lugar de su forma de cadena
            # de texto plana. Para las cadenas de texto, esto envuelve el
            # valor entre comillas en la salida (p. ej. 'PushEvent' en
            # lugar de PushEvent), lo que hace visualmente inequívoco
            # dónde termina el valor de un campo y dónde empieza la
            # etiqueta del siguiente campo al examinar la salida
            # impresa.
            #
            # Esta única llamada a print() está dividida en cuatro
            # líneas en el código fuente mediante concatenación implícita
            # de cadenas — Python une automáticamente los literales de
            # cadena adyacentes que aparecen uno junto al otro sin nada
            # más que espacio en blanco/saltos de línea entre ellos, así
            # que esto en realidad es solo un f-string largo escrito en
            # varias líneas por legibilidad.
            # ---------------------------------------------------------------
            print(f"[{i}] type={event['type']!r} "
                  f"actor={event['actor']['login']!r} "
                  f"repo={event['repo']['name']!r} "
                  f"created_at={event['created_at']!r}")


# ---------------------------------------------------------------------
# parse_args(): el mismo patrón general que la versión de
# download_gharchive.py, con dos diferencias que vale la pena señalar:
#
#   type=Path (para --file)
#     Mientras que el argumento --date de download_gharchive.py se
#     mantenía como una cadena de texto simple, aquí le decimos a
#     argparse que convierta el valor de --file directamente en un
#     objeto Path (argparse llamará a Path("lo que sea que escribió el
#     usuario") por nosotros). Eso significa que args.file ya es un Path
#     propiamente dicho en el momento en que peek() lo recibe, en lugar
#     de una cadena cruda que tendríamos que convertir nosotros mismos.
#
#   Sin restricción `choices=` en --lines
#     download_gharchive.py restringía --hour a range(0, 24) porque solo
#     24 valores son siempre válidos. Aquí, --lines es simplemente
#     "cuantas quieras ver" — cualquier entero positivo es razonable, así
#     que no hay un conjunto fijo de opciones válidas al que
#     restringirlo.
# ---------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE,
                         help=f"Path to the JSON Lines file (default: {DEFAULT_FILE})")
    parser.add_argument("--lines", type=int, default=DEFAULT_LINES,
                         help=f"How many events to print (default: {DEFAULT_LINES})")
    return parser.parse_args()


# main() y la protección `if __name__ == "__main__":`: propósito y
# mecánica idénticos a los de download_gharchive.py — ver la copia
# anotada de ese archivo para la explicación completa. En resumen:
# main() conecta el análisis de argumentos con el trabajo real (aquí,
# peek() en lugar de download()), y la protección asegura que ese
# trabajo solo se ejecute cuando este archivo se ejecuta directamente, no
# cuando se importa.
def main() -> None:
    args = parse_args()
    peek(args.file, args.lines)


if __name__ == "__main__":
    main()
