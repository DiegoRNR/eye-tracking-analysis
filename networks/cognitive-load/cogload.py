"""
cogload.py

CLI entry point para el pipeline de red de carga cognitiva.

Uso:
  python cogload.py build [shared-build-args]
  python cogload.py stats [--load DIR] [shared-build-args] [stats-args]
  python cogload.py analysis [--load DIR] [--outdir DIR] [--name SUFIJO] [--top-n N]

Shared build args: --subid --lang --trialid --itemid --wave --groupby
                   --normalize --edge-mode --edge-window --outdir
Stats-only args:   --load --cascade-window --z-thresh --p-thresh --name
Analysis args:     --load --outdir --name --top-n
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
    analysis_from_cache,
    build_cogload_network,
    build_prefix,
    check_cache_fresh,
    load_all_fixations,
    save_built_network,
    stats_from_cache,
    visualize_cogload_network,
)


def _add_shared_args(parser):
    """Argumentos compartidos por los subcomandos build y stats."""
    parser.add_argument("--subid", type=str, help="Filtrar por participante (uniform_id, ej. du_4).")
    parser.add_argument("--lang", type=str, help="Filtrar por L1 (ej. du, es, de, it).")
    parser.add_argument("--trialid", type=str, default="1", help="ID de texto [1-12] (por defecto: 1).")
    parser.add_argument("--itemid", type=str, help="ID del item/texto (alias de trialid, más preciso).")
    parser.add_argument(
        "--wave",
        type=str,
        default="both",
        choices=["1", "2", "both"],
        help="Ola(s) a cargar: 1, 2 o 'both' (por defecto).",
    )
    parser.add_argument(
        "--groupby",
        type=str,
        default="all",
        choices=["participant", "lang", "all"],
        help="Agregación de sesiones: participant, lang o all (por defecto).",
    )
    parser.add_argument(
        "--normalize",
        type=str,
        default="zscore",
        choices=["zscore", "robust", "none"],
        help="Normalización de PS por sesión: 'zscore' (default), 'robust' o 'none' (crudo).",
    )
    parser.add_argument(
        "--edge-mode",
        type=str,
        default="temporal",
        choices=["textual", "temporal", "refixations", "regressions"],
        help="Modo de aristas: 'textual' (adyacencia lineal), 'temporal' (navegación completa), 'refixations' (relecturas), 'regressions' (saltos atrás).",
    )
    parser.add_argument(
        "--edge-window",
        type=int,
        default=4,
        help="Tamaño de ventana hacia adelante (reservado para uso futuro, default 4).",
    )
    parser.add_argument(
        "--outdir",
        type=str,
        default=os.path.join("networks", "cognitive-load", "output"),
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


def _run_build_pipeline(args, do_interactive=True, within_sentence=False):
    """
    Carga fijaciones, construye la red, la persiste y genera los plots base.
    """
    fixations, source_files = load_all_fixations(
        wave=args.wave,
        uniform_id=args.subid,
        lang=args.lang,
        trialid=args.itemid or args.trialid,
        normalize=args.normalize,
    )
    if not fixations:
        print("[!] No se encontraron fijaciones con los criterios especificados.")
        return None

    trialid_for_label = args.itemid or args.trialid
    text_label = f"Trial_{trialid_for_label}"
    if args.lang:
        text_label += f"_Lang_{args.lang}"
    if args.subid:
        text_label += f"_Sub_{args.subid}"

    G = build_cogload_network(
        fixations,
        groupby=args.groupby,
        text_label=text_label,
        edge_mode=args.edge_mode,
        edge_window=args.edge_window,
        within_sentence=within_sentence,
    )

    prefix = build_prefix(args, within_sentence=within_sentence)
    build_dir = save_built_network(
        G,
        output_dir=args.outdir,
        prefix=prefix,
        source_files=source_files,
        groupby=args.groupby,
        wave=args.wave,
        subid=args.subid,
        lang=args.lang,
        trialid=args.itemid or args.trialid,
        normalize=args.normalize,
        edge_mode=args.edge_mode,
        edge_window=args.edge_window,
    )

    visualize_cogload_network(G, build_dir, prefix)

    if do_interactive:
        try:
            from core.interactive_viz import visualize_network_interactive
            visualize_network_interactive(G, build_dir, prefix)
        except ImportError as e:
            print(f"[!] pyvis no instalado; saltando network_interactive.html ({e}).")
            print("    Instalar con: pip install pyvis")

    return build_dir


def build_command(args):
    build_dir = _run_build_pipeline(
        args,
        do_interactive=not args.no_interactive,
        within_sentence=args.per_sentence,
    )
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
        build_dir = _run_build_pipeline(args, do_interactive=False, within_sentence=False)
        if build_dir is None:
            return 0
        stats_dir = build_dir

    stats_from_cache(
        stats_dir,
        args.cascade_window,
        args.z_thresh,
        args.p_thresh,
        args.name,
    )
    print(f"\n[ÉXITO] Estadísticas generadas.")
    return 0


def analysis_command(args):
    """Ejecuta el análisis completo: centralidades, Louvain, k-core, asortatividad."""
    import glob as globmod

    build_dirs = []

    if args.load:
        # Modo cache: un solo build
        if not os.path.isdir(args.load):
            print(f"[ERROR] No existe la carpeta de build: {args.load}")
            return 1
        meta_path = os.path.join(args.load, "metadata.json")
        if os.path.exists(meta_path):
            import json
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            check_cache_fresh(meta, [s["path"] for s in meta.get("source_files", [])])
        build_dirs = [args.load]
    else:
        # Analizar todos los builds en outdir que empiecen con 'cogload_'
        pattern = os.path.join(args.outdir, "nav_*")
        build_dirs = sorted(globmod.glob(pattern))
        build_dirs = [d for d in build_dirs if os.path.isdir(d)]

    if not build_dirs:
        print("[!] No se encontraron builds para analizar.")
        return 1

    print(f"--> Analizando {len(build_dirs)} build(s)...\n")

    for bd in build_dirs:
        print(f"\n{'=' * 60}")
        print(f"ANALIZANDO: {os.path.basename(bd)}")
        print(f"{'=' * 60}")
        try:
            analysis_from_cache(bd, name_suffix=args.name, top_n=args.top_n)
        except Exception as e:
            print(f"[ERROR] Fallo al analizar {bd}: {e}")

    print(f"\n[ÉXITO] Análisis completado para {len(build_dirs)} build(s).")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="cogload",
        description="Pipeline de Red de Carga Cognitiva Pupilo-dilatada (MECO L2).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_p = subparsers.add_parser(
        "build",
        help="Construir y persistir la red de carga cognitiva.",
    )
    _add_shared_args(build_p)
    build_p.add_argument(
        "--no-interactive",
        action="store_true",
        help="Omite la generación del HTML interactivo (network_interactive.html).",
    )
    build_p.add_argument(
        "--per-sentence",
        action="store_true",
        help="Restringe aristas a dentro de la oración.",
    )

    stats_p = subparsers.add_parser(
        "stats",
        help="Calcular estadísticas, cascadas y modularidad.",
    )
    _add_shared_args(stats_p)
    _add_stats_args(stats_p)

    analysis_p = subparsers.add_parser(
        "analysis",
        help="Análisis completo: centralidades, Louvain, k-core, asortatividad.",
    )
    analysis_p.add_argument(
        "--load",
        type=str,
        help="Ruta a una carpeta de build existente. Si se omite, analiza todos los builds en outdir.",
    )
    analysis_p.add_argument(
        "--outdir",
        type=str,
        default=os.path.join("networks", "cognitive-load", "output"),
        help="Carpeta raíz donde buscar builds (default: networks/cognitive-load/output).",
    )
    analysis_p.add_argument(
        "--name",
        type=str,
        default="",
        help="Sufijo para nombres de archivos de stats/plots.",
    )
    analysis_p.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Cantidad de nodos en los rankings de centralidad (default: 10).",
    )

    args = parser.parse_args(argv)
    if args.command == "build":
        return build_command(args)
    if args.command == "stats":
        return stats_command(args)
    if args.command == "analysis":
        return analysis_command(args)
    parser.error(f"Subcomando desconocido: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
