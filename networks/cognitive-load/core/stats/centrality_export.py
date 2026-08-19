"""
centrality_export.py

Exportación de CSVs derivados del análisis completo de centralidades.
"""

import csv
import os


def export_centrality_report(
    build_dir,
    degree_df,
    assortativity_results,
    community_map,
    community_summary,
    kcore_dict,
    kcore_df,
    centrality_dict,
    centrality_df,
    rankings_df,
    corr_matrix,
    modularity_score,
    name_suffix="",
):
    """
    Exporta todos los CSVs del análisis de centralidades al subdirectorio stats/.
    """
    stats_dir = os.path.join(build_dir, "stats")
    os.makedirs(stats_dir, exist_ok=True)
    suffix = f"_{name_suffix}" if name_suffix else ""

    # 1. Degree distribution
    _export_df(degree_df, stats_dir, f"degree_distribution{suffix}.csv")

    # 2. Assortativity
    _export_assortativity(assortativity_results, stats_dir, f"assortativity{suffix}.csv")

    # 3. Louvain communities
    _export_louvain(community_map, community_summary, modularity_score,
                    stats_dir, f"louvain_communities{suffix}.csv")

    # 4. K-core values
    _export_df(kcore_df, stats_dir, f"kcore_values{suffix}.csv")

    # 5. All centralities
    _export_df(centrality_df, stats_dir, f"centrality_all{suffix}.csv")

    # 6. Rankings
    _export_df(rankings_df, stats_dir, f"centrality_rankings{suffix}.csv")

    # 7. Correlation matrix
    _export_correlation(corr_matrix, stats_dir, f"centrality_correlation{suffix}.csv")


def _export_df(df, stats_dir, filename):
    """Exporta un DataFrame a CSV."""
    path = os.path.join(stats_dir, filename)
    df.to_csv(path, index=False, encoding="utf-8")
    print(f"[OK] CSV guardado en: {path}")


def _export_assortativity(results, stats_dir, filename):
    """Exporta la asortatividad como CSV de 2 columnas."""
    path = os.path.join(stats_dir, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "coefficient", "p_value"])
        for variant, vals in results.items():
            w.writerow([variant, vals["coefficient"], vals["p_value"]])
    print(f"[OK] CSV guardado en: {path}")


def _export_louvain(community_map, community_summary, modularity_score,
                    stats_dir, filename):
    """Exporta las comunidades Louvain a CSV."""
    path = os.path.join(stats_dir, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        # Cabecera: resumen global
        w = csv.writer(f)
        w.writerow(["# modularity_score", modularity_score])
        w.writerow([])
        # Resumen por comunidad
        if community_summary:
            w.writerow(["community_id", "size", "mean_signal", "words_sample", "wordnum_range"])
            for row in community_summary:
                w.writerow([
                    row["community_id"],
                    row["size"],
                    row["mean_signal"],
                    row["words_sample"],
                    row["wordnum_range"],
                ])
            w.writerow([])
        # Mapeo nodo -> comunidad
        w.writerow(["node_id", "louvain_community_id"])
        for node_id, comm_id in sorted(community_map.items()):
            w.writerow([node_id, comm_id])
    print(f"[OK] CSV guardado en: {path}")


def _export_correlation(corr_matrix, stats_dir, filename):
    """Exporta la matriz de correlación como CSV."""
    path = os.path.join(stats_dir, filename)
    corr_matrix.to_csv(path, encoding="utf-8")
    print(f"[OK] CSV guardado en: {path}")
