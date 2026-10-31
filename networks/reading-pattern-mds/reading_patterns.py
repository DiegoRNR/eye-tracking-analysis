"""
networks/reading-pattern-mds/reading_patterns.py

Entry point CLI. La lógica vive en core/.

Compara patrones de lectura (distribuciones de transición entre tipos de
palabra, mismas que networks/word-type-transitions) de cada grupo lingüístico
contra los cohortes nativos de inglés en_ca (grupo "en", wave 1) y en_uk
(wave 2), y los proyecta en MDS 2-D (distancia = Jensen–Shannon).

Subcomandos:
- build:     perfiles pooled (full y Q1/Q4) + matrices de distancia CSV.
- figures:   variantes de figuras MDS (l1/l2 vs nativos, por lengua, cuartiles).
- dashboard: dashboard HTML interactivo (filtros por lengua/sesión/cuartil,
             modo de color por distancia lingüística, correlaciones).
- all:       build + figures + dashboard.

Uso:
    python reading_patterns.py all --mode temporal
    python reading_patterns.py build --mode regression
    python reading_patterns.py figures --mode temporal
    python reading_patterns.py dashboard            (ambos modos)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("subcommand", choices=["build", "figures", "dashboard", "all"])
    parser.add_argument("--mode", choices=["temporal", "regression"], default="temporal")
    args = parser.parse_args()

    from core import app

    if args.subcommand in ("build", "all"):
        app.build_all(args.mode)
    if args.subcommand in ("figures", "all"):
        app.figures_all(args.mode)
    if args.subcommand == "dashboard":
        from core.dashboard import generate_dashboard

        generate_dashboard()
    if args.subcommand == "all":
        from core.dashboard import generate_dashboard

        generate_dashboard()
    return 0


if __name__ == "__main__":
    sys.exit(main())
