"""
regcomp.py

Entry point CLI de la red de regresiones por familia lingüística.

Usage:
  python regcomp.py build   --lang-group <grupo|all> [shared-args]
  python regcomp.py compare [--families f1 f2 ...] [shared-args] [--no-reuse]

Ejemplos:
  python networks/regression-comparison/regcomp.py build --lang-group all --trialid 4 --wave 1
  python networks/regression-comparison/regcomp.py compare --trialid 4 --wave 1
"""

import argparse
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

from core import build_families, run_comparison  # noqa: E402

_DEFAULT_OUTDIR = os.path.join("networks", "regression-comparison", "output")


def _add_shared_args(parser):
    """Argumentos compartidos por los subcomandos build y compare."""
    parser.add_argument(
        "--trialid", type=str, default="1", help="ID de texto [1-12] (por defecto: 1)."
    )
    parser.add_argument(
        "--wave",
        type=str,
        default="1",
        choices=["1", "2"],
        help="Ola a cargar. No se admite 'both': son cohortes independientes.",
    )
    parser.add_argument(
        "--edge-weight",
        type=str,
        default="rate",
        choices=["rate", "count", "dur"],
        help="Peso principal de arista (por defecto: rate).",
    )
    parser.add_argument(
        "--min-rate",
        type=float,
        default=0.02,
        help="Poda aristas soportadas por menos de esta fracción de lectores.",
    )
    parser.add_argument(
        "--no-filter-discordant",
        action="store_true",
        help="No descartar sesiones cuyo texto no coincide con el del trial.",
    )
    parser.add_argument(
        "--outdir", type=str, default=_DEFAULT_OUTDIR, help="Carpeta raíz de salida."
    )
    parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="Omite la generación de network_interactive.html.",
    )


def cmd_build(args):
    """Subcomando build: construye la red de una familia o de todas."""
    built = build_families(
        lang_group=args.lang_group,
        trialid=args.trialid,
        wave=args.wave,
        edge_weight=args.edge_weight,
        min_rate=args.min_rate,
        filter_discordant=not args.no_filter_discordant,
        outdir=args.outdir,
        do_interactive=not args.no_interactive,
        reuse_cache=False,
    )
    print(f"\n{'=' * 62}\n[ÉXITO] {len(built)} red(es) construida(s):")
    for build_dir, _meta in built.values():
        print(f"  - {build_dir}")
    print("=" * 62)


def cmd_compare(args):
    """Subcomando compare: reporte HTML comparativo de todas las familias."""
    comp_dir = run_comparison(
        trialid=args.trialid,
        wave=args.wave,
        families=args.families or "all",
        edge_weight=args.edge_weight,
        min_rate=args.min_rate,
        filter_discordant=not args.no_filter_discordant,
        outdir=args.outdir,
        reuse_cache=not args.no_reuse,
        do_interactive=not args.no_interactive,
    )
    if comp_dir:
        report = os.path.join(comp_dir, "comparison_report.html")
        print(f"[ÉXITO] Abre el reporte desde su carpeta: {report}")


def main():
    parser = argparse.ArgumentParser(
        description="Red de regresiones por familia lingüística (MECO L2)."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="Construye y persiste la red.")
    p_build.add_argument(
        "--lang-group",
        type=str,
        default="germanic",
        help="Familia lingüística o 'all' para construir todas las del wave.",
    )
    _add_shared_args(p_build)
    p_build.set_defaults(func=cmd_build)

    p_cmp = sub.add_parser("compare", help="Reporte HTML comparativo por familia.")
    p_cmp.add_argument(
        "--families",
        nargs="*",
        default=None,
        help="Familias a comparar (separadas por espacios). Por defecto, todas.",
    )
    p_cmp.add_argument(
        "--no-reuse",
        action="store_true",
        help="Reconstruye todas las familias en vez de reutilizar builds existentes.",
    )
    _add_shared_args(p_cmp)
    p_cmp.set_defaults(func=cmd_compare)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
