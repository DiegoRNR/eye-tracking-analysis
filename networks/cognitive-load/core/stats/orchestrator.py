"""
orchestrator.py

Compone los módulos de stats: carga la red persistida, calcula métricas,
comunidades, cascadas, exports y plots, e imprime un resumen.
"""

import os

from ..data_io import load_fixations_from_cache_metadata, normalize_session_ps
from ..persistence import load_built_network
from .cascades import detect_cognitive_load_cascades
from .exports import export_cogload_report
from .metrics import compute_cogload_metrics
from .modularity import compute_effort_modularity
from .viz import visualize_cogload_cascades, visualize_community_along_text

from .centrality import (
    compute_all_centralities,
    compute_assortativity,
    compute_assortativity_neighbor_degree,
    compute_centrality_correlations,
    compute_degree_distribution,
    compute_kcore_decomposition,
    compute_louvain_communities,
    build_centrality_rankings,
)
from .centrality_export import export_centrality_report
from .centrality_viz import (
    plot_assortativity,
    plot_centrality_correlation,
    plot_centrality_distributions,
    plot_centrality_rankings,
    plot_degree_distribution,
    plot_kcore_decomposition,
    plot_louvain_communities,
)


def stats_from_cache(
    build_dir, cascade_window, z_thresh, p_thresh, name_suffix
):
    """Carga la red persistida y calcula/exporta todas las estadísticas."""
    G, metadata = load_built_network(build_dir)

    print(f"--> Calculando métricas de red...")
    metrics = compute_cogload_metrics(G)

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
        cascades = detect_cognitive_load_cascades(
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

    export_cogload_report(
        G,
        metrics,
        cascades,
        community_summary,
        build_dir,
        name_suffix=name_suffix,
        modularity_score=modularity_score,
    )
    visualize_cogload_cascades(cascades, build_dir, name_suffix=name_suffix)
    visualize_community_along_text(G, build_dir, name_suffix=name_suffix)

    print("\n" + "=" * 60)
    print(f"RESUMEN DE MÉTRICAS: {os.path.basename(build_dir)}")
    print("=" * 60)
    for k, v in metrics.items():
        print(f"  {k:25s}: {v}")
    print("=" * 60 + "\n")

    return metrics, cascades, community_summary


# ---------------------------------------------------------------------------
# Análisis completo: centralidades, Louvain, k-core, asortatividad
# ---------------------------------------------------------------------------

def analysis_from_cache(build_dir, name_suffix="", top_n=10):
    """
    Ejecuta el análisis completo de la red: distribución de grado,
    asortatividad, comunidades Louvain, k-core decomposition y
    todas las centralidades. Genera CSVs y gráficos.
    """
    G, metadata = load_built_network(build_dir)
    prefix = os.path.basename(build_dir)
    plots_dir = os.path.join(build_dir, "plots")
    os.makedirs(plots_dir, exist_ok=True)

    if G.number_of_nodes() == 0:
        print("[!] Red vacía; análisis omitido.")
        return {}

    # 1. Distribución de grado
    print(f"--> Calculando distribución de grado...")
    degree_df = compute_degree_distribution(G)
    plot_degree_distribution(degree_df, plots_dir, prefix)

    # 2. Asortatividad
    print(f"--> Calculando asortatividad...")
    assortativity_results = compute_assortativity(G)
    assort_df = compute_assortativity_neighbor_degree(G)
    plot_assortativity(assort_df, assortativity_results, plots_dir, prefix)

    # 3. Comunidades Louvain
    print(f"--> Detectando comunidades Louvain...")
    community_map, community_summary, modularity_score = (
        compute_louvain_communities(G)
    )
    plot_louvain_communities(G, community_map, plots_dir, prefix)

    # 4. K-core decomposition
    print(f"--> Calculando k-core decomposition...")
    kcore_dict, kcore_df = compute_kcore_decomposition(G)
    plot_kcore_decomposition(G, kcore_df, plots_dir, prefix)

    # 5. Centralidades
    print(f"--> Calculando centralidades...")
    centrality_dict, centrality_df = compute_all_centralities(G)
    plot_centrality_distributions(centrality_dict, plots_dir, prefix)

    # 6. Rankings
    print(f"--> Generando rankings de centralidades...")
    rankings_df = build_centrality_rankings(centrality_dict, top_n=top_n)
    plot_centrality_rankings(centrality_dict, plots_dir, prefix, top_n=top_n)

    # 7. Correlaciones
    print(f"--> Calculando correlaciones de centralidades...")
    corr_matrix = compute_centrality_correlations(centrality_dict)
    plot_centrality_correlation(corr_matrix, plots_dir, prefix)

    # 8. Exportar CSVs
    print(f"--> Exportando CSVs de análisis...")
    export_centrality_report(
        build_dir=build_dir,
        degree_df=degree_df,
        assortativity_results=assortativity_results,
        community_map=community_map,
        community_summary=community_summary,
        kcore_dict=kcore_dict,
        kcore_df=kcore_df,
        centrality_dict=centrality_dict,
        centrality_df=centrality_df,
        rankings_df=rankings_df,
        corr_matrix=corr_matrix,
        modularity_score=modularity_score,
        name_suffix=name_suffix,
    )

    # Resumen
    print("\n" + "=" * 60)
    print(f"ANÁLISIS COMPLETO: {prefix}")
    print("=" * 60)
    print(f"  Nodos:                {G.number_of_nodes()}")
    print(f"  Aristas:              {G.number_of_edges()}")
    print(f"  Comunidades Louvain:  {len(community_summary)}")
    print(f"  Modularidad:          {modularity_score}")
    print(f"  K-core max (total):   {kcore_df['kcore_total'].max()}")
    print(f"  K-core max (in):      {kcore_df['kcore_in'].max()}")
    print(f"  K-core max (out):     {kcore_df['kcore_out'].max()}")
    for variant, vals in assortativity_results.items():
        print(f"  Asortatividad {variant:6s}: r={vals['coefficient']:+.4f} (p={vals['p_value']:.4f})")
    print(f"  Centralidades:        {', '.join(centrality_dict.keys())}")
    print("=" * 60 + "\n")

    return {
        "degree_df": degree_df,
        "assortativity": assortativity_results,
        "community_map": community_map,
        "community_summary": community_summary,
        "modularity_score": modularity_score,
        "kcore_dict": kcore_dict,
        "kcore_df": kcore_df,
        "centrality_dict": centrality_dict,
        "centrality_df": centrality_df,
        "rankings_df": rankings_df,
        "corr_matrix": corr_matrix,
    }
