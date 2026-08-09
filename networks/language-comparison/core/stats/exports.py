"""
exports.py

Exportación de los CSVs derivados al subdirectorio stats/ del build.
"""

import csv
import os


def export_group_report(
    G,
    metrics,
    cascades,
    community_summary,
    build_dir,
    name_suffix="",
    modularity_score=0.0,
):
    """
    Exporta los CSVs derivados al subdirectorio stats/ del build.
    """
    stats_dir = os.path.join(build_dir, "stats")
    os.makedirs(stats_dir, exist_ok=True)
    suffix = f"_{name_suffix}" if name_suffix else ""

    g_path = os.path.join(stats_dir, f"global_metrics{suffix}.csv")
    with open(g_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value"])
        for k, v in metrics.items():
            w.writerow([k, v])
    print(f"[OK] Métricas globales guardadas en: {g_path}")

    n_path = os.path.join(stats_dir, f"node_metrics{suffix}.csv")
    with open(n_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "node_id",
                "word",
                "wordnum",
                "sentnum",
                "fix_count",
                "dwell_total",
                "mean_dur",
                "mean_ps",
                "ps_std",
                "ps_max",
                "ps_obs",
                "mean_ps_z",
                "ps_z_std",
                "ps_z_max",
                "strength_in",
                "strength_out",
                "ps_zscore",
                "is_ps_peak",
                "community_id",
                "community_label",
            ]
        )
        for n, d in G.nodes(data=True):
            w.writerow(
                [
                    n,
                    d.get("word", ""),
                    d.get("wordnum", 0),
                    d.get("sentnum", 1),
                    d.get("fix_count", 0),
                    round(d.get("dwell_total", 0.0), 2),
                    round(d.get("mean_dur", 0.0), 2),
                    round(d.get("mean_ps", 0.0), 2),
                    round(d.get("ps_std", 0.0), 2),
                    round(d.get("ps_max", 0.0), 2),
                    d.get("ps_obs", 0),
                    round(d.get("mean_ps_z", 0.0), 4),
                    round(d.get("ps_z_std", 0.0), 4),
                    round(d.get("ps_z_max", 0.0), 4),
                    round(d.get("strength_in", 0.0), 4),
                    round(d.get("strength_out", 0.0), 4),
                    round(d.get("ps_zscore", 0.0), 4),
                    d.get("is_ps_peak", False),
                    d.get("community_id", -1),
                    d.get("community_label", "neutral"),
                ]
            )
    print(f"[OK] Métricas de nodo guardadas en: {n_path}")

    e_path = os.path.join(stats_dir, f"edge_list{suffix}.csv")
    with open(e_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            ["source", "target", "mean_dps", "count", "n_sessions", "type"]
        )
        for u, v, d in G.edges(data=True):
            w.writerow(
                [
                    u,
                    v,
                    round(d.get("mean_dps", 0.0), 4),
                    d.get("count", 0),
                    d.get("n_sessions", 0),
                    d.get("type", "forward"),
                ]
            )
    print(f"[OK] Lista de aristas guardada en: {e_path}")

    if cascades is not None:
        c_path = os.path.join(stats_dir, f"cascades{suffix}.csv")
        with open(c_path, "w", newline="", encoding="utf-8") as f:
            if cascades:
                w = csv.DictWriter(f, fieldnames=list(cascades[0].keys()))
                w.writeheader()
                for row in cascades:
                    w.writerow(row)
            else:
                w = csv.writer(f)
                w.writerow(
                    [
                        "uniform_id",
                        "lang",
                        "trialid",
                        "wave",
                        "peak_sentnum",
                        "peak_wordnum",
                        "peak_ps",
                        "window_mean_signal",
                        "baseline_mean_signal",
                        "signal_field",
                        "window_size",
                        "p_value",
                        "t_stat",
                        "is_cascade",
                        "propagation_depth",
                    ]
                )
        print(f"[OK] Cascadas guardadas en: {c_path}")

    if community_summary:
        cs_path = os.path.join(stats_dir, f"community_summary{suffix}.csv")
        with open(cs_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(community_summary[0].keys()))
            w.writeheader()
            for row in community_summary:
                w.writerow(row)
        print(f"[OK] Resumen de comunidades guardado en: {cs_path}")
