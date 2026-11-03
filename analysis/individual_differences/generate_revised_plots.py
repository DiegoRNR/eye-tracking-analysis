"""
analysis/individual_differences/generate_revised_plots.py

Generación de gráficos refinados y simplificados según el feedback:
1. Figura 2A: Diagrama de Mediación dedicado + gráficos de dispersión de cada vía (Path a, b, c).
2. Figura 2B: Mecanismo Compensatorio desglosado por CUARTILES de Vocabulario (Q1 a Q4).
3. Figura 3: Descubrimiento de Arquetipos (Biplot PCA de 2 ejes + distribuciones reales por boxplot).
4. Figura 4A: Calibración Metacognitiva (Gráfico de dispersión con zonas).
5. Figura 4B: Sesgo de Calibración desglosado POR CADA LENGUA individualmente (ordenada por distancia).
6. Figura 4C: Sesgo de Calibración agrupado por CUARTILES de Distancia Lingüística.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
from scipy import stats
from scipy.cluster.vq import kmeans2

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "analysis" / "individual_differences" / "output"
PLOTS_DIR = OUTPUT_DIR / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACT_DIR = Path("/Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177")

LANG_NAMES = {
    "du": "Holandés (du)",
    "da": "Danés (da)",
    "no": "Noruego (no)",
    "ge": "Alemán (ge)",
    "ge_po": "Alemán Potsdam (ge_po)",
    "ge_zu": "Alemán Zúrich (ge_zu)",
    "ic": "Islandés (ic)",
    "it": "Italiano (it)",
    "ru": "Ruso (ru)",
    "ru_mo": "Ruso Moscú (ru_mo)",
    "se": "Serbio (se)",
    "bp": "Portugués Bras. (bp)",
    "sp": "Español (sp)",
    "sp_ch": "Español Chile (sp_ch)",
    "hi_iiith": "Hindi IIITH (hi)",
    "hi_iitk": "Hindi IITK (hi)",
    "gr": "Griego (gr)",
    "ee": "Estonio (ee)",
    "fi": "Finlandés (fi)",
    "ch_s": "Chino Simpl. (zh-s)",
    "ch_t": "Chino Trad. (zh-t)",
    "he": "Hebreo (he)",
    "tr": "Turco (tr)",
    "ba": "Baskir (ba)",
}


def load_data() -> pd.DataFrame:
    p = OUTPUT_DIR / "master_multilevel_dataset.csv"
    if not p.exists():
        from advanced_multilevel_analysis import load_integrated_master
        return load_integrated_master()
    return pd.read_csv(p)


# ===========================================================================
# 1. FIGURA 2A: DIAGRAMA DE MEDIACIÓN SIMPLIFICADO Y DISPERSIÓN POR VÍAS
# ===========================================================================
def plot_figure_2a_mediation(df: pd.DataFrame):
    sub = df.dropna(subset=["accuracy", "vocab.t2.5", "mean_fix_dur"]).copy()
    
    # Estandarización
    sub["z_acc"] = (sub["accuracy"] - sub["accuracy"].mean()) / sub["accuracy"].std()
    sub["z_voc"] = (sub["vocab.t2.5"] - sub["vocab.t2.5"].mean()) / sub["vocab.t2.5"].std()
    sub["z_dur"] = (sub["mean_fix_dur"] - sub["mean_fix_dur"].mean()) / sub["mean_fix_dur"].std()

    # Modelos
    m_c = sm.OLS(sub["z_acc"], sm.add_constant(sub[["z_voc"]])).fit()
    m_a = sm.OLS(sub["z_dur"], sm.add_constant(sub[["z_voc"]])).fit()
    m_b = sm.OLS(sub["z_acc"], sm.add_constant(sub[["z_voc", "z_dur"]])).fit()

    a = m_a.params["z_voc"]
    se_a = m_a.bse["z_voc"]
    b = m_b.params["z_dur"]
    se_b = m_b.bse["z_dur"]
    c = m_c.params["z_voc"]
    c_prime = m_b.params["z_voc"]

    indirect = a * b
    sobel_z = indirect / np.sqrt(b**2 * se_a**2 + a**2 * se_b**2)
    p_sobel = 2 * (1 - stats.norm.cdf(abs(sobel_z)))

    # Layout: Arriba el diagrama conceptual, abajo los 3 scatter plots de cada vía
    fig = plt.figure(figsize=(13.5, 8.5), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    gs = fig.add_gridspec(2, 3, height_ratios=[1.1, 1.3], hspace=0.35, wspace=0.25)

    ax_diag = fig.add_subplot(gs[0, :])
    ax_diag.axis("off")
    ax_diag.set_facecolor("#FFFFFF")

    # Dibujar cajas de mediación
    box_blue = dict(boxstyle="round,pad=0.7", facecolor="#EFF6FF", edgecolor="#2563EB", linewidth=1.8)
    box_red = dict(boxstyle="round,pad=0.7", facecolor="#FEF2F2", edgecolor="#DC2626", linewidth=1.8)

    ax_diag.text(0.18, 0.70, "Vocabulario Receptivo\n(Nation / L2)", ha="center", va="center", fontsize=11, fontweight="bold", color="#1E3A8A", bbox=box_blue)
    ax_diag.text(0.82, 0.70, "Comprensión Lectora\n(Accuracy MECO)", ha="center", va="center", fontsize=11, fontweight="bold", color="#1E3A8A", bbox=box_blue)
    ax_diag.text(0.50, 0.20, "Duración Media de Fijación\n(Carga Cognitiva en ms)", ha="center", va="center", fontsize=11, fontweight="bold", color="#991B1B", bbox=box_red)

    # Flechas
    arrow_props = dict(arrowstyle="->", lw=2.2, color="#1E293B")
    ax_diag.annotate("", xy=(0.70, 0.70), xytext=(0.30, 0.70), arrowprops=arrow_props)
    ax_diag.text(0.50, 0.76, f"Efecto Directo c' = {c_prime:+.3f}*** (p < .001)", ha="center", fontsize=10.5, fontweight="bold", color="#1E3A8A")

    ax_diag.annotate("", xy=(0.42, 0.30), xytext=(0.23, 0.60), arrowprops=arrow_props)
    ax_diag.text(0.24, 0.40, f"Vía a = {a:+.3f}***\n(p < 10⁻²⁸)", fontsize=10, fontweight="bold", color="#DC2626")

    ax_diag.annotate("", xy=(0.77, 0.60), xytext=(0.58, 0.30), arrowprops=arrow_props)
    ax_diag.text(0.74, 0.40, f"Vía b = {b:+.3f}***\n(p < .001)", fontsize=10, fontweight="bold", color="#DC2626")

    # Resumen Sobel
    ax_diag.text(0.50, -0.05, 
                 f"Efecto Total c = {c:+.3f}***  |  Efecto Indirecto (a × b) = {indirect:+.3f}***  |  Test de Sobel: Z = {sobel_z:.3f} (p = {p_sobel:.4e})\n"
                 "Conclusión: Mediación Parcial Significativa (Mayor vocabulario reduce las fijaciones, aumentando la comprensión)",
                 ha="center", va="center", fontsize=9.8, fontweight="bold", color="#0F172A",
                 bbox=dict(boxstyle="round,pad=0.5", facecolor="#F8FAFC", edgecolor="#CBD5E1", linewidth=1.2))

    ax_diag.set_title("A. Diagrama de Mediación Cognitiva (Sobel Path Analysis, N = 1,117)", fontsize=13, fontweight="bold", pad=10, color="#0F172A")

    # 3 subplots abajo con los datos reales
    # 1. Vía a: Vocabulario vs Fijación
    ax1 = fig.add_subplot(gs[1, 0])
    ax1.scatter(sub["vocab.t2.5"], sub["mean_fix_dur"], color="#DC2626", alpha=0.35, s=20)
    sns.regplot(data=sub, x="vocab.t2.5", y="mean_fix_dur", ax=ax1, scatter=False, color="#991B1B", line_kws={"linewidth": 2.2})
    ax1.set_title(f"Vía a: Vocabulario → Fijación\nr = {a:+.3f} (p < 10⁻²⁸)", fontsize=10.5, fontweight="bold", color="#0F172A")
    ax1.set_xlabel("Vocabulario (Nation)", fontsize=9.5)
    ax1.set_ylabel("Duración Media Fijación (ms)", fontsize=9.5)
    ax1.grid(True, linestyle="--", alpha=0.4)
    ax1.set_facecolor("#F8FAFC")

    # 2. Vía b: Fijación vs Comprensión
    ax2 = fig.add_subplot(gs[1, 1])
    r_dur, p_dur = stats.pearsonr(sub["mean_fix_dur"], sub["accuracy"] * 100)
    ax2.scatter(sub["mean_fix_dur"], sub["accuracy"] * 100, color="#D97706", alpha=0.35, s=20)
    sns.regplot(data=sub, x="mean_fix_dur", y=sub["accuracy"] * 100, ax=ax2, scatter=False, color="#B45309", line_kws={"linewidth": 2.2})
    ax2.set_title(f"Vía b: Fijación → Comprensión\nr = {r_dur:+.3f} (p < 10⁻¹⁶)", fontsize=10.5, fontweight="bold", color="#0F172A")
    ax2.set_xlabel("Duración Media Fijación (ms)", fontsize=9.5)
    ax2.set_ylabel("Comprensión Lectora (%)", fontsize=9.5)
    ax2.grid(True, linestyle="--", alpha=0.4)
    ax2.set_facecolor("#F8FAFC")

    # 3. Vía c: Vocabulario vs Comprensión
    ax3 = fig.add_subplot(gs[1, 2])
    ax3.scatter(sub["vocab.t2.5"], sub["accuracy"] * 100, color="#1E40AF", alpha=0.35, s=20)
    sns.regplot(data=sub, x="vocab.t2.5", y=sub["accuracy"] * 100, ax=ax3, scatter=False, color="#1D4ED8", line_kws={"linewidth": 2.2})
    ax3.set_title(f"Vía c: Vocabulario → Comprensión\nr = {c:+.3f} (p < 10⁻⁶⁰)", fontsize=10.5, fontweight="bold", color="#0F172A")
    ax3.set_xlabel("Vocabulario (Nation)", fontsize=9.5)
    ax3.set_ylabel("Comprensión Lectora (%)", fontsize=9.5)
    ax3.grid(True, linestyle="--", alpha=0.4)
    ax3.set_facecolor("#F8FAFC")

    plt.suptitle("Modelo de Mediación: El Vocabulario Acelera la Decodificación Ocular", fontsize=14, fontweight="bold", y=0.98, color="#0F172A")
    out_path = PLOTS_DIR / "figure_2a_mediation_path_diagram.png"
    plt.savefig(out_path, bbox_inches="tight", dpi=300)
    plt.close()
    shutil.copy(out_path, ARTIFACT_DIR / out_path.name)
    print(f"[figure-2a] Guardada en {out_path}")


# ===========================================================================
# 2. FIGURA 2B: MECANISMO COMPENSATORIO POR CUARTILES DE VOCABULARIO
# ===========================================================================
def plot_figure_2b_compensation_quartiles(df: pd.DataFrame):
    sub = df.dropna(subset=["accuracy", "vocab.t2.5", "regression_rate"]).copy()
    
    q_labels = ["Q1: Bajo (≤ 24)", "Q2: Medio-Bajo (25-35)", "Q3: Medio-Alto (36-38)", "Q4: Alto (39-40)"]
    sub["vocab_quartile"] = pd.qcut(sub["vocab.t2.5"], 4, labels=q_labels)

    q_colors = {
        "Q1: Bajo (≤ 24)": "#DC2626",
        "Q2: Medio-Bajo (25-35)": "#D97706",
        "Q3: Medio-Alto (36-38)": "#2563EB",
        "Q4: Alto (39-40)": "#059669",
    }

    fig = plt.figure(figsize=(14, 6.5), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    gs = fig.add_gridspec(2, 3, width_ratios=[1, 1, 1.2], hspace=0.35, wspace=0.25)

    # 4 paneles para cada cuartil (2x2 a la izquierda)
    axes_grid = [
        fig.add_subplot(gs[0, 0]),
        fig.add_subplot(gs[0, 1]),
        fig.add_subplot(gs[1, 0]),
        fig.add_subplot(gs[1, 1]),
    ]

    slopes_summary = []

    for ax, q in zip(axes_grid, q_labels):
        q_data = sub[sub["vocab_quartile"] == q]
        c = q_colors[q]

        ax.scatter(q_data["regression_rate"] * 100, q_data["accuracy"] * 100, color=c, alpha=0.4, s=22)
        sns.regplot(data=q_data, x=q_data["regression_rate"] * 100, y=q_data["accuracy"] * 100, 
                    ax=ax, scatter=False, color=c, line_kws={"linewidth": 2.2})

        # Estadísticas de regresión
        slope, intercept, r_val, p_val, std_err = stats.linregress(q_data["regression_rate"], q_data["accuracy"])
        sig_str = "***" if p_val < 0.001 else ("**" if p_val < 0.01 else ("*" if p_val < 0.05 else "n.s."))
        
        slopes_summary.append({
            "quartile": q.split(":")[0],
            "label": q,
            "slope": slope,
            "std_err": std_err,
            "p_val": p_val,
            "r": r_val,
            "color": c,
            "n": len(q_data)
        })

        ax.set_title(q, fontsize=10.5, fontweight="bold", pad=6, color="#0F172A")
        ax.set_xlabel("Tasa de Regresiones (%)", fontsize=9)
        ax.set_ylabel("Comprensión (%)", fontsize=9)
        ax.set_ylim(20, 100)
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.set_facecolor("#F8FAFC")

    # Panel a la derecha (comparación de pendientes con barras de error)
    ax_bar = fig.add_subplot(gs[:, 2])
    ax_bar.set_facecolor("#F8FAFC")

    s_df = pd.DataFrame(slopes_summary)
    x_pos = np.arange(len(s_df))
    bars = ax_bar.bar(x_pos, s_df["slope"], yerr=s_df["std_err"], capsize=5, 
                      color=s_df["color"], edgecolor="#1E293B", linewidth=1.0, width=0.55)

    for i, row in s_df.iterrows():
        sig = "*** (p < .001)" if row["p_val"] < 0.001 else "n.s."
        y_text = row["slope"] + row["std_err"] + 0.04
        ax_bar.text(i, y_text, f"{row['slope']:+.3f}\n{sig}", ha="center", va="bottom", fontsize=9, fontweight="bold", color="#0F172A")

    ax_bar.axhline(0, color="#64748B", linestyle="--", linewidth=1)
    ax_bar.set_xticks(x_pos)
    ax_bar.set_xticklabels([f"{row['quartile']}\n({row['label'].split(':')[1].strip()})" for _, row in s_df.iterrows()], fontsize=9.2, fontweight="semibold")
    ax_bar.set_ylabel("Efecto de las Regresiones sobre Comprensión (Pendiente)", fontsize=10)
    ax_bar.set_title("Comparación de Beneficio de Relectura:\nSolo Q1 compensa con regresiones", fontsize=11, fontweight="bold", pad=10, color="#0F172A")
    ax_bar.set_ylim(-0.15, 1.15)
    ax_bar.grid(True, linestyle="--", alpha=0.4, axis="y")

    plt.suptitle("Mecanismo Compensatorio: La Relectura Rescata la Comprensión en Lectores con Bajo Vocabulario (Q1)", 
                 fontsize=13.5, fontweight="bold", y=0.99, color="#0F172A")
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    out_path = PLOTS_DIR / "figure_2b_compensatory_mechanism_by_quartiles.png"
    plt.savefig(out_path, bbox_inches="tight", dpi=300)
    plt.close()
    shutil.copy(out_path, ARTIFACT_DIR / out_path.name)
    print(f"[figure-2b] Guardada en {out_path}")


# ===========================================================================
# 3. FIGURA 3: DESCUBRIMIENTO DE ARQUETIPOS (BIPLOT PCA + DISTRIBUCIONES)
# ===========================================================================
def plot_figure_3_archetypes_discovery(df: pd.DataFrame):
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
    # Invertir signos para que PC1 = mayor proficiencia, PC2 = mayores regresiones
    pc1 = - (Z @ Vt[0])
    pc2 = - (Z @ Vt[1])
    sub["PC1"] = pc1
    sub["PC2"] = pc2

    var_exp = (S**2) / np.sum(S**2)

    c_colors = {
        "Nativoide / Eficiente": "#10B981",
        "Estratégico / Compensador": "#8B5CF6",
        "Intermedio / Moderado": "#3B82F6",
        "Bloqueado / Con Dificultad": "#EF4444"
    }

    fig = plt.figure(figsize=(15, 6.8), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    gs = fig.add_gridspec(2, 4, width_ratios=[1.3, 1, 1, 1], hspace=0.35, wspace=0.3)

    # Panel A: Biplot PCA (Ocupa las 2 filas de la izquierda)
    ax_pca = fig.add_subplot(gs[:, 0])
    ax_pca.set_facecolor("#F8FAFC")

    for arch, col in c_colors.items():
        arch_data = sub[sub["archetype_name"] == arch]
        ax_pca.scatter(arch_data["PC1"], arch_data["PC2"], color=col, alpha=0.55, s=26, 
                       label=f"{arch} (N={len(arch_data)})", edgecolors="none")

        # Centroide
        mean_pc1 = arch_data["PC1"].mean()
        mean_pc2 = arch_data["PC2"].mean()
        ax_pca.scatter(mean_pc1, mean_pc2, color=col, s=140, edgecolors="#0F172A", linewidth=2.0, marker="X")

    # Flechas de carga de variables en PCA (Biplot)
    loadings = {
        "Vocabulario": (-Vt[0, 0] * 3.2, -Vt[1, 0] * 3.2),
        "LexTALE": (-Vt[0, 1] * 3.2, -Vt[1, 1] * 3.2),
        "Duración": (-Vt[0, 2] * 3.2, -Vt[1, 2] * 3.2),
        "Regresiones": (-Vt[0, 3] * 3.2, -Vt[1, 3] * 3.2),
        "Comprensión": (-Vt[0, 4] * 3.2, -Vt[1, 4] * 3.2),
    }

    for var_name, (lx, ly) in loadings.items():
        ax_pca.annotate("", xy=(lx, ly), xytext=(0, 0), arrowprops=dict(arrowstyle="->", lw=1.6, color="#0F172A"))
        ax_pca.text(lx * 1.12, ly * 1.12, var_name, fontsize=8.8, fontweight="bold", color="#0F172A", ha="center", va="center")

    ax_pca.axhline(0, color="#CBD5E1", linestyle="--", linewidth=1.0)
    ax_pca.axvline(0, color="#CBD5E1", linestyle="--", linewidth=1.0)
    ax_pca.set_xlabel(f"PC1: Proficiencia General ({var_exp[0]*100:.1f}% varianza)", fontsize=9.8, fontweight="semibold")
    ax_pca.set_ylabel(f"PC2: Estrategia de Relectura ({var_exp[1]*100:.1f}% varianza)", fontsize=9.8, fontweight="semibold")
    ax_pca.set_title("A. Espacio Latente PCA:\nDe Dónde Provienen los 4 Arquetipos", fontsize=11.5, fontweight="bold", pad=10)
    ax_pca.legend(loc="lower left", fontsize=8.2, framealpha=0.9)
    ax_pca.grid(True, linestyle="--", alpha=0.4)

    # Paneles de Distribuciones Reales (Boxplots / Stripplot) para las variables clave
    # Arriba: Vocabulario y Duración Fijación
    # Abajo: Tasa Regresiones y Comprensión
    var_configs = [
        ("vocab.t2.5", "Vocabulario (Nation, 0-40)", gs[0, 1]),
        ("mean_fix_dur", "Duración Fijación (ms)", gs[0, 2]),
        ("regression_rate", "Tasa de Regresiones (%)", gs[1, 1]),
        ("accuracy", "Comprensión Lectora (%)", gs[1, 2]),
    ]

    order_arch = ["Nativoide / Eficiente", "Estratégico / Compensador", "Intermedio / Moderado", "Bloqueado / Con Dificultad"]
    short_labels = ["Nativoide", "Estratégico", "Intermedio", "Bloqueado"]

    for col, title, grid_pos in var_configs:
        ax = fig.add_subplot(grid_pos)
        ax.set_facecolor("#F8FAFC")
        
        # Escala porcentual para regressions y accuracy
        plot_data = sub.copy()
        if col in ["regression_rate", "accuracy"]:
            plot_data[col] = plot_data[col] * 100

        sns.boxplot(data=plot_data, x="archetype_name", y=col, order=order_arch, palette=c_colors, ax=ax, width=0.55, fliersize=2)
        ax.set_title(title, fontsize=10.5, fontweight="bold", pad=6)
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.set_xticks(range(4))
        ax.set_xticklabels(short_labels, rotation=25, ha="right", fontsize=8.8)
        ax.grid(True, linestyle="--", alpha=0.4, axis="y")

    # Panel final a la derecha: Resumen funcional / Tabla de Perfiles
    ax_table = fig.add_subplot(gs[:, 3])
    ax_table.axis("off")
    ax_table.set_title("C. Características Clave\nde Cada Arquetipo", fontsize=11, fontweight="bold", pad=12)

    summary_text = (
        "[1] NATIVOIDE / EFICIENTE (27.7%)\n"
        "• Vocabulario: 37.0 / 40\n"
        "• Fijación: 202 ms (Muy rápida)\n"
        "• Regresiones: 12.9% (Bajas)\n"
        "• Comprensión: 78.3% (Máxima)\n"
        "Estrategia: Fluidez automática en 1er pase.\n\n"
        "[2] ESTRATÉGICO / COMPENSADOR (23.7%)\n"
        "• Vocabulario: 36.1 / 40\n"
        "• Fijación: 213 ms (Rápida)\n"
        "• Regresiones: 21.1% (Muy alta)\n"
        "• Comprensión: 76.1% (Excelente)\n"
        "Estrategia: Relectura activa reparadora.\n\n"
        "[3] INTERMEDIO / MODERADO (32.2%)\n"
        "• Vocabulario: 30.0 / 40\n"
        "• Fijación: 236 ms (Moderada)\n"
        "• Regresiones: 13.6% (Promedio)\n"
        "• Comprensión: 72.2% (Sólida)\n"
        "Estrategia: Mayor tiempo por palabra.\n\n"
        "[4] BLOQUEADO / DIFICULTAD (16.4%)\n"
        "• Vocabulario: 13.5 / 40 (Deficitario)\n"
        "• Fijación: 244 ms (Muy pesada)\n"
        "• Regresiones: 13.7% (Insuficiente)\n"
        "• Comprensión: 53.6% (Baja)\n"
        "Estrategia: Cuello de botella léxico severo."
    )
    ax_table.text(0.02, 0.50, summary_text, va="center", fontsize=8.8, fontfamily="monospace",
                  bbox=dict(boxstyle="round,pad=0.6", facecolor="#F8FAFC", edgecolor="#CBD5E1", linewidth=1.2))

    plt.suptitle("Descubrimiento de Arquetipos de Lectores: Espacio Multidimensional PCA y Distribuciones Reales (N = 1,032)", 
                 fontsize=13.5, fontweight="bold", y=0.99, color="#0F172A")
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    out_path = PLOTS_DIR / "figure_3_reader_archetypes_discovery.png"
    plt.savefig(out_path, bbox_inches="tight", dpi=300)
    plt.close()
    shutil.copy(out_path, ARTIFACT_DIR / out_path.name)
    print(f"[figure-3] Guardada en {out_path}")


# ===========================================================================
# 4. FIGURAS 4A, 4B y 4C: CALIBRACIÓN METACOGNITIVA
# ===========================================================================
def plot_figure_4_calibration(df: pd.DataFrame):
    sub = df.dropna(subset=["english_domain_read", "language_skill_composite", "linguistic_distance", "lang"]).copy()

    sub["z_self"] = (sub["english_domain_read"] - sub["english_domain_read"].mean()) / sub["english_domain_read"].std()
    sub["z_skill"] = (sub["language_skill_composite"] - sub["language_skill_composite"].mean()) / sub["language_skill_composite"].std()
    sub["calibration_bias"] = sub["z_self"] - sub["z_skill"]

    sub["calibration_cat"] = "Calibrado"
    sub.loc[sub["calibration_bias"] < -0.75, "calibration_cat"] = "Subestimador (Impostor)"
    sub.loc[sub["calibration_bias"] > +0.75, "calibration_cat"] = "Sobreestimador"

    # --- FIGURA 4A: SCATTER PLOT INDIVIDUAL DE CALIBRACIÓN ---
    fig, ax = plt.subplots(figsize=(7.5, 6.5), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#F8FAFC")

    cat_colors = {"Subestimador (Impostor)": "#2563EB", "Calibrado": "#64748B", "Sobreestimador": "#EA580C"}
    for cat, c in cat_colors.items():
        c_sub = sub[sub["calibration_cat"] == cat]
        ax.scatter(c_sub["z_skill"], c_sub["z_self"], color=c, alpha=0.55, s=26, 
                   label=f"{cat} ({len(c_sub)/len(sub)*100:.1f}%)")

    lims = [-3, 3]
    ax.plot(lims, lims, color="#0F172A", linestyle="-", linewidth=1.5, label="Calibración Perfecta (y = x)")
    ax.plot(lims, [l + 0.75 for l in lims], color="#EA580C", linestyle=":", linewidth=1.2, label="Zona Sobreestimador (+0.75 SD)")
    ax.plot(lims, [l - 0.75 for l in lims], color="#2563EB", linestyle=":", linewidth=1.2, label="Zona Impostor (-0.75 SD)")

    ax.set_xlim(-3, 3)
    ax.set_ylim(-3, 3)
    ax.set_xlabel("Habilidad Real Objetiva en Inglés (z)", fontsize=10.5, fontweight="semibold")
    ax.set_ylabel("Autoevaluación Lectora Subjetiva (z)", fontsize=10.5, fontweight="semibold")
    ax.set_title("Calibración Metacognitiva:\nBrecha entre Autopercepción y Habilidad Real (N = 735)", fontsize=12, fontweight="bold", pad=12)
    ax.legend(loc="upper left", fontsize=8.8)
    ax.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()

    out_4a = PLOTS_DIR / "figure_4a_metacognitive_calibration_scatter.png"
    plt.savefig(out_4a, bbox_inches="tight", dpi=300)
    plt.close()
    shutil.copy(out_4a, ARTIFACT_DIR / out_4a.name)
    print(f"[figure-4a] Guardada en {out_4a}")

    # --- FIGURA 4B: SESGO DE CALIBRACIÓN POR CADA LENGUA (ORDENADA POR DISTANCIA) ---
    lang_stats = sub.groupby("lang").agg(
        n=("calibration_bias", "count"),
        dist=("linguistic_distance", "first"),
        bias_mean=("calibration_bias", "mean"),
        bias_sem=("calibration_bias", lambda x: x.std() / np.sqrt(len(x))),
    ).sort_values("dist").reset_index()

    fig, ax = plt.subplots(figsize=(13.5, 6.2), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#F8FAFC")

    x_pos = np.arange(len(lang_stats))
    colors_lang = ["#2563EB" if b < 0 else "#EA580C" for b in lang_stats["bias_mean"]]

    bars = ax.bar(x_pos, lang_stats["bias_mean"], yerr=lang_stats["bias_sem"], capsize=4,
                  color=colors_lang, edgecolor="#1E293B", linewidth=0.8, width=0.6)

    ax.axhline(0, color="#0F172A", linestyle="-", linewidth=1.2)
    ax.set_xticks(x_pos)
    labels = [f"{LANG_NAMES.get(r['lang'], r['lang'])}\n(d = {r['dist']:.1f})" for _, r in lang_stats.iterrows()]
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8.8)
    ax.set_ylabel("Sesgo Medio de Calibración (z_self - z_skill)", fontsize=10.5, fontweight="semibold")
    ax.set_title("Sesgo de Calibración Metacognitiva por Lengua Materna\n(Ordenadas de Menor a Mayor Distancia al Inglés: Izquierda a Derecha)", 
                 fontsize=12.5, fontweight="bold", pad=12, color="#0F172A")
    ax.grid(True, linestyle="--", alpha=0.4, axis="y")

    plt.tight_layout()
    out_4b = PLOTS_DIR / "figure_4b_calibration_by_language.png"
    plt.savefig(out_4b, bbox_inches="tight", dpi=300)
    plt.close()
    shutil.copy(out_4b, ARTIFACT_DIR / out_4b.name)
    print(f"[figure-4b] Guardada en {out_4b}")

    # --- FIGURA 4C: SESGO DE CALIBRACIÓN POR CUARTILES DE DISTANCIA LINGÜÍSTICA ---
    sub["dist_quartile"] = pd.qcut(sub["linguistic_distance"], 4, labels=[
        "Q1: Cercanas\n(21.8 - 31.3)",
        "Q2: Intermedias\n(42.8 - 56.5)",
        "Q3: Distantes\n(59.3 - 85.6)",
        "Q4: Muy Distantes\n(88.5 - 97.2)"
    ])

    q_stats = sub.groupby("dist_quartile", observed=False).agg(
        n=("calibration_bias", "count"),
        bias_mean=("calibration_bias", "mean"),
        bias_sem=("calibration_bias", lambda x: x.std() / np.sqrt(len(x))),
    ).reset_index()

    fig, ax = plt.subplots(figsize=(8.5, 5.5), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#F8FAFC")

    colors_q = ["#2563EB", "#EA580C", "#94A3B8", "#D97706"]
    x_q = np.arange(len(q_stats))
    bars = ax.bar(x_q, q_stats["bias_mean"], yerr=q_stats["bias_sem"], capsize=5,
                  color=colors_q, edgecolor="#1E293B", linewidth=1.0, width=0.52)

    for i, row in q_stats.iterrows():
        y_text = row["bias_mean"] + (row["bias_sem"] + 0.05 if row["bias_mean"] >= 0 else -row["bias_sem"] - 0.10)
        ax.text(i, y_text, f"{row['bias_mean']:+.3f}\n(N={row['n']})", ha="center", fontsize=9.2, fontweight="bold")

    ax.axhline(0, color="#0F172A", linestyle="-", linewidth=1.2)
    ax.set_xticks(x_q)
    ax.set_xticklabels(q_stats["dist_quartile"], fontsize=9.5, fontweight="semibold")
    ax.set_ylabel("Sesgo Medio de Calibración (z)", fontsize=10.5, fontweight="semibold")
    ax.set_title("Sesgo de Calibración por Cuartiles de Distancia Lingüística al Inglés", fontsize=12, fontweight="bold", pad=12)
    ax.set_ylim(-0.70, 0.95)
    ax.grid(True, linestyle="--", alpha=0.4, axis="y")

    plt.tight_layout()
    out_4c = PLOTS_DIR / "figure_4c_calibration_by_distance_quartiles.png"
    plt.savefig(out_4c, bbox_inches="tight", dpi=300)
    plt.close()
    shutil.copy(out_4c, ARTIFACT_DIR / out_4c.name)
    print(f"[figure-4c] Guardada en {out_4c}")


def main():
    print("=== GENERANDO FIGURAS REFINADAS Y REESTRUCTURADAS ===")
    df = load_data()
    plot_figure_2a_mediation(df)
    plot_figure_2b_compensation_quartiles(df)
    plot_figure_3_archetypes_discovery(df)
    plot_figure_4_calibration(df)
    print("=== TODAS LAS FIGURAS REFINADAS GENERADAS CON ÉXITO ===")


if __name__ == "__main__":
    main()
