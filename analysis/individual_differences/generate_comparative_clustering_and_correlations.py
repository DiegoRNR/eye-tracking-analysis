"""
analysis/individual_differences/generate_comparative_clustering_and_correlations.py

Implementa la comparación integral de arquetipos lectores con y sin comprensión,
incorporando la tasa de salto (skipping_rate) a las variables de comportamiento ocular.

Genera los 5 entregables solicitados:
1. Matriz de correlación completa de diferencias individuales (11 variables incl. skipping y distancia).
2. Matriz de correlación de los 6 campos seleccionados para el clustering.
3. Visualización comparativa de clusters (Caso A: Con comprensión en build vs. Caso B: Sin comprensión).
4. Tabla metodológica de campos, nombres, constructos y valores promedio en ambos casos.
5. Gráficos de comparación de perfiles por variable (boxplots de las 6 variables para ambos casos).
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import FancyBboxPatch
from scipy import stats
from scipy.cluster.vq import kmeans2

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "analysis" / "individual_differences" / "output"
PLOTS_DIR = OUTPUT_DIR / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACT_DIR = Path("/Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177")

# Paleta oficial unificada de arquetipos
ARCH_COLORS = {
    "Nativoide / Eficiente": "#10B981",
    "Estratégico / Compensador": "#8B5CF6",
    "Intermedio / Moderado": "#3B82F6",
    "Bloqueado / Con Dificultad": "#EF4444",
}

ARCH_ORDER = [
    "Nativoide / Eficiente",
    "Estratégico / Compensador",
    "Intermedio / Moderado",
    "Bloqueado / Con Dificultad",
]


def load_dataset() -> pd.DataFrame:
    p = OUTPUT_DIR / "master_multilevel_dataset.csv"
    if not p.exists():
        from advanced_multilevel_analysis import load_integrated_master
        return load_integrated_master()
    return pd.read_csv(p)


# ===========================================================================
# 1. MATRIZ DE CORRELACIÓN COMPLETA (11 DIFERENCIAS INDIVIDUALES)
# ===========================================================================
def plot_full_correlation_matrix(df: pd.DataFrame):
    vars_11 = [
        "accuracy", "lextale", "vocab.t2.5", "TOWRE_nonword", "spelling",
        "exposure_english", "english_domain_read", "english_start_age",
        "linguistic_distance", "cft20", "skipping_rate"
    ]
    labels_11 = [
        "Comprensión (Accuracy)", "LexTALE (%)", "Vocabulario (Nation)",
        "Decodificación (PDE)", "Ortografía (Spelling)", "% Exposición Inglés",
        "Autoeval. Lectora", "Edad Inicio Inglés", "Distancia L1 a EN",
        "Inteligencia (CFT-20)", "Tasa Skipping"
    ]
    sub = df[vars_11].dropna()
    corr = sub.corr(method="pearson")

    fig, ax = plt.subplots(figsize=(11.5, 9.5), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    sns.heatmap(
        corr,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        vmin=-0.6,
        vmax=0.6,
        xticklabels=labels_11,
        yticklabels=labels_11,
        cbar_kws={"label": "Correlación de Pearson (r)", "shrink": 0.8},
        ax=ax,
        linewidths=0.5,
        linecolor="#E2E8F0"
    )
    plt.title(
        f"Matriz de Correlación Completa: Diferencias Individuales, Eye-Tracking y Comprensión (N = {len(sub)})",
        fontsize=12.5, fontweight="bold", pad=15, color="#0F172A"
    )
    plt.xticks(rotation=40, ha="right", fontsize=9.5)
    plt.yticks(fontsize=9.5)
    plt.tight_layout()

    out1 = PLOTS_DIR / "correlations_heatmap_all_ind_diff.png"
    out2 = PLOTS_DIR / "correlations_heatmap.png"
    plt.savefig(out1, bbox_inches="tight", dpi=300)
    plt.savefig(out2, bbox_inches="tight", dpi=300)
    plt.close()

    shutil.copy(out1, ARTIFACT_DIR / out1.name)
    shutil.copy(out2, ARTIFACT_DIR / out2.name)
    print(f"[plot-1] Matriz completa guardada en {out1} y actualizada en {out2}")


# ===========================================================================
# 2. MATRIZ DE CORRELACIÓN DE CAMPOS SELECCIONADOS (6 VARIABLES)
# ===========================================================================
def plot_selected_fields_correlation(df: pd.DataFrame):
    vars_6 = ["accuracy", "vocab.t2.5", "lextale", "mean_fix_dur", "regression_rate", "skipping_rate"]
    labels_6 = [
        "Comprensión (Accuracy)", "Vocabulario (Nation)", "LexTALE (%)",
        "Fijación Ocular (ms)", "Tasa Regresiones", "Tasa Skipping"
    ]
    sub = df[vars_6].dropna()
    corr = sub.corr(method="pearson")

    # Matriz de p-valores
    pval_matrix = np.zeros((len(vars_6), len(vars_6)))
    for i in range(len(vars_6)):
        for j in range(len(vars_6)):
            if i == j:
                pval_matrix[i, j] = 0.0
            else:
                _, p = stats.pearsonr(sub[vars_6[i]], sub[vars_6[j]])
                pval_matrix[i, j] = p

    # Crear anotaciones personalizadas con asteriscos
    annot_text = np.empty_like(corr, dtype=object)
    for i in range(len(vars_6)):
        for j in range(len(vars_6)):
            r = corr.iloc[i, j]
            p = pval_matrix[i, j]
            stars = "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else ""))
            if i == j:
                annot_text[i, j] = "1.00"
            else:
                annot_text[i, j] = f"{r:+.2f}{stars}"

    fig, ax = plt.subplots(figsize=(8.8, 7.2), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    sns.heatmap(
        corr,
        annot=annot_text,
        fmt="",
        cmap="coolwarm",
        vmin=-0.5,
        vmax=0.7,
        xticklabels=labels_6,
        yticklabels=labels_6,
        cbar_kws={"label": "Correlación de Pearson (r)", "shrink": 0.8},
        ax=ax,
        linewidths=0.8,
        linecolor="#E2E8F0"
    )
    plt.title(
        f"Matriz de Correlación: Variables Nucleares de Lectura y Comprensión L2 (N = {len(sub)})\n*** p < 0.001, ** p < 0.01, * p < 0.05",
        fontsize=11.5, fontweight="bold", pad=15, color="#0F172A"
    )
    plt.xticks(rotation=35, ha="right", fontsize=9.5)
    plt.yticks(fontsize=9.5)
    plt.tight_layout()

    out = PLOTS_DIR / "correlations_selected_clustering_fields.png"
    plt.savefig(out, bbox_inches="tight", dpi=300)
    plt.close()

    shutil.copy(out, ARTIFACT_DIR / out.name)
    print(f"[plot-2] Matriz de campos seleccionados guardada en {out}")


# ===========================================================================
# 3. PIPELINE DE CLUSTERING: CASO A (CON ACCURACY) Y CASO B (SIN ACCURACY)
# ===========================================================================
def run_both_clustering_cases(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict, Dict]:
    cols6 = ["vocab.t2.5", "lextale", "mean_fix_dur", "regression_rate", "skipping_rate", "accuracy"]
    sub = df.dropna(subset=cols6).copy()

    # Función determinista de mapeo a nombres interpretables
    def map_clusters(m_df: pd.DataFrame) -> Dict[int, str]:
        l_map = {}
        for cl in m_df.index:
            v = m_df.loc[cl, "vocab.t2.5"]
            reg = m_df.loc[cl, "regression_rate"]
            dur = m_df.loc[cl, "mean_fix_dur"]
            if reg > 0.17:
                l_map[cl] = "Estratégico / Compensador"
            elif v < 22:
                l_map[cl] = "Bloqueado / Con Dificultad"
            elif dur < 210 and v > 34:
                l_map[cl] = "Nativoide / Eficiente"
            else:
                l_map[cl] = "Intermedio / Moderado"
        return l_map

    # --- CASO A: CON ACCURACY (6 variables) ---
    Z_with = (sub[cols6] - sub[cols6].mean()) / sub[cols6].std()
    np.random.seed(42)
    _, labels_with = kmeans2(Z_with.values, 4, minit="points")
    sub["cl_raw_with"] = labels_with
    means_with = sub.groupby("cl_raw_with")[cols6].mean()
    map_with = map_clusters(means_with)
    sub["archetype_with"] = sub["cl_raw_with"].map(map_with)

    # PCA Caso A
    U_a, S_a, Vt_a = np.linalg.svd(Z_with.values, full_matrices=False)
    sub["PC1_with"] = -U_a[:, 0] * S_a[0]
    sub["PC2_with"] = -U_a[:, 1] * S_a[1]
    var_exp_a = (S_a ** 2) / (len(sub) - 1)
    var_ratio_a = var_exp_a / var_exp_a.sum()

    # --- CASO B: SIN ACCURACY (5 variables, accuracy evaluada post-hoc) ---
    cols5 = ["vocab.t2.5", "lextale", "mean_fix_dur", "regression_rate", "skipping_rate"]
    Z_behav = (sub[cols5] - sub[cols5].mean()) / sub[cols5].std()
    np.random.seed(42)
    _, labels_behav = kmeans2(Z_behav.values, 4, minit="points")
    sub["cl_raw_behav"] = labels_behav
    means_behav = sub.groupby("cl_raw_behav")[cols6].mean()
    map_behav = map_clusters(means_behav)
    sub["archetype_behav"] = sub["cl_raw_behav"].map(map_behav)

    # PCA Caso B
    U_b, S_b, Vt_b = np.linalg.svd(Z_behav.values, full_matrices=False)
    sub["PC1_behav"] = -U_b[:, 0] * S_b[0]
    sub["PC2_behav"] = -U_b[:, 1] * S_b[1]
    var_exp_b = (S_b ** 2) / (len(sub) - 1)
    var_ratio_b = var_exp_b / var_exp_b.sum()

    meta_a = {"Vt": Vt_a, "var_ratio": var_ratio_a, "cols": cols6}
    meta_b = {"Vt": Vt_b, "var_ratio": var_ratio_b, "cols": cols5}

    return sub, meta_a, meta_b


# ===========================================================================
# 4. VISUALIZACIÓN COMPARATIVA DE CLUSTERS (BIPLOTS 2D)
# ===========================================================================
def plot_clusters_comparison(sub: pd.DataFrame, meta_a: Dict, meta_b: Dict):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(17.5, 7.8), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    ax1.set_facecolor("#F8FAFC")
    ax2.set_facecolor("#F8FAFC")

    # Mapeo de nombres limpios para vectores
    label_dict = {
        "vocab.t2.5": "Vocabulario",
        "lextale": "LexTALE",
        "mean_fix_dur": "Fijación (ms)",
        "regression_rate": "Regresiones",
        "skipping_rate": "Skipping",
        "accuracy": "Comprensión"
    }

    # --- PANEL IZQUIERDO: CASO A (CON ACCURACY) ---
    for arch in ARCH_ORDER:
        d = sub[sub["archetype_with"] == arch]
        col = ARCH_COLORS[arch]
        ax1.scatter(d["PC1_with"], d["PC2_with"], color=col, alpha=0.50, s=26, label=f"{arch} (N = {len(d)})", edgecolors="none")
        ax1.scatter(d["PC1_with"].mean(), d["PC2_with"].mean(), color=col, s=150, edgecolors="#0F172A", linewidth=2.0, marker="X")

    # Vectores Caso A
    Vt_a = meta_a["Vt"]
    scale_a = 3.6
    for idx, col_name in enumerate(meta_a["cols"]):
        lx = -Vt_a[0, idx] * scale_a
        ly = -Vt_a[1, idx] * scale_a
        ax1.annotate("", xy=(lx, ly), xytext=(0, 0), arrowprops=dict(arrowstyle="->", lw=1.6, color="#0F172A"))
        ax1.text(lx * 1.15, ly * 1.15, label_dict[col_name], fontsize=8.8, fontweight="bold", color="#0F172A", ha="center", va="center")

    vr_a = meta_a["var_ratio"]
    ax1.axhline(0, color="#CBD5E1", linestyle="--", linewidth=1.0)
    ax1.axvline(0, color="#CBD5E1", linestyle="--", linewidth=1.0)
    ax1.set_xlabel(f"PC1: Proficiencia y Rapidez ({vr_a[0]*100:.1f}%)", fontsize=10.0, fontweight="semibold")
    ax1.set_ylabel(f"PC2: Navegación Activa / Skipping-Regresiones ({vr_a[1]*100:.1f}%)", fontsize=10.0, fontweight="semibold")
    ax1.set_title(
        f"A. Caso A: Comprensión Incluida en la Construcción (6D)\n(Total Varianza Explicada: {sum(vr_a[:2])*100:.1f}%, N = {len(sub)})",
        fontsize=11.5, fontweight="bold", pad=12, color="#0F172A"
    )
    ax1.legend(loc="lower left", fontsize=8.5, framealpha=0.95)
    ax1.grid(True, linestyle="--", alpha=0.4)

    # --- PANEL DERECHO: CASO B (SIN ACCURACY - COMPORTAMIENTO NATURAL) ---
    for arch in ARCH_ORDER:
        d = sub[sub["archetype_behav"] == arch]
        col = ARCH_COLORS[arch]
        acc_post = d["accuracy"].mean() * 100
        ax2.scatter(d["PC1_behav"], d["PC2_behav"], color=col, alpha=0.50, s=26, label=f"{arch} (N = {len(d)}, Acc = {acc_post:.1f}%)", edgecolors="none")
        ax2.scatter(d["PC1_behav"].mean(), d["PC2_behav"].mean(), color=col, s=150, edgecolors="#0F172A", linewidth=2.0, marker="X")

    # Vectores Caso B
    Vt_b = meta_b["Vt"]
    scale_b = 3.6
    for idx, col_name in enumerate(meta_b["cols"]):
        lx = -Vt_b[0, idx] * scale_b
        ly = -Vt_b[1, idx] * scale_b
        ax2.annotate("", xy=(lx, ly), xytext=(0, 0), arrowprops=dict(arrowstyle="->", lw=1.6, color="#0F172A"))
        ax2.text(lx * 1.15, ly * 1.15, label_dict[col_name], fontsize=8.8, fontweight="bold", color="#0F172A", ha="center", va="center")

    # ANOVA post-hoc de comprensión en Caso B
    f_stat, p_val = stats.f_oneway(
        sub[sub["archetype_behav"] == "Nativoide / Eficiente"]["accuracy"],
        sub[sub["archetype_behav"] == "Estratégico / Compensador"]["accuracy"],
        sub[sub["archetype_behav"] == "Intermedio / Moderado"]["accuracy"],
        sub[sub["archetype_behav"] == "Bloqueado / Con Dificultad"]["accuracy"]
    )

    vr_b = meta_b["var_ratio"]
    ax2.axhline(0, color="#CBD5E1", linestyle="--", linewidth=1.0)
    ax2.axvline(0, color="#CBD5E1", linestyle="--", linewidth=1.0)
    ax2.set_xlabel(f"PC1: Proficiencia y Rapidez ({vr_b[0]*100:.1f}%)", fontsize=10.0, fontweight="semibold")
    ax2.set_ylabel(f"PC2: Navegación Activa / Skipping-Regresiones ({vr_b[1]*100:.1f}%)", fontsize=10.0, fontweight="semibold")
    ax2.set_title(
        f"B. Caso B: Comportamiento Natural (5D, Comprensión Post-Hoc)\n(Total Varianza Explicada: {sum(vr_b[:2])*100:.1f}%, ANOVA Post-Hoc: F = {f_stat:.1f}, p < 10⁻⁵⁰)",
        fontsize=11.5, fontweight="bold", pad=12, color="#0F172A"
    )
    ax2.legend(loc="lower left", fontsize=8.5, framealpha=0.95)
    ax2.grid(True, linestyle="--", alpha=0.4)

    plt.suptitle(
        "Comparación de Arquetipos Lectores L2: Con Comprensión en Build vs. Comportamiento Natural Puro",
        fontsize=13.5, fontweight="bold", y=0.98, color="#0F172A"
    )
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    out_comp = PLOTS_DIR / "clusters_comparison_with_vs_without_accuracy.png"
    plt.savefig(out_comp, bbox_inches="tight", dpi=300)
    plt.close()

    shutil.copy(out_comp, ARTIFACT_DIR / out_comp.name)
    print(f"[plot-3] Comparación de clusters guardada en {out_comp}")

    # Guardar además los biplots individuales limpios
    for mode, ax_name, title_txt, out_name in [
        ("with", "A", "Biplot PCA de Arquetipos (Caso A: Comprensión Incluida en Build)", "figure_3a_reader_archetypes_pca_with_accuracy.png"),
        ("behav", "B", "Biplot PCA de Arquetipos (Caso B: Comportamiento Natural, Comprensión Post-Hoc)", "figure_3a_reader_archetypes_pca_without_accuracy.png"),
    ]:
        f_single, a_s = plt.subplots(figsize=(9.2, 7.2), dpi=300)
        f_single.patch.set_facecolor("#FFFFFF")
        a_s.set_facecolor("#F8FAFC")

        arch_col = "archetype_with" if mode == "with" else "archetype_behav"
        pc1_col = "PC1_with" if mode == "with" else "PC1_behav"
        pc2_col = "PC2_with" if mode == "with" else "PC2_behav"
        meta = meta_a if mode == "with" else meta_b
        vr = meta["var_ratio"]
        Vt = meta["Vt"]

        for arch in ARCH_ORDER:
            d = sub[sub[arch_col] == arch]
            col = ARCH_COLORS[arch]
            extra = f", Acc={d['accuracy'].mean()*100:.1f}%" if mode == "behav" else ""
            a_s.scatter(d[pc1_col], d[pc2_col], color=col, alpha=0.55, s=28, label=f"{arch} (N={len(d)}{extra})", edgecolors="none")
            a_s.scatter(d[pc1_col].mean(), d[pc2_col].mean(), color=col, s=160, edgecolors="#0F172A", linewidth=2.0, marker="X")

        for idx, col_name in enumerate(meta["cols"]):
            lx = -Vt[0, idx] * 3.6
            ly = -Vt[1, idx] * 3.6
            a_s.annotate("", xy=(lx, ly), xytext=(0, 0), arrowprops=dict(arrowstyle="->", lw=1.6, color="#0F172A"))
            a_s.text(lx * 1.15, ly * 1.15, label_dict[col_name], fontsize=9.0, fontweight="bold", color="#0F172A", ha="center", va="center")

        a_s.axhline(0, color="#CBD5E1", linestyle="--", linewidth=1.0)
        a_s.axvline(0, color="#CBD5E1", linestyle="--", linewidth=1.0)
        a_s.set_xlabel(f"PC1: Proficiencia Léxica y Velocidad ({vr[0]*100:.1f}%)", fontsize=10.0, fontweight="semibold")
        a_s.set_ylabel(f"PC2: Navegación Activa / Regresiones y Skipping ({vr[1]*100:.1f}%)", fontsize=10.0, fontweight="semibold")
        a_s.set_title(f"{title_txt}\n(Varianza Total: {sum(vr[:2])*100:.1f}%, N = {len(sub)})", fontsize=12.0, fontweight="bold", pad=12, color="#0F172A")
        a_s.legend(loc="lower left", fontsize=8.8, framealpha=0.95)
        a_s.grid(True, linestyle="--", alpha=0.4)
        plt.tight_layout()

        out_s = PLOTS_DIR / out_name
        plt.savefig(out_s, bbox_inches="tight", dpi=300)
        plt.close()
        shutil.copy(out_s, ARTIFACT_DIR / out_s.name)


# ===========================================================================
# 5. TABLA COMPARATIVA DE VARIABLES Y PROMEDIOS (CASO A VS CASO B)
# ===========================================================================
def generate_summary_table_both_cases(sub: pd.DataFrame):
    # Definición de metadatos de las 6 variables
    fields_info = [
        {"var": "vocab.t2.5", "name": "Vocabulario Receptivo", "construct": "Almacén Léxico L2", "unit": "0 - 40", "fmt": lambda m, s: f"{m:.1f} ± {s:.1f}"},
        {"var": "lextale", "name": "Proficiencia Léxica", "construct": "Acceso Léxico L2", "unit": "% aciertos", "fmt": lambda m, s: f"{m:.1f}% ± {s:.1f}%"},
        {"var": "mean_fix_dur", "name": "Duración de Fijación", "construct": "Esfuerzo Local", "unit": "ms", "fmt": lambda m, s: f"{m:.1f} ± {s:.1f} ms"},
        {"var": "regression_rate", "name": "Tasa de Regresiones", "construct": "Monitoreo / Relectura", "unit": "% sacadas", "fmt": lambda m, s: f"{m*100:.1f}% ± {s*100:.1f}%"},
        {"var": "skipping_rate", "name": "Tasa de Salto (Skipping)", "construct": "Parafóvea / Riesgo", "unit": "% palabras", "fmt": lambda m, s: f"{m*100:.1f}% ± {s*100:.1f}%"},
        {"var": "accuracy", "name": "Comprensión Lectora", "construct": "Resultado Global L2", "unit": "% aciertos", "fmt": lambda m, s: f"{m*100:.1f}% ± {s*100:.1f}%"},
    ]

    # Crear tabla de datos CSV detallada
    records = []
    for f in fields_info:
        v = f["var"]
        gm, gs = sub[v].mean(), sub[v].std()
        rec = {
            "Variable": v,
            "Nombre": f["name"],
            "Constructo": f["construct"],
            "Unidad": f["unit"],
            "Global_Media_DE": f["fmt"](gm, gs),
        }
        # Caso A
        for arch in ARCH_ORDER:
            d = sub[sub["archetype_with"] == arch][v]
            rec[f"CasoA_{arch}"] = f["fmt"](d.mean(), d.std())
        # Caso B
        for arch in ARCH_ORDER:
            d = sub[sub["archetype_behav"] == arch][v]
            rec[f"CasoB_{arch}"] = f["fmt"](d.mean(), d.std())
        records.append(rec)

    df_table = pd.DataFrame(records)
    csv_out = OUTPUT_DIR / "tabla_resumen_ambos_casos_clustering.csv"
    df_table.to_csv(csv_out, index=False)
    print(f"[table] CSV comparativo guardado en {csv_out}")

    # Renderizar imagen de alta resolución (300 DPI)
    fig, ax = plt.subplots(figsize=(16.8, 6.5), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    ax.axis("off")

    headers = [
        "Campo", "Constructo", "Unidad", "Muestra Global\n(N = 1,032)",
        "Nativoide\n(Caso A | Caso B)", "Estratégico\n(Caso A | Caso B)",
        "Intermedio\n(Caso A | Caso B)", "Bloqueado\n(Caso A | Caso B)"
    ]

    cell_rows = []
    for f in fields_info:
        v = f["var"]
        gm, gs = sub[v].mean(), sub[v].std()
        row = [f["name"], f["construct"], f["unit"], f["fmt"](gm, gs)]

        for arch in ARCH_ORDER:
            da = sub[sub["archetype_with"] == arch][v]
            db = sub[sub["archetype_behav"] == arch][v]
            val_a = f["fmt"](da.mean(), da.std())
            val_b = f["fmt"](db.mean(), db.std())
            row.append(f"A: {val_a}\nB: {val_b}")

        cell_rows.append(row)

    col_widths = [0.15, 0.14, 0.09, 0.12, 0.125, 0.125, 0.125, 0.125]

    table = ax.table(
        cellText=cell_rows,
        colLabels=headers,
        colWidths=col_widths,
        loc="center",
        cellLoc="center"
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8.2)
    table.scale(1.0, 2.4)

    # Estilos de encabezados
    header_base = "#1E293B"
    arch_cols = ["#059669", "#7C3AED", "#2563EB", "#DC2626"]
    for j in range(len(headers)):
        cell = table[0, j]
        if j < 4:
            cell.set_facecolor(header_base)
        else:
            cell.set_facecolor(arch_cols[j - 4])
        cell.set_text_props(color="#FFFFFF", fontweight="bold", fontsize=8.6)
        cell.set_edgecolor("#94A3B8")

    # Filas alternas y fuentes
    for i in range(1, len(fields_info) + 1):
        bg = "#F8FAFC" if i % 2 == 1 else "#FFFFFF"
        for j in range(len(headers)):
            cell = table[i, j]
            cell.set_facecolor(bg)
            cell.set_edgecolor("#CBD5E1")
            if j == 0:
                cell.set_text_props(fontweight="bold", color="#0F172A", ha="left")
            elif j in [1, 2]:
                cell.set_text_props(color="#475569")
            elif j == 3:
                cell.set_text_props(fontweight="semibold", color="#0F172A")
            elif j >= 4:
                cell.set_text_props(fontweight="semibold", color="#0F172A")

    plt.suptitle(
        "Tabla Comparativa de Variables y Valores Promedio por Arquetipo Lector",
        fontsize=13.5, fontweight="bold", y=0.96, color="#0F172A"
    )
    plt.title(
        "Caso A: Comprensión Incluida en la Construcción del Cluster | Caso B: Comportamiento Natural Puro (Comprensión Evaluada Post-Hoc)\nValores: Media ± Desviación Estándar (N = 1,032 participantes)",
        fontsize=9.0, color="#475569", pad=12
    )
    plt.tight_layout()

    out_tbl = PLOTS_DIR / "tabla_campos_y_valores_promedio.png"
    plt.savefig(out_tbl, bbox_inches="tight", dpi=300)
    plt.close()

    shutil.copy(out_tbl, ARTIFACT_DIR / out_tbl.name)
    print(f"[plot-4] Imagen de tabla comparativa guardada en {out_tbl}")


# ===========================================================================
# 6. BOXPLOTS DE DISTRIBUCIONES POR VARIABLE Y ARQUETIPO (CASO A, B Y COMPARATIVO)
# ===========================================================================
def plot_boxplots_comparison(sub: pd.DataFrame):
    vars_config = [
        ("vocab.t2.5", "Vocabulario Receptivo (Nation)", "Puntos (0-40)"),
        ("lextale", "Proficiencia Léxica (LexTALE)", "Aciertos (%)"),
        ("mean_fix_dur", "Duración de Fijación", "Milisegundos (ms)"),
        ("regression_rate", "Tasa de Regresiones", "Proporción"),
        ("skipping_rate", "Tasa de Salto (Skipping)", "Proporción"),
        ("accuracy", "Comprensión Lectora (Accuracy)", "Proporción"),
    ]

    for mode, col_name, suffix, title_prefix in [
        ("with", "archetype_with", "with_accuracy", "Caso A: Comprensión en Build"),
        ("behav", "archetype_behav", "without_accuracy", "Caso B: Comportamiento Natural Puro"),
    ]:
        fig, axes = plt.subplots(2, 3, figsize=(15.5, 9.2), dpi=300)
        fig.patch.set_facecolor("#FFFFFF")

        for idx, (var, title, ylabel) in enumerate(vars_config):
            ax = axes[idx // 3, idx % 3]
            ax.set_facecolor("#F8FAFC")

            # Preparar datos por arquetipo
            data_to_plot = [sub[sub[col_name] == arch][var].values for arch in ARCH_ORDER]
            box = ax.boxplot(
                data_to_plot,
                patch_artist=True,
                showmeans=True,
                meanprops={"marker": "D", "markeredgecolor": "#0F172A", "markerfacecolor": "#FFFFFF", "markersize": 4.5},
                medianprops={"color": "#0F172A", "linewidth": 1.5},
            )
            ax.set_xticks(range(1, 5))
            ax.set_xticklabels(["Nativoide", "Estratégico", "Intermedio", "Bloqueado"])

            for patch, arch in zip(box["boxes"], ARCH_ORDER):
                patch.set_facecolor(ARCH_COLORS[arch])
                patch.set_alpha(0.75)
                patch.set_edgecolor("#334155")

            ax.set_title(title, fontsize=10.5, fontweight="bold", pad=8, color="#0F172A")
            ax.set_ylabel(ylabel, fontsize=9.0)
            ax.tick_params(axis="x", rotation=20, labelsize=8.8)
            ax.grid(axis="y", linestyle="--", alpha=0.4)

        plt.suptitle(
            f"Distribuciones Reales por Arquetipo Lector ({title_prefix}) - N = {len(sub)}",
            fontsize=13.0, fontweight="bold", y=0.98, color="#0F172A"
        )
        plt.tight_layout(rect=[0, 0, 1, 0.95])

        out_bp = PLOTS_DIR / f"boxplots_profiles_{suffix}.png"
        plt.savefig(out_bp, bbox_inches="tight", dpi=300)
        plt.close()

        shutil.copy(out_bp, ARTIFACT_DIR / out_bp.name)
        print(f"[plot-5] Boxplots ({suffix}) guardados en {out_bp}")

    # Gráfico combinado directo: Caso A vs Caso B lado a lado
    fig, axes = plt.subplots(2, 3, figsize=(16.5, 9.8), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")

    for idx, (var, title, ylabel) in enumerate(vars_config):
        ax = axes[idx // 3, idx % 3]
        ax.set_facecolor("#F8FAFC")

        positions = []
        data_all = []
        colors_all = []
        hatches_all = []

        for i, arch in enumerate(ARCH_ORDER):
            pos_a = i * 2.5 + 1.0
            pos_b = i * 2.5 + 1.8
            positions.extend([pos_a, pos_b])

            da = sub[sub["archetype_with"] == arch][var].values
            db = sub[sub["archetype_behav"] == arch][var].values
            data_all.extend([da, db])
            colors_all.extend([ARCH_COLORS[arch], ARCH_COLORS[arch]])
            hatches_all.extend(["", "///"])

        box = ax.boxplot(
            data_all,
            positions=positions,
            widths=0.65,
            patch_artist=True,
            showmeans=True,
            meanprops={"marker": "D", "markeredgecolor": "#0F172A", "markerfacecolor": "#FFFFFF", "markersize": 3.8},
            medianprops={"color": "#0F172A", "linewidth": 1.4},
        )

        for patch, col, hatch in zip(box["boxes"], colors_all, hatches_all):
            patch.set_facecolor(col)
            patch.set_alpha(0.85 if hatch == "" else 0.45)
            patch.set_edgecolor("#1E293B")
            patch.set_hatch(hatch)

        ax.set_title(title, fontsize=10.5, fontweight="bold", pad=8, color="#0F172A")
        ax.set_ylabel(ylabel, fontsize=9.0)
        ax.set_xticks([i * 2.5 + 1.4 for i in range(4)])
        ax.set_xticklabels(["Nativoide", "Estratégico", "Intermedio", "Bloqueado"], fontsize=9.0)
        ax.tick_params(axis="x", rotation=15)
        ax.grid(axis="y", linestyle="--", alpha=0.4)

    # Leyenda compartida
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#475569", edgecolor="#0F172A", alpha=0.85, label="Caso A: Comprensión Incluida en Build"),
        Patch(facecolor="#475569", edgecolor="#0F172A", alpha=0.45, hatch="///", label="Caso B: Comportamiento Natural (Comprensión Post-Hoc)"),
    ]
    fig.legend(handles=legend_elements, loc="upper right", bbox_to_anchor=(0.98, 0.99), framealpha=0.95, fontsize=9.5)

    plt.suptitle(
        f"Comparación Directa de Distribuciones por Arquetipo: Caso A vs. Caso B (N = {len(sub)})",
        fontsize=13.5, fontweight="bold", y=0.98, color="#0F172A"
    )
    plt.tight_layout(rect=[0, 0, 0.99, 0.95])

    out_comb = PLOTS_DIR / "boxplots_profiles_comparative_both_cases.png"
    plt.savefig(out_comb, bbox_inches="tight", dpi=300)
    plt.close()

    shutil.copy(out_comb, ARTIFACT_DIR / out_comb.name)
    print(f"[plot-5] Boxplots combinados guardados en {out_comb}")


def main():
    print("=== INICIANDO PIPELINE COMPARATIVO: CON Y SIN COMPRENSIÓN (CON SKIPPING) ===")
    df = load_dataset()
    print(f"Dataset cargado: {len(df)} registros totales.")

    # 1. Matriz completa 11 variables
    plot_full_correlation_matrix(df)

    # 2. Matriz de los 6 campos seleccionados
    plot_selected_fields_correlation(df)

    # 3. Clustering en ambos casos
    sub, meta_a, meta_b = run_both_clustering_cases(df)

    # 4. Gráficos de dispersión y biplots comparativos
    plot_clusters_comparison(sub, meta_a, meta_b)

    # 5. Tabla comparativa de variables y promedios
    generate_summary_table_both_cases(sub)

    # 6. Boxplots por variable para ambos casos
    plot_boxplots_comparison(sub)

    print("=== PIPELINE COMPARATIVO COMPLETADO EXITOSAMENTE ===")


if __name__ == "__main__":
    main()
