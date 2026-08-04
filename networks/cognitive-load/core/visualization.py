"""
visualization.py

Plots base de la red de carga cognitiva: series temporales, heatmap y grafo.
"""

import math
import os
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import seaborn as sns


def visualize_cogload_network(G, build_dir, prefix):
    """Genera los plots base de la red (series temporales, heatmap y grafo)."""
    plots_dir = os.path.join(build_dir, "plots")
    os.makedirs(plots_dir, exist_ok=True)

    if G.number_of_nodes() == 0:
        print("[!] Red vacía, no se generan visualizaciones.")
        return

    node_items = list(G.nodes(data=True))

    wordnums = []
    sents = []
    means = []
    means_z = []
    for _, d in node_items:
        wn = d.get("wordnum", 0)
        sn = d.get("sentnum", 1)
        mp = d.get("mean_ps", 0.0)
        mz = d.get("mean_ps_z", 0.0)
        if mp > 0:
            wordnums.append(wn)
            sents.append(sn)
            means.append(mp)
            means_z.append(mz)

    order = np.argsort(wordnums)
    wordnums_arr = np.array(wordnums)[order]
    sents_arr = np.array(sents)[order]
    means_arr = np.array(means)[order]
    means_z_arr = np.array(means_z)[order]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7), sharex=True)
    ax1.plot(
        wordnums_arr,
        means_arr,
        color="#2980b9",
        linewidth=1.2,
        marker="o",
        markersize=3,
    )
    ax1.set_title(f"Series temporales de PS por palabra — {prefix}", fontsize=12)
    ax1.set_ylabel("PS crudo (mean_ps)")
    ax1.grid(True, linestyle=":", alpha=0.4)

    ax2.plot(
        wordnums_arr,
        means_z_arr,
        color="#c0392b",
        linewidth=1.2,
        marker="o",
        markersize=3,
    )
    ax2.axhline(0, color="#7f8c8d", linewidth=0.8, linestyle="-")
    ax2.axhline(1, color="#7f8c8d", linewidth=0.6, linestyle="--", alpha=0.5)
    ax2.axhline(-1, color="#7f8c8d", linewidth=0.6, linestyle="--", alpha=0.5)
    ax2.set_xlabel("Posición de palabra (wordnum)")
    ax2.set_ylabel("PS z-score (mean_ps_z)")
    ax2.grid(True, linestyle=":", alpha=0.4)

    sent_breaks = np.where(np.diff(sents_arr) != 0)[0]
    for sb in sent_breaks:
        for ax in (ax1, ax2):
            ax.axvline(
                wordnums_arr[sb] + 0.5, color="#7f8c8d", linestyle="--", alpha=0.5
            )
    fig.tight_layout()
    ts_path = os.path.join(plots_dir, "ps_timeseries.png")
    fig.savefig(ts_path, dpi=200)
    plt.close(fig)
    print(f"[OK] Serie temporal PS guardada en: {ts_path}")

    pivot_data = defaultdict(dict)
    for _, d in node_items:
        if d.get("mean_ps", 0) <= 0:
            continue
        wn = int(d.get("wordnum", 0))
        sn = int(d.get("sentnum", 1))
        pivot_data[sn][wn] = d["mean_ps"]
    if pivot_data:
        all_sents = sorted(pivot_data.keys())
        all_words = sorted({wn for s in all_sents for wn in pivot_data[s].keys()})
        matrix = np.full((len(all_sents), len(all_words)), np.nan)
        for i, s in enumerate(all_sents):
            for j, w in enumerate(all_words):
                v = pivot_data[s].get(w)
                if v is not None:
                    matrix[i, j] = v
        fig, ax = plt.subplots(figsize=(max(8, len(all_words) * 0.2), max(4, len(all_sents) * 0.4)))
        sns.heatmap(
            matrix,
            cmap="viridis",
            ax=ax,
            cbar_kws={"label": "mean_ps"},
            mask=np.isnan(matrix),
        )
        ax.set_title(f"Mapa de calor de PS — {prefix}", fontsize=12)
        ax.set_xlabel("Posición de palabra (wordnum)")
        ax.set_ylabel("Oración (sentnum)")
        fig.tight_layout()
        heat_path = os.path.join(plots_dir, "ps_heatmap.png")
        fig.savefig(heat_path, dpi=200)
        plt.close(fig)
        print(f"[OK] Heatmap PS guardado en: {heat_path}")

    pos = {}
    for n, d in G.nodes(data=True):
        try:
            x = int(d.get("wordnum", 0))
            y = -int(d.get("sentnum", 1))
        except (ValueError, TypeError):
            x, y = 0, 0
        pos[n] = (x, y)

    node_colors = [d.get("mean_ps", 0.0) for _, d in node_items]
    node_sizes = [
        30 + 60 * min(1.0, d.get("fix_count", 0) / 20.0) for _, d in node_items
    ]
    edge_widths = [
        max(0.3, min(3.0, math.log1p(d.get("count", 1)) * 0.6))
        for _, _, d in G.edges(data=True)
    ]
    edge_colors = [d.get("mean_dps", 0.0) for _, _, d in G.edges(data=True)]

    fig, ax = plt.subplots(figsize=(14, 7))
    nodes_collection = nx.draw_networkx_nodes(
        G,
        pos,
        node_color=node_colors,
        node_size=node_sizes,
        cmap=plt.cm.viridis,
        alpha=0.85,
        ax=ax,
    )
    if edge_widths:
        from matplotlib.collections import LineCollection
        edge_segs = []
        for (u, v), color, width in zip(G.edges(), edge_colors, edge_widths):
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_segs.append([(x0, y0), (x1, y1)])
        if edge_segs:
            ec_min = min(edge_colors)
            ec_max = max(edge_colors)
            ec_range = ec_max - ec_min if ec_max > ec_min else 1.0
            edges_collection = LineCollection(
                edge_segs,
                cmap=plt.cm.coolwarm,
                linewidths=edge_widths,
                array=[(c - ec_min) / ec_range for c in edge_colors],
                alpha=0.5,
            )
            ax.add_collection(edges_collection)
            cb_e = plt.colorbar(edges_collection, ax=ax, fraction=0.03, pad=0.02)
            cb_e.set_label("mean_dps (ΔPS promedio)")
    if nodes_collection is not None:
        cb_n = plt.colorbar(nodes_collection, ax=ax, fraction=0.03, pad=0.04)
        cb_n.set_label("mean_ps (PS promedio)")

    ax.set_title(f"Red de Carga Cognitiva — {prefix}", fontsize=12)
    ax.set_xlabel("Posición de palabra (wordnum)")
    ax.set_ylabel("Oración (sentnum, invertido)")
    ax.grid(True, linestyle=":", alpha=0.3)
    fig.tight_layout()
    net_path = os.path.join(plots_dir, "network.png")
    fig.savefig(net_path, dpi=200)
    plt.close(fig)
    print(f"[OK] Visualización de la red guardada en: {net_path}")
