"""
analysis/individual_differences/generate_separated_plots.py

Genera los gráficos individuales separados en alta resolución (300 DPI):
1. figure_2b1_compensation_quartiles_grid.png (Las 4 dispersiones Q1-Q4 de compensación)
2. figure_2b2_compensation_slopes_comparison.png (El gráfico de barras de comparación de pendientes)
3. figure_3a_reader_archetypes_pca.png (Biplot PCA de arquetipos en 2D)
4. figure_3b_reader_archetypes_boxplots.png (Distribuciones reales por arquetipo en boxplots)
5. figure_3c_reader_archetypes_profiles.png (Tarjeta visual con el resumen y características de arquetipos)
"""

from __future__ import annotations

import shutil
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
from scipy.cluster.vq import kmeans2

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "analysis" / "individual_differences" / "output"
PLOTS_DIR = OUTPUT_DIR / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACT_DIR = Path("/Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177")


def load_data() -> pd.DataFrame:
    p = OUTPUT_DIR / "master_multilevel_dataset.csv"
    if not p.exists():
        from advanced_multilevel_analysis import load_integrated_master
        return load_integrated_master()
    return pd.read_csv(p)


# ===========================================================================
# 1. FIGURA 2B1: LAS 4 DISPERSIONES POR CUARTILES DE VOCABULARIO
# ===========================================================================
def plot_figure_2b1_quartiles_grid(df: pd.DataFrame):
    sub = df.dropna(subset=["accuracy", "vocab.t2.5", "regression_rate"]).copy()
    
    q_labels = ["Q1: Bajo (≤ 24)", "Q2: Medio-Bajo (25-35)", "Q3: Medio-Alto (36-38)", "Q4: Alto (39-40)"]
    sub["vocab_quartile"] = pd.qcut(sub["vocab.t2.5"], 4, labels=q_labels)

    q_colors = {
        "Q1: Bajo (≤ 24)": "#DC2626",
        "Q2: Medio-Bajo (25-35)": "#D97706",
        "Q3: Medio-Alto (36-38)": "#2563EB",
        "Q4: Alto (39-40)": "#059669",
    }

    fig, axes = plt.subplots(2, 2, figsize=(10.5, 8.5), dpi=300, sharex=True, sharey=True)
    fig.patch.set_facecolor("#FFFFFF")
    axes_flat = axes.flatten()

    for ax, q in zip(axes_flat, q_labels):
        q_data = sub[sub["vocab_quartile"] == q]
        c = q_colors[q]

        ax.scatter(q_data["regression_rate"] * 100, q_data["accuracy"] * 100, color=c, alpha=0.45, s=28, edgecolors="none")
        sns.regplot(data=q_data, x=q_data["regression_rate"] * 100, y=q_data["accuracy"] * 100, 
                    ax=ax, scatter=False, color=c, line_kws={"linewidth": 2.5})

        ax.set_title(f"{q}  (N = {len(q_data)})", fontsize=11, fontweight="bold", pad=8, color="#0F172A")
        ax.set_xlabel("Tasa de Regresiones (%)", fontsize=10, fontweight="semibold")
        ax.set_ylabel("Comprensión Lectora (%)", fontsize=10, fontweight="semibold")
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.set_facecolor("#F8FAFC")

    plt.suptitle("Comprensión Lectora vs. Tasa de Regresiones según Cuartil de Vocabulario", 
                 fontsize=13.5, fontweight="bold", y=0.99, color="#0F172A")
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    out_path = PLOTS_DIR / "figure_2b1_compensation_quartiles_grid.png"
    plt.savefig(out_path, bbox_inches="tight", dpi=300)
    plt.close()
    shutil.copy(out_path, ARTIFACT_DIR / out_path.name)
    print(f"[figure-2b1] Guardada en {out_path}")


