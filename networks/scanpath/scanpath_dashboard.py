"""
scanpath_dashboard.py

Dashboard HTML auto-contenido de las redes de scanpath por texto
(estilo reading_patterns_dashboard): filtros de lengua / texto / cuartil y
dos granos — palabra (layout de mapa de lectura) y tipo de palabra
(layout de muelle, categoria_gramatical).

Salida: networks/scanpath/output/scanpath_dashboard.html

Uso:
  python scanpath_dashboard.py                  # todas las lenguas
  python scanpath_dashboard.py --langs du,ee    # subset (más rápido)
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core import CONDITION_LANGS
from core.dashboard import generate_dashboard


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument(
        "--langs",
        default="all",
        help="lenguas separadas por coma, o 'all' (default 'all')",
    )
    p.add_argument(
        "--out",
        default="scanpath_dashboard.html",
        help="nombre del HTML de salida (en networks/scanpath/output/)",
    )
    args = p.parse_args()

    if args.langs == "all":
        langs = list(CONDITION_LANGS)
    else:
        sel = [s.strip() for s in args.langs.split(",") if s.strip()]
        valid = set(CONDITION_LANGS)
        bad = [s for s in sel if s not in valid]
        if bad:
            sys.exit(f"[error] lenguas desconocidas: {bad}. Válidas: {CONDITION_LANGS}")
        langs = sel

    generate_dashboard(langs, out_name=args.out)


if __name__ == "__main__":
    main()
