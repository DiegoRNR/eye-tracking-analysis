"""
langcomp.py

Single CLI entry point for the language-comparison network pipeline.

Usage:
  python langcomp.py build --lang-group <group> [shared-args]
  python langcomp.py stats [--load DIR] [shared-args] [stats-args]

Shared args: --lang-group --trialid --wave --normalize --outdir
Stats-only:  --load --cascade-window --z-thresh --p-thresh --name

Examples:
  python langcomp.py build --lang-group germanic --trialid 4 --wave 1
  python langcomp.py stats --load networks/language-comparison/output/langcomp_trial4_w1_zscore_germanic
"""

import argparse
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

from core import (
    ALL_FAMILIES,
    build_group_network,
    build_prefix,
    check_cache_fresh,
    group_stats_from_cache,
    langs_without_ps,
    load_accuracy,
    load_fixations_by_group,
    normalize_session_ps,
    resolve_group,
    run_comparison,
    save_built_network,
    summarize_accuracy,
    visualize_group_network,
    visualize_group_network_interactive,
)


def _add_shared_args(parser):
    """Argumentos compartidos por los subcomandos build y stats."""
    parser.add_argument(
        "--lang-group",
        type=str,
        default="germanic",
        help="Familia lingüística o 'all'. "
             f"Disponibles: {', '.join(ALL_FAMILIES)}.",
    )
    parser.add_argument(
        "--trialid",
        type=str,
        default="1",
        help="ID de texto [1-12] (por defecto: 1).",
    )
    parser.add_argument(
        "--wave",
        type=str,
        default="1",
        choices=["1", "2", "both"],
        help="Ola(s) a cargar: 1, 2 o 'both'.",
    )
    parser.add_argument(
        "--normalize",
        type=str,
        default="zscore",
        choices=["zscore", "none"],
        help="Normalización de PS por sesión: 'zscore' (default) o 'none' (crudo).",
    )
    parser.add_argument(
        "--outdir",
        type=str,
        default=os.path.join("networks", "language-comparison", "output"),
        help="Carpeta raíz de salida donde se creará la carpeta del build.",
    )


def _add_stats_args(parser):
    """Argumentos exclusivos del subcomando stats."""
    parser.add_argument(
        "--load",
        type=str,
        help="Ruta a una carpeta de build existente (modo cache). Si se omite, se reconstruye desde los args compartidos.",
    )
    parser.add_argument("--cascade-window", type=int, default=4)
    parser.add_argument("--z-thresh", type=float, default=1.0)
    parser.add_argument("--p-thresh", type=float, default=0.05)
    parser.add_argument(
        "--name",
        type=str,
        default="",
        help="Sufijo para nombres de archivos de stats/plots.",
    )


def _build_single_group(
    group, trialid, wave, normalize, outdir, do_interactive=True
):
    """
    Carga fijaciones del grupo, carga accuracy, construye la red, la persiste
    y genera los plots base. Retorna la ruta del build_dir, o None si no se
    encontraron fijaciones.
    """
    try:
        resolve_group(group, wave)
    except ValueError as e:
        print(f"[ERROR] {e}")
        return None

    fixations, source_files, langs = load_fixations_by_group(
        wave=wave,
        group=group,
        trialid=trialid,
    )
    if not fixations:
        print("[!] No se encontraron fijaciones con los criterios especificados.")
        return None

    if normalize == "zscore":
        fixations = normalize_session_ps(fixations)
        for f in fixations:
            f["has_z"] = True
    elif normalize == "none":
        for f in fixations:
            f["ps_z"] = 0.0
            f["has_z"] = False
    else:
        raise ValueError(f"normalize debe ser 'zscore' o 'none', got {normalize!r}")

    acc_map, comp_files = load_accuracy(wave, set(langs))
    accuracy_summary, n_participants, n_with_accuracy = summarize_accuracy(
        acc_map, fixations
    )

    if accuracy_summary.get("mean") is not None:
        print(
            f"--> Accuracy del grupo '{group}': mean={accuracy_summary['mean']}, "
            f"median={accuracy_summary['median']}, n={accuracy_summary['n']}"
        )
    else:
        print("[!] No se pudo calcular accuracy: ningún participante con datos de comprensión.")

    text_label = (
        f"Language-Comparison_{group}_Trial_{trialid}"
    )

    G = build_group_network(
        fixations,
        groupby="all",
        text_label=text_label,
    )

    ps_absent = langs_without_ps(wave)
    prefix = build_prefix(
        lang_group=group,
        trialid=trialid,
        wave=wave,
        normalize=normalize,
        group_langs=langs,
        ps_absent_langs=[l for l in ps_absent if l in resolve_group(group, wave)],
    )

    all_source = list(source_files) + list(comp_files)
    build_dir = save_built_network(
        G,
        output_dir=outdir,
        prefix=prefix,
        source_files=all_source,
        groupby="all",
        wave=wave,
        trialid=trialid,
        lang_group=group,
        languages=langs,
        accuracy_summary=accuracy_summary,
        n_participants=n_participants,
        n_with_accuracy=n_with_accuracy,
        normalize=normalize,
    )

    visualize_group_network(G, build_dir, prefix)

    if do_interactive:
        try:
            from core.interactive_viz import visualize_group_network_interactive
            visualize_group_network_interactive(G, build_dir, prefix)
        except ImportError as e:
            print(f"[!] pyvis no instalado; saltando network_interactive.html ({e}).")
            print("    Instalar con: pip install pyvis")

    return build_dir