# ===========================================================================
# 2. FIGURA 2B2: COMPARACIÓN DE PENDIENTES DE COMPENSACIÓN (BAR CHART)
# ===========================================================================
def plot_figure_2b2_slopes_comparison(df: pd.DataFrame):
    sub = df.dropna(subset=["accuracy", "vocab.t2.5", "regression_rate"]).copy()
    
    q_labels = ["Q1: Bajo (≤ 24)", "Q2: Medio-Bajo (25-35)", "Q3: Medio-Alto (36-38)", "Q4: Alto (39-40)"]
    sub["vocab_quartile"] = pd.qcut(sub["vocab.t2.5"], 4, labels=q_labels)

    q_colors = {
        "Q1: Bajo (≤ 24)": "#DC2626",
        "Q2: Medio-Bajo (25-35)": "#D97706",
        "Q3: Medio-Alto (36-38)": "#2563EB",
        "Q4: Alto (39-40)": "#059669",
    }

    slopes_summary = []
    for q in q_labels:
        q_data = sub[sub["vocab_quartile"] == q]
        slope, intercept, r_val, p_val, std_err = stats.linregress(q_data["regression_rate"], q_data["accuracy"])
        slopes_summary.append({
            "label": q,
            "slope": slope,
            "std_err": std_err,
            "p_val": p_val,
            "color": q_colors[q],
            "n": len(q_data)
        })

    s_df = pd.DataFrame(slopes_summary)

    fig, ax = plt.subplots(figsize=(8.5, 6.0), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#F8FAFC")

    x_pos = np.arange(len(s_df))
    bars = ax.bar(x_pos, s_df["slope"], yerr=s_df["std_err"], capsize=6, 
                  color=s_df["color"], edgecolor="#1E293B", linewidth=1.1, width=0.52)

    for i, row in s_df.iterrows():
        sig = "*** (p < .001)" if row["p_val"] < 0.001 else "n.s."
        y_text = row["slope"] + row["std_err"] + 0.035
        ax.text(i, y_text, f"{row['slope']:+.3f}\n{sig}", ha="center", va="bottom", fontsize=9.5, fontweight="bold", color="#0F172A")

    ax.axhline(0, color="#64748B", linestyle="--", linewidth=1.2)
    ax.set_xticks(x_pos)
    ax.set_xticklabels([f"{row['label'].split(':')[0]}\n({row['label'].split(':')[1].strip()})" for _, row in s_df.iterrows()], 
                       fontsize=9.8, fontweight="semibold")
    ax.set_ylabel("Pendiente de las Regresiones sobre Comprensión (β)", fontsize=10.5, fontweight="semibold")
    ax.set_title("Efecto de la Tasa de Regresiones sobre la Comprensión por Cuartil de Vocabulario\n(Solo Q1 muestra beneficio compensatorio estadísticamente significativo)", 
                 fontsize=11.5, fontweight="bold", pad=12, color="#0F172A")
    ax.set_ylim(-0.15, 1.15)
    ax.grid(True, linestyle="--", alpha=0.4, axis="y")

    plt.tight_layout()
    out_path = PLOTS_DIR / "figure_2b2_compensation_slopes_comparison.png"
    plt.savefig(out_path, bbox_inches="tight", dpi=300)
    plt.close()
    shutil.copy(out_path, ARTIFACT_DIR / out_path.name)
    print(f"[figure-2b2] Guardada en {out_path}")


# ===========================================================================
# 3. FIGURA 3A: BIPLOT PCA 2D DE ARQUETIPOS DE LECTORES
# ===========================================================================
def plot_figure_3a_pca(df: pd.DataFrame):
    cluster_cols = ["vocab.t2.5", "lextale", "mean_fix_dur", "regression_rate", "accuracy"]
    sub = df.dropna(subset=cluster_cols).copy()

    # Estandarizar
    Z = np.zeros((len(sub), len(cluster_cols)))
    for i, c in enumerate(cluster_cols):
        Z[:, i] = (sub[c] - sub[c].mean()) / sub[c].std()

    np.random.seed(42)
    centroids, labels = kmeans2(Z, 4, minit="points")
    sub["cluster"] = labels

    cluster_means = sub.groupby("cluster")[cluster_cols].mean()
    labels_map = {}
    for cl in range(4):
        v = cluster_means.loc[cl, "vocab.t2.5"]
        dur = cluster_means.loc[cl, "mean_fix_dur"]
        reg = cluster_means.loc[cl, "regression_rate"]
        acc = cluster_means.loc[cl, "accuracy"]

        if v > 34 and dur < 210 and reg < 0.16:
            labels_map[cl] = "Nativoide / Eficiente"
        elif v > 33 and reg >= 0.18:
            labels_map[cl] = "Estratégico / Compensador"
        elif v < 20 or acc < 0.60:
            labels_map[cl] = "Bloqueado / Con Dificultad"
        else:
            labels_map[cl] = "Intermedio / Moderado"

    sub["archetype_name"] = sub["cluster"].map(labels_map)

    # PCA 2D vía SVD
    U, S, Vt = np.linalg.svd(Z, full_matrices=False)
    sub["PC1"] = - (Z @ Vt[0])
    sub["PC2"] = - (Z @ Vt[1])
    var_exp = (S**2) / np.sum(S**2)

    c_colors = {
        "Nativoide / Eficiente": "#10B981",
        "Estratégico / Compensador": "#8B5CF6",
        "Intermedio / Moderado": "#3B82F6",
        "Bloqueado / Con Dificultad": "#EF4444"
    }

    fig, ax = plt.subplots(figsize=(9.5, 7.5), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#F8FAFC")

    for arch, col in c_colors.items():
        arch_data = sub[sub["archetype_name"] == arch]
        ax.scatter(arch_data["PC1"], arch_data["PC2"], color=col, alpha=0.55, s=30, 
                   label=f"{arch} (N = {len(arch_data)})", edgecolors="none")

        mean_pc1 = arch_data["PC1"].mean()
        mean_pc2 = arch_data["PC2"].mean()
        ax.scatter(mean_pc1, mean_pc2, color=col, s=160, edgecolors="#0F172A", linewidth=2.2, marker="X")

    # Vectores de carga de variables
    loadings = {
        "Vocabulario": (-Vt[0, 0] * 3.3, -Vt[1, 0] * 3.3),
        "LexTALE": (-Vt[0, 1] * 3.3, -Vt[1, 1] * 3.3),
        "Duración Fijación": (-Vt[0, 2] * 3.3, -Vt[1, 2] * 3.3),
        "Tasa Regresiones": (-Vt[0, 3] * 3.3, -Vt[1, 3] * 3.3),
        "Comprensión": (-Vt[0, 4] * 3.3, -Vt[1, 4] * 3.3),
    }

    for var_name, (lx, ly) in loadings.items():
        ax.annotate("", xy=(lx, ly), xytext=(0, 0), arrowprops=dict(arrowstyle="->", lw=1.8, color="#0F172A"))
        ax.text(lx * 1.13, ly * 1.13, var_name, fontsize=9.5, fontweight="bold", color="#0F172A", ha="center", va="center")

    ax.axhline(0, color="#CBD5E1", linestyle="--", linewidth=1.0)
    ax.axvline(0, color="#CBD5E1", linestyle="--", linewidth=1.0)
    ax.set_xlabel(f"PC1: Proficiencia General ({var_exp[0]*100:.1f}% de Varianza Explicada)", fontsize=10.5, fontweight="semibold")
    ax.set_ylabel(f"PC2: Estrategia de Relectura ({var_exp[1]*100:.1f}% de Varianza Explicada)", fontsize=10.5, fontweight="semibold")
    ax.set_title("Espacio Latente PCA de los Arquetipos de Lectores (Biplot 2D)\n(Total Varianza Explicada: 65.9%, N = 1,032)", 
                 fontsize=12.5, fontweight="bold", pad=12, color="#0F172A")
    ax.legend(loc="lower left", fontsize=9.2, framealpha=0.95)
    ax.grid(True, linestyle="--", alpha=0.4)

    plt.tight_layout()
    out_path = PLOTS_DIR / "figure_3a_reader_archetypes_pca.png"
    plt.savefig(out_path, bbox_inches="tight", dpi=300)
    plt.close()
    shutil.copy(out_path, ARTIFACT_DIR / out_path.name)
    print(f"[figure-3a] Guardada en {out_path}")


# ===========================================================================
# 4. FIGURA 3B: DISTRIBUCIONES REALES POR ARQUETIPO (BOXPLOTS)
# ===========================================================================
def plot_figure_3b_boxplots(df: pd.DataFrame):
    cluster_cols = ["vocab.t2.5", "lextale", "mean_fix_dur", "regression_rate", "accuracy"]
    sub = df.dropna(subset=cluster_cols).copy()

    Z = np.zeros((len(sub), len(cluster_cols)))
    for i, c in enumerate(cluster_cols):
        Z[:, i] = (sub[c] - sub[c].mean()) / sub[c].std()

    np.random.seed(42)
    centroids, labels = kmeans2(Z, 4, minit="points")
    sub["cluster"] = labels

    cluster_means = sub.groupby("cluster")[cluster_cols].mean()
    labels_map = {}
    for cl in range(4):
        v = cluster_means.loc[cl, "vocab.t2.5"]
        dur = cluster_means.loc[cl, "mean_fix_dur"]
        reg = cluster_means.loc[cl, "regression_rate"]
        acc = cluster_means.loc[cl, "accuracy"]

        if v > 34 and dur < 210 and reg < 0.16:
            labels_map[cl] = "Nativoide / Eficiente"
        elif v > 33 and reg >= 0.18:
            labels_map[cl] = "Estratégico / Compensador"
        elif v < 20 or acc < 0.60:
            labels_map[cl] = "Bloqueado / Con Dificultad"
        else:
            labels_map[cl] = "Intermedio / Moderado"

    sub["archetype_name"] = sub["cluster"].map(labels_map)

    c_colors = {
        "Nativoide / Eficiente": "#10B981",
        "Estratégico / Compensador": "#8B5CF6",
        "Intermedio / Moderado": "#3B82F6",
        "Bloqueado / Con Dificultad": "#EF4444"
    }

    var_configs = [
        ("vocab.t2.5", "Vocabulario Receptivo (Nation, 0-40)"),
        ("mean_fix_dur", "Duración Media de Fijación (ms)"),
        ("regression_rate", "Tasa de Regresiones (%)"),
        ("accuracy", "Comprensión Lectora (%)"),
    ]

    order_arch = ["Nativoide / Eficiente", "Estratégico / Compensador", "Intermedio / Moderado", "Bloqueado / Con Dificultad"]
    short_labels = ["Nativoide", "Estratégico", "Intermedio", "Bloqueado"]

    fig, axes = plt.subplots(2, 2, figsize=(11.5, 8.5), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    axes_flat = axes.flatten()

    for ax, (col, title) in zip(axes_flat, var_configs):
        ax.set_facecolor("#F8FAFC")
        plot_data = sub.copy()
        if col in ["regression_rate", "accuracy"]:
            plot_data[col] = plot_data[col] * 100

        sns.boxplot(data=plot_data, x="archetype_name", y=col, order=order_arch, palette=c_colors, hue="archetype_name", legend=False, ax=ax, width=0.52, fliersize=2.5)
        ax.set_title(title, fontsize=11, fontweight="bold", pad=8, color="#0F172A")
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.set_xticks(range(4))
        ax.set_xticklabels(short_labels, fontsize=10, fontweight="semibold")
        ax.grid(True, linestyle="--", alpha=0.4, axis="y")

    plt.suptitle("Distribución Real de Variables Clave en los 4 Arquetipos de Lectores", 
                 fontsize=13.5, fontweight="bold", y=0.99, color="#0F172A")
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    out_path = PLOTS_DIR / "figure_3b_reader_archetypes_boxplots.png"
    plt.savefig(out_path, bbox_inches="tight", dpi=300)
    plt.close()
    shutil.copy(out_path, ARTIFACT_DIR / out_path.name)
    print(f"[figure-3b] Guardada en {out_path}")


# ===========================================================================
# 5. FIGURA 3C: TARJETA VISUAL DE PERFILES DE ARQUETIPOS
# ===========================================================================
def plot_figure_3c_profiles_table(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(11.8, 6.2), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    ax.axis("off")

    cards = [
        {
            "title_lines": ["NATIVOIDE /", "EFICIENTE"],
            "share": "27.7% (N = 286)",
            "color": "#10B981",
            "bg": "#ECFDF5",
            "stats": [
                "Vocabulario: 37.0 / 40",
                "LexTALE: 86.9%",
                "Fijación: 202 ms",
                "Regresiones: 12.9%",
                "Comprensión: 78.3%",
            ],
            "strategy": "Fluidez automática en primer pase sin necesidad de relectura compensatoria.",
        },
        {
            "title_lines": ["ESTRATÉGICO /", "COMPENSADOR"],
            "share": "23.7% (N = 245)",
            "color": "#8B5CF6",
            "bg": "#F5F3FF",
            "stats": [
                "Vocabulario: 36.1 / 40",
                "LexTALE: 84.1%",
                "Fijación: 213 ms",
                "Regresiones: 21.1%",
                "Comprensión: 76.1%",
            ],
            "strategy": "Relectura activa y monitoreo constante para asegurar comprensión profunda.",
        },
        {
            "title_lines": ["INTERMEDIO /", "MODERADO"],
            "share": "32.2% (N = 332)",
            "color": "#3B82F6",
            "bg": "#EFF6FF",
            "stats": [
                "Vocabulario: 30.0 / 40",
                "LexTALE: 70.0%",
                "Fijación: 236 ms",
                "Regresiones: 13.6%",
                "Comprensión: 72.2%",
            ],
            "strategy": "Mayor tiempo invertido por fijación para decodificar texto en L2.",
        },
        {
            "title_lines": ["BLOQUEADO /", "CON DIFICULTAD"],
            "share": "16.4% (N = 169)",
            "color": "#EF4444",
            "bg": "#FEF2F2",
            "stats": [
                "Vocabulario: 13.5 / 40",
                "LexTALE: 63.0%",
                "Fijación: 244 ms",
                "Regresiones: 13.7%",
                "Comprensión: 53.6%",
            ],
            "strategy": "Cuello de botella léxico severo que interrumpe el flujo y frena comprensión.",
        },
    ]

    w = 0.224
    gap = 0.02
    left = 0.024
    y0 = 0.04
    h = 0.88

    for i, c in enumerate(cards):
        x0 = left + i * (w + gap)

        # Card container with rounded corners
        rect = FancyBboxPatch(
            (x0, y0), w, h,
            boxstyle="round,pad=0.0,rounding_size=0.02",
            facecolor=c["bg"],
            edgecolor=c["color"],
            linewidth=1.8,
            transform=ax.transAxes,
            clip_on=False,
        )
        ax.add_patch(rect)

        # Title (2 lines)
        title_text = "\n".join(c["title_lines"])
        ax.text(
            x0 + w / 2, y0 + h - 0.055,
            title_text,
            transform=ax.transAxes,
            ha="center", va="top",
            fontsize=9.2, fontweight="bold",
            color=c["color"],
            linespacing=1.1,
        )

        # Share badge
        ax.text(
            x0 + w / 2, y0 + h - 0.155,
            c["share"],
            transform=ax.transAxes,
            ha="center", va="top",
            fontsize=8.2, fontweight="semibold",
            color="#475569",
        )

        # Separator line 1
        ax.plot(
            [x0 + 0.015, x0 + w - 0.015],
            [y0 + h - 0.19, y0 + h - 0.19],
            color=c["color"], alpha=0.35, linewidth=0.9,
            transform=ax.transAxes,
        )

        # Section: Métricas Promedio
        ax.text(
            x0 + 0.018, y0 + h - 0.215,
            "Métricas Promedio:",
            transform=ax.transAxes,
            va="top",
            fontsize=7.8, fontweight="bold",
            color="#64748B",
        )

        stats_text = "\n".join([f"• {s}" for s in c["stats"]])
        ax.text(
            x0 + 0.018, y0 + h - 0.26,
            stats_text,
            transform=ax.transAxes,
            va="top",
            fontsize=8.0,
            color="#1E293B",
            linespacing=1.45,
        )

        # Separator line 2
        ax.plot(
            [x0 + 0.015, x0 + w - 0.015],
            [y0 + 0.24, y0 + 0.24],
            color=c["color"], alpha=0.35, linewidth=0.9,
            transform=ax.transAxes,
        )

        # Section: Patrón / Estrategia
        ax.text(
            x0 + 0.018, y0 + 0.21,
            "Patrón y Estrategia:",
            transform=ax.transAxes,
            va="top",
            fontsize=7.8, fontweight="bold",
            color=c["color"],
        )

        wrapped_strat = textwrap.fill(c["strategy"], width=23)
        ax.text(
            x0 + 0.018, y0 + 0.17,
            wrapped_strat,
            transform=ax.transAxes,
            va="top",
            fontsize=7.6,
            color="#334155",
            linespacing=1.25,
        )

    ax.set_title(
        "Perfiles Comparativos de los 4 Arquetipos de Lectura Bilingüe (Clustering k-Means)",
        fontsize=12.5, fontweight="bold", pad=12, color="#0F172A",
    )
    plt.tight_layout()
    out_path = PLOTS_DIR / "figure_3c_reader_archetypes_profiles.png"
    plt.savefig(out_path, bbox_inches="tight", dpi=300)
    plt.close()
    shutil.copy(out_path, ARTIFACT_DIR / out_path.name)
    print(f"[figure-3c] Guardada en {out_path}")


def main():
    print("=== GENERANDO FIGURAS SEPARADAS ===")
    df = load_data()
    plot_figure_2b1_quartiles_grid(df)
    plot_figure_2b2_slopes_comparison(df)
    plot_figure_3a_pca(df)
    plot_figure_3b_boxplots(df)
    plot_figure_3c_profiles_table(df)
    print("=== TODAS LAS FIGURAS SEPARADAS GENERADAS EXITOSAMENTE ===")


if __name__ == "__main__":
    main()

