"""
viz.py

Plots de cascadas y comunidades para la red de carga cognitiva.
"""

import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def visualize_cogload_cascades(cascades, build_dir, name_suffix=""):
    """
    Genera el plot de cascadas: histograma/densidad de p-valores y
    barras separadas para cascadas confirmadas vs. rechazadas.
    """
    if not cascades:
        print("[!] No hay cascadas para visualizar.")
        return
    plots_dir = os.path.join(build_dir, "plots")
    os.makedirs(plots_dir, exist_ok=True)
    suffix = f"_{name_suffix}" if name_suffix else ""

    df = pd.DataFrame(cascades)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    sns.histplot(
        data=df,
        x="p_value",
        hue="is_cascade",
        multiple="stack",
        bins=30,
        ax=axes[0],
        palette={True: "#27ae60", False: "#c0392b"},
    )
    axes[0].axvline(0.05, color="black", linestyle="--", linewidth=1)
    axes[0].set_title("Distribución de p-valores por pico")
    axes[0].set_xlabel("p_value")
    axes[0].set_ylabel("Conteo")

    cascade_only = df[df["is_cascade"]]
    axes[1].bar(
        range(len(cascade_only)),
        cascade_only["peak_ps"] - cascade_only["baseline_mean_signal"],
        color="#27ae60",
    )
    axes[1].set_title("Magnitud de cascadas confirmadas (peak − baseline)")
    axes[1].set_xlabel("Cascada #")
    axes[1].set_ylabel("Δseñal")

    fig.tight_layout()
    plot_path = os.path.join(plots_dir, f"cascade_plot{suffix}.png")
    fig.savefig(plot_path, dpi=200)
    plt.close(fig)
    print(f"[OK] Plot de cascadas guardado en: {plot_path}")


def visualize_community_along_text(G, build_dir, name_suffix=""):
    """
    Genera plots/community_along_text.png: por cada nodo muestra su
    community_label a lo largo de wordnum, con colores por community_id.
    Permite ver si las comunidades high_stress / neutral / low_stress se
    alinean con la estructura de oraciones o se distribuyen a lo largo del
    texto.
    """
    if G.number_of_nodes() == 0:
        return
    plots_dir = os.path.join(build_dir, "plots")
    os.makedirs(plots_dir, exist_ok=True)
    suffix = f"_{name_suffix}" if name_suffix else ""

    rows = []
    for n, d in G.nodes(data=True):
        if "community_id" not in d:
            continue
        rows.append(
            {
                "wordnum": d.get("wordnum", 0),
                "sentnum": d.get("sentnum", 1),
                "community_id": d.get("community_id", -1),
                "community_label": d.get("community_label", "neutral"),
                "mean_ps_z": d.get("mean_ps_z", 0.0),
                "mean_ps": d.get("mean_ps", 0.0),
            }
        )
    if not rows:
        print("[!] Sin etiquetas de comunidad; saltando community_along_text.png")
        return
    df = pd.DataFrame(rows).sort_values("wordnum")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7), sharex=True)

    label_color = {
        "high_stress": "#c0392b",
        "neutral": "#7f8c8d",
        "low_stress": "#2980b9",
    }
    colors = [label_color.get(l, "#7f8c8d") for l in df["community_label"]]
    ax1.scatter(
        df["wordnum"],
        df["mean_ps_z"],
        c=colors,
        s=30,
        alpha=0.7,
        edgecolors="black",
        linewidth=0.3,
    )
    ax1.axhline(0, color="black", linewidth=0.5, linestyle="-")
    ax1.set_ylabel("mean_ps_z")
    ax1.set_title("Comunidades y carga cognitiva a lo largo del texto", fontsize=12)
    ax1.grid(True, linestyle=":", alpha=0.3)

    sent_breaks = df["sentnum"].diff().fillna(0).ne(0)
    sb_indices = sent_breaks[sent_breaks].index.tolist()
    for sb_idx in sb_indices:
        sb_wordnum = df.loc[sb_idx, "wordnum"]
        for ax in (ax1, ax2):
            ax.axvline(
                sb_wordnum - 0.5, color="#7f8c8d", linestyle="--", alpha=0.5
            )

    cmap = plt.colormaps.get_cmap("tab20") if hasattr(plt, "colormaps") else plt.cm.get_cmap("tab20")
    cmap = cmap.resampled(max(1, int(df["community_id"].max()) + 1))
    comm_colors = [cmap(int(c) % 20) for c in df["community_id"]]
    ax2.scatter(
        df["wordnum"],
        df["community_id"],
        c=comm_colors,
        s=30,
        alpha=0.85,
        edgecolors="black",
        linewidth=0.3,
    )
    ax2.set_xlabel("Posición de palabra (wordnum)")
    ax2.set_ylabel("community_id")
    ax2.grid(True, linestyle=":", alpha=0.3)

    from matplotlib.patches import Patch
    legend_handles = [
        Patch(facecolor=color, edgecolor="black", label=label)
        for label, color in label_color.items()
    ]
    ax1.legend(handles=legend_handles, loc="upper right", fontsize=9)

    fig.tight_layout()
    plot_path = os.path.join(plots_dir, f"community_along_text{suffix}.png")
    fig.savefig(plot_path, dpi=200)
    plt.close(fig)
    print(f"[OK] Plot de comunidades a lo largo del texto guardado en: {plot_path}")
