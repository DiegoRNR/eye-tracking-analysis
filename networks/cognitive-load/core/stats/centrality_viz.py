"""
centrality_viz.py

Gráficos de matplotlib/seaborn para el análisis completo de centralidades,
distribución de grado, asortatividad, Louvain y k-core.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import seaborn as sns


_PLOT_STYLE = {
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linestyle": ":",
    "font.size": 10,
}


def _save_fig(fig, plots_dir, name):
    path = os.path.join(plots_dir, f"{name}.png")
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] Plot guardado en: {path}")
    return path


# ---------------------------------------------------------------------------
# 1. Distribución de grado
# ---------------------------------------------------------------------------

def plot_degree_distribution(degree_df, plots_dir, prefix=""):
    """
    Histograma de in-degree y out-degree con CCDF superpuesto.
    """
    if degree_df.empty:
        return

    with plt.rc_context(_PLOT_STYLE):
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        fig.suptitle(f"Distribución de Grado — {prefix}", fontsize=12, y=1.02)

        for ax, col, title, color in [
            (axes[0], "in_degree", "In-Degree", "#2980b9"),
            (axes[1], "out_degree", "Out-Degree", "#c0392b"),
        ]:
            vals = degree_df[col].values
            # Histograma
            ax.hist(vals, bins=max(1, int(vals.max()) + 1), color=color,
                    alpha=0.7, edgecolor="white", linewidth=0.5, label="Frecuencia")
            ax.set_xlabel(f"{title}")
            ax.set_ylabel("Frecuencia")
            ax.set_title(title)

            # CCDF en eje secundario
            ax2 = ax.twinx()
            sorted_vals = np.sort(vals)[::-1]
            ccdf_y = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)
            ax2.plot(sorted_vals, ccdf_y, color="black", linewidth=1.5,
                     linestyle="--", alpha=0.7, label="CCDF")
            ax2.set_ylabel("CCDF")
            ax2.set_ylim(0, 1.05)

        fig.tight_layout()
        _save_fig(fig, plots_dir, "degree_distribution")


# ---------------------------------------------------------------------------
# 2. Asortatividad (scatter)
# ---------------------------------------------------------------------------

def plot_assortativity(assort_df, assortativity_results, plots_dir, prefix=""):
    """
    Scatter degree vs mean_neighbor_degree con línea de regresión.
    """
    if assort_df.empty:
        return

    with plt.rc_context(_PLOT_STYLE):
        fig, ax = plt.subplots(figsize=(7, 6))
        fig.suptitle(f"Asortatividad por Grado — {prefix}", fontsize=12, y=1.02)

        x = assort_df["degree"].values
        y = assort_df["mean_neighbor_degree"].values

        ax.scatter(x, y, alpha=0.5, s=30, c="#2980b9", edgecolors="white",
                   linewidth=0.3)

        # Línea de regresión
        mask = (x > 0) & (y > 0)
        if mask.sum() > 2:
            z = np.polyfit(x[mask], y[mask], 1)
            p = np.poly1d(z)
            x_line = np.linspace(x[mask].min(), x[mask].max(), 100)
            ax.plot(x_line, p(x_line), color="#c0392b", linewidth=2,
                    linestyle="--", label=f"regresión (m={z[0]:.3f})")

        total_coef = assortativity_results.get("total", {}).get("coefficient", 0)
        total_p = assortativity_results.get("total", {}).get("p_value", 1)
        ax.text(0.02, 0.98,
                f"r = {total_coef:.4f}\np = {total_p:.4f}",
                transform=ax.transAxes, verticalalignment="top",
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
                fontsize=10)

        ax.set_xlabel("Grado del nodo")
        ax.set_ylabel("Grado promedio de vecinos")
        ax.legend(loc="upper right", fontsize=9)
        fig.tight_layout()
        _save_fig(fig, plots_dir, "assortativity")


# ---------------------------------------------------------------------------
# 3. Comunidades Louvain (grafo)
# ---------------------------------------------------------------------------

def plot_louvain_communities(G, community_map, plots_dir, prefix=""):
    """
    Grafo con nodos coloreados por comunidad Louvain.
    """
    if G.number_of_nodes() == 0 or not community_map:
        return

    pos = {}
    for n, d in G.nodes(data=True):
        try:
            x = int(d.get("wordnum", 0))
            y = -int(d.get("sentnum", 1))
        except (ValueError, TypeError):
            x, y = 0, 0
        pos[n] = (x, y)

    n_communities = max(community_map.values()) + 1 if community_map else 1
    cmap = plt.colormaps.get_cmap("tab20") if hasattr(plt, "colormaps") else plt.cm.get_cmap("tab20")
    cmap = cmap.resampled(max(1, n_communities))

    node_colors = [cmap(community_map.get(n, 0) % 20) for n in G.nodes()]
    node_sizes = [30 + 50 * min(1.0, d.get("fix_count", 0) / 20.0) for _, d in G.nodes(data=True)]

    with plt.rc_context(_PLOT_STYLE):
        fig, ax = plt.subplots(figsize=(14, 7))
        fig.suptitle(f"Comunidades Louvain — {prefix}", fontsize=12, y=1.02)

        nx.draw_networkx_nodes(
            G, pos, node_color=node_colors, node_size=node_sizes,
            alpha=0.85, ax=ax,
        )

        # Dibujar aristas ligeras
        edge_widths = [0.3 for _ in G.edges()]
        nx.draw_networkx_edges(
            G, pos, alpha=0.15, width=edge_widths, ax=ax,
        )

        # Etiquetas para nodos con fix_count alto
        labels = {}
        for n, d in G.nodes(data=True):
            if d.get("fix_count", 0) >= 5:
                labels[n] = d.get("word", n)
        if labels:
            nx.draw_networkx_labels(
                G, pos, labels=labels, font_size=7, font_weight="bold",
                ax=ax,
            )

        # Leyenda de comunidades
        from matplotlib.patches import Patch
        legend_handles = [
            Patch(facecolor=cmap(i % 20), edgecolor="black", label=f"Comunidad {i}")
            for i in range(min(n_communities, 15))
        ]
        if n_communities > 15:
            legend_handles.append(
                Patch(facecolor=cmap(15 % 20), edgecolor="black", label="...")
            )
        ax.legend(handles=legend_handles, loc="upper right", fontsize=8,
                  title="Louvain", title_fontsize=9)

        ax.set_xlabel("Posición de palabra (wordnum)")
        ax.set_ylabel("Oración (sentnum, invertido)")
        fig.tight_layout()
        _save_fig(fig, plots_dir, "louvain_communities")


# ---------------------------------------------------------------------------
# 4. K-core decomposition (3 paneles)
# ---------------------------------------------------------------------------

def plot_kcore_decomposition(G, kcore_df, plots_dir, prefix=""):
    """
    3 subplots: grafo coloreado por k-core in/out/total + distribución.
    """
    if G.number_of_nodes() == 0 or kcore_df.empty:
        return

    pos = {}
    for n, d in G.nodes(data=True):
        try:
            x = int(d.get("wordnum", 0))
            y = -int(d.get("sentnum", 1))
        except (ValueError, TypeError):
            x, y = 0, 0
        pos[n] = (x, y)

    with plt.rc_context(_PLOT_STYLE):
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle(f"K-Core Decomposition — {prefix}", fontsize=12, y=1.02)

        for ax, col, title in [
            (axes[0], "kcore_in", "K-Core (In-Degree)"),
            (axes[1], "kcore_out", "K-Core (Out-Degree)"),
            (axes[2], "kcore_total", "K-Core (Total)"),
        ]:
            kcore_map = dict(zip(kcore_df["node_id"], kcore_df[col]))
            values = [kcore_map.get(n, 0) for n in G.nodes()]
            max_val = max(values) if values else 1

            nodes_coll = nx.draw_networkx_nodes(
                G, pos, node_color=values, node_size=30,
                cmap=plt.cm.YlOrRd, vmin=0, vmax=max_val,
                alpha=0.85, ax=ax,
            )
            nx.draw_networkx_edges(G, pos, alpha=0.1, width=0.2, ax=ax)

            cb = plt.colorbar(nodes_coll, ax=ax, fraction=0.046, pad=0.04)
            cb.set_label(f"k-core ({col.replace('kcore_', '')})")
            ax.set_title(title, fontsize=10)
            ax.set_xlabel("wordnum")
            ax.set_ylabel("sentnum")

        fig.tight_layout()
        _save_fig(fig, plots_dir, "kcore_decomposition")


# ---------------------------------------------------------------------------
# 5. Centralidad ranking (barras horizontales top-10)
# ---------------------------------------------------------------------------

def plot_centrality_rankings(centrality_dict, plots_dir, prefix="", top_n=10):
    """
    Barras horizontales con top-10 nodos por cada centralidad.
    """
    if not centrality_dict:
        return

    centralities_to_plot = [
        ("degree", "Degree"),
        ("betweenness", "Betweenness"),
        ("closeness", "Closeness"),
        ("eigenvector", "Eigenvector"),
        ("pagerank", "PageRank"),
    ]

    available = [(k, v) for k, v in centralities_to_plot if k in centrality_dict]
    if not available:
        return

    n_plots = len(available)
    with plt.rc_context(_PLOT_STYLE):
        fig, axes = plt.subplots(n_plots, 1, figsize=(10, 3 * n_plots))
        if n_plots == 1:
            axes = [axes]
        fig.suptitle(f"Ranking de Centralidades (Top {top_n}) — {prefix}",
                     fontsize=12, y=1.01)

        colors = ["#2980b9", "#c0392b", "#27ae60", "#8e44ad", "#f39c12"]

        for i, (cname, label) in enumerate(available):
            cdict = centrality_dict[cname]
            sorted_nodes = sorted(cdict.items(), key=lambda x: -x[1])[:top_n]
            nodes = [n.split(":", 1)[1] if ":" in n else n for n, _ in sorted_nodes]
            values = [v for _, v in sorted_nodes]

            ax = axes[i]
            y_pos = range(len(nodes))
            ax.barh(y_pos, values, color=colors[i % len(colors)], alpha=0.8,
                    edgecolor="white", linewidth=0.5)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(nodes, fontsize=8)
            ax.set_xlabel(label)
            ax.set_title(label, fontsize=10, loc="left", fontweight="bold")
            ax.invert_yaxis()

        fig.tight_layout()
        _save_fig(fig, plots_dir, "centrality_ranking")


# ---------------------------------------------------------------------------
# 6. Correlación de centralidades (heatmap)
# ---------------------------------------------------------------------------

def plot_centrality_correlation(corr_matrix, plots_dir, prefix=""):
    """
    Heatmap de correlación Spearman entre centralidades.
    """
    if corr_matrix.empty:
        return

    with plt.rc_context(_PLOT_STYLE):
        fig, ax = plt.subplots(figsize=(8, 7))
        fig.suptitle(f"Correlación de Centralidades (Spearman) — {prefix}",
                     fontsize=12, y=1.02)

        mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
        sns.heatmap(
            corr_matrix, annot=True, fmt=".3f", cmap="RdBu_r",
            center=0, vmin=-1, vmax=1,
            mask=mask,
            square=True, linewidths=0.5,
            cbar_kws={"label": "Correlación Spearman"},
            ax=ax,
        )
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right", fontsize=9)
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=9)

        fig.tight_layout()
        _save_fig(fig, plots_dir, "centrality_correlation")


# ---------------------------------------------------------------------------
# 7. Distribución de centralidades (histogramas)
# ---------------------------------------------------------------------------

def plot_centrality_distributions(centrality_dict, plots_dir, prefix=""):
    """
    Histogramas de cada centralidad en layout 2x3.
    """
    if not centrality_dict:
        return

    centralities_to_plot = [
        ("degree", "Degree"),
        ("in_degree", "In-Degree"),
        ("out_degree", "Out-Degree"),
        ("betweenness", "Betweenness"),
        ("closeness", "Closeness"),
        ("pagerank", "PageRank"),
    ]

    available = [(k, v) for k, v in centralities_to_plot if k in centrality_dict]
    if not available:
        return

    n_cols = 3
    n_rows = (len(available) + n_cols - 1) // n_cols
    colors = ["#2980b9", "#3498db", "#1abc9c", "#c0392b", "#27ae60", "#f39c12"]

    with plt.rc_context(_PLOT_STYLE):
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(12, 4 * n_rows))
        if n_rows == 1:
            axes = axes.reshape(1, -1)
        fig.suptitle(f"Distribución de Centralidades — {prefix}", fontsize=12, y=1.02)

        for i, (cname, label) in enumerate(available):
            r, c = divmod(i, n_cols)
            ax = axes[r, c]
            values = list(centrality_dict[cname].values())
            ax.hist(values, bins=min(30, max(5, len(values) // 3)),
                    color=colors[i % len(colors)], alpha=0.7,
                    edgecolor="white", linewidth=0.5)
            ax.set_title(label, fontsize=10, fontweight="bold")
            ax.set_xlabel(label)
            ax.set_ylabel("Frecuencia")

        # Ocultar ejes vacíos
        for i in range(len(available), n_rows * n_cols):
            r, c = divmod(i, n_cols)
            axes[r, c].set_visible(False)

        fig.tight_layout()
        _save_fig(fig, plots_dir, "centrality_distributions")
