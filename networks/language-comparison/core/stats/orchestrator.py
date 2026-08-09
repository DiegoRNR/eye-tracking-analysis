"""
orchestrator.py

Compone los módulos de stats: carga la red persistida, calcula métricas,
comunidades, cascadas, exports y plots, e imprime un resumen.
"""

import os

from ..data_io import load_fixations_from_cache_metadata, normalize_session_ps
from ..persistence import load_built_network
from .cascades import detect_group_cascades
from .exports import export_group_report
from .metrics import compute_group_metrics
from .modularity import compute_effort_modularity
from .viz import (
    visualize_group_cascades,
    visualize_group_community_along_text,
)


def group_stats_from_cache(
    build_dir, cascade_window, z_thresh, p_thresh, name_suffix
):
    """Carga la red persistida y calcula/exporta todas las estadísticas."""
    G, metadata = load_built_network(build_dir)

    print(f"--> Calculando métricas de red...")
    metrics = compute_group_metrics(G)

    print(f"--> Detectando comunidades (modularidad del esfuerzo)...")
    community_summary, modularity_score = compute_effort_modularity(G)
    metrics["modularity"] = round(modularity_score, 4)

    print(
        f"--> Detectando cascadas (window={cascade_window}, "
        f"z_thresh={z_thresh}, p_thresh={p_thresh})..."
    )

    fixations = []
    sources = []
    normalize = (metadata or {}).get("normalize", "zscore")
    if metadata and "source_files" in metadata:
        for src in metadata["source_files"]:
            p = src["path"]
            if os.path.exists(p):
                w = 1 if "wave-1" in p else 2
                fixations.extend(
                    load_fixations_from_cache_metadata(
                        p, w, metadata
                    )
                )
                sources.append(p)
    if normalize == "zscore" and fixations:
        fixations = normalize_session_ps(fixations)
        for f in fixations:
            f["has_z"] = True
    elif fixations:
        for f in fixations:
            f.setdefault("ps_z", 0.0)
            f["has_z"] = False
    if not fixations:
        print(
            "[!] No se pudieron recargar fijaciones desde metadata; "
            "las cascadas se omitirán."
        )
        cascades = []
    else:
        cascades = detect_group_cascades(
            fixations,
            G,
            window=cascade_window,
            z_thresh=z_thresh,
            p_thresh=p_thresh,
        )

    print(
        f"--> {len(cascades)} picos evaluados, "
        f"{sum(1 for c in cascades if c['is_cascade'])} cascadas confirmadas."
    )

    export_group_report(
        G,
        metrics,
        cascades,
        community_summary,
        build_dir,
        name_suffix=name_suffix,
        modularity_score=modularity_score,
    )
    visualize_group_cascades(cascades, build_dir, name_suffix=name_suffix)
    visualize_group_community_along_text(G, build_dir, name_suffix=name_suffix)

    print("\n" + "=" * 60)
    print(f"RESUMEN DE MÉTRICAS: {os.path.basename(build_dir)}")
    print("=" * 60)
    for k, v in metrics.items():
        print(f"  {k:25s}: {v}")
    print("=" * 60 + "\n")

    return metrics, cascades, community_summary