def _run_build_pipeline(args, do_interactive=True):
    """Wrapper de _build_single_group a partir de argparse args."""
    return _build_single_group(
        group=args.lang_group,
        trialid=args.trialid,
        wave=args.wave,
        normalize=args.normalize,
        outdir=args.outdir,
        do_interactive=do_interactive,
    )


def build_command(args):
    build_dir = _run_build_pipeline(args, do_interactive=not args.no_interactive)
    if build_dir is None:
        return 0
    print(f"\n[ÉXITO] Build completo. Carpeta: {build_dir}")
    return 0


def stats_command(args):
    if args.load:
        if not os.path.isdir(args.load):
            print(f"[ERROR] No existe la carpeta de build: {args.load}")
            return 1
        meta_path = os.path.join(args.load, "metadata.json")
        meta = None
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        if meta is not None:
            check_cache_fresh(meta, [s["path"] for s in meta.get("source_files", [])])
        stats_dir = args.load
    else:
        build_dir = _run_build_pipeline(args, do_interactive=False)
        if build_dir is None:
            return 0
        stats_dir = build_dir

    group_stats_from_cache(
        stats_dir,
        args.cascade_window,
        args.z_thresh,
        args.p_thresh,
        args.name,
    )
    print(f"\n[ÉXITO] Estadísticas generadas.")
    return 0


def compare_command(args):
    comp_dir = run_comparison(
        trialid=args.trialid,
        wave=args.wave,
        families=args.families,
        normalize=args.normalize,
        outdir=args.outdir,
        reuse_cache=not args.no_reuse,
        do_interactive=not args.no_interactive,
    )
    if comp_dir is None:
        return 0
    print(f"\n[ÉXITO] Comparación generada en: {comp_dir}")
    print(f"    Abrir: {os.path.join(comp_dir, 'comparison_report.html')}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="langcomp",
        description="Pipeline de Red de Carga Cognitiva por Familias Lingüísticas (MECO L2).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_p = subparsers.add_parser(
        "build",
        help="Construir y persistir la red de un grupo de lenguas.",
    )
    _add_shared_args(build_p)
    build_p.add_argument(
        "--no-interactive",
        action="store_true",
        help="Omite la generación del HTML interactivo (network_interactive.html).",
    )

    stats_p = subparsers.add_parser(
        "stats",
        help="Calcular estadísticas, cascadas y modularidad.",
    )
    _add_shared_args(stats_p)
    _add_stats_args(stats_p)

    compare_p = subparsers.add_parser(
        "compare",
        help="Comparar familias: una red por familia + reporte HTML.",
    )
    compare_p.add_argument(
        "--trialid",
        type=str,
        default="1",
        help="ID de texto [1-12] (por defecto: 1).",
    )
    compare_p.add_argument(
        "--wave",
        type=str,
        default="1",
        choices=["1", "2", "both"],
        help="Ola(s) a cargar: 1, 2 o 'both'.",
    )
    compare_p.add_argument(
        "--families",
        type=str,
        nargs="*",
        default=None,
        help="Familias a comparar (separadas por espacios; default: todas). "
             f"Disponibles: {', '.join(ALL_FAMILIES)}.",
    )
    compare_p.add_argument(
        "--normalize",
        type=str,
        default="zscore",
        choices=["zscore", "none"],
        help="Normalización de PS por sesión.",
    )
    compare_p.add_argument(
        "--outdir",
        type=str,
        default=os.path.join("networks", "language-comparison", "output"),
        help="Carpeta raíz de salida.",
    )
    compare_p.add_argument(
        "--no-reuse",
        action="store_true",
        help="Reconstruye todas las familias (ignora builds existentes).",
    )
    compare_p.add_argument(
        "--no-interactive",
        action="store_true",
        help="Omite la generación del HTML interactivo de cada familia.",
    )

    args = parser.parse_args(argv)
    if args.command == "build":
        return build_command(args)
    if args.command == "stats":
        return stats_command(args)
    if args.command == "compare":
        return compare_command(args)
    parser.error(f"Subcomando desconocido: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
