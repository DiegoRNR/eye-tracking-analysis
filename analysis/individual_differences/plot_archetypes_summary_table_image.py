"""
analysis/individual_differences/plot_archetypes_summary_table_image.py

Genera una imagen en alta resolución (300 DPI) con la tabla exacta de:
'Resumen Numérico por Campo y Arquetipo'
"""

from __future__ import annotations

import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "analysis" / "individual_differences" / "output"
PLOTS_DIR = OUTPUT_DIR / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACT_DIR = Path("/Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177")


def render_table_image():
    # Cargar datos
    df_path = OUTPUT_DIR / "master_multilevel_dataset.csv"
    df = pd.read_csv(df_path)

    cluster_cols = ["vocab.t2.5", "lextale", "mean_fix_dur", "regression_rate", "accuracy"]
    sub = df.dropna(subset=cluster_cols).copy()

    # Clustering reproducible
    import numpy as np
    from scipy.cluster.vq import kmeans2

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

    arch_order = [
        "Nativoide / Eficiente",
        "Estratégico / Compensador",
        "Intermedio / Moderado",
        "Bloqueado / Con Dificultad"
    ]

    # Metadatos de filas
    rows_def = [
        {
            "field": "Vocabulario Receptivo",
            "var": "vocab.t2.5",
            "unit": "Escala 0 a 40",
            "col": "vocab.t2.5",
            "fmt": lambda m, s: f"{m:.1f} ± {s:.1f}"
        },
        {
            "field": "Proficiencia Léxica",
            "var": "lextale",
            "unit": "% aciertos",
            "col": "lextale",
            "fmt": lambda m, s: f"{m:.1f}% ± {s:.1f}%"
        },
        {
            "field": "Duración de Fijación",
            "var": "mean_fix_dur",
            "unit": "ms",
            "col": "mean_fix_dur",
            "fmt": lambda m, s: f"{m:.1f} ± {s:.1f} ms"
        },
        {
            "field": "Tasa de Regresiones",
            "var": "regression_rate",
            "unit": "% sacadas",
            "col": "regression_rate",
            "fmt": lambda m, s: f"{m*100:.1f}% ± {s*100:.1f}%"
        },
        {
            "field": "Precisión de Comprensión",
            "var": "accuracy",
            "unit": "% aciertos",
            "col": "accuracy",
            "fmt": lambda m, s: f"{m*100:.1f}% ± {s*100:.1f}%"
        },
    ]

    headers = [
        "Campo Utilizado en Clustering",
        "Variable en Dataset",
        "Unidad",
        "Muestra Global\n(N = 1,032)",
        "Nativoide / Eficiente\n(N = 286, 27.7%)",
        "Estratégico / Compensador\n(N = 245, 23.7%)",
        "Intermedio / Moderado\n(N = 332, 32.2%)",
        "Bloqueado / Con Dificultad\n(N = 169, 16.4%)"
    ]

    cell_text = []
    for r in rows_def:
        col = r["col"]
        gm = sub[col].mean()
        gs = sub[col].std()
        
        row_vals = [
            r["field"],
            r["var"],
            r["unit"],
            r["fmt"](gm, gs)
        ]

        for arch in arch_order:
            sub_a = sub[sub["archetype_name"] == arch][col]
            m = sub_a.mean()
            s = sub_a.std()
            z = (m - gm) / gs
            val_str = r["fmt"](m, s)
            z_str = f"({z:+.2f} z)"
            row_vals.append(f"{val_str}\n{z_str}")

        cell_text.append(row_vals)

    # Crear figura
    fig, ax = plt.subplots(figsize=(15.2, 5.6), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    ax.axis("off")

    col_widths = [0.18, 0.11, 0.09, 0.13, 0.13, 0.13, 0.13, 0.13]

    table = ax.table(
        cellText=cell_text,
        colLabels=headers,
        colWidths=col_widths,
        loc="center",
        cellLoc="center"
    )

    table.auto_set_font_size(False)
    table.set_fontsize(8.8)
    table.scale(1.0, 2.3)

    # Estilos de encabezado
    header_base_color = "#1E293B"
    arch_colors = ["#059669", "#7C3AED", "#2563EB", "#DC2626"]

    for j in range(len(headers)):
        cell = table[0, j]
        if j < 4:
            cell.set_facecolor(header_base_color)
        else:
            cell.set_facecolor(arch_colors[j - 4])
        cell.set_text_props(color="#FFFFFF", fontweight="bold", fontsize=9.2)
        cell.set_edgecolor("#94A3B8")

    # Filas alternas y formato tipográfico
    for i in range(1, len(rows_def) + 1):
        bg = "#F8FAFC" if i % 2 == 1 else "#FFFFFF"
        for j in range(len(headers)):
            cell = table[i, j]
            cell.set_facecolor(bg)
            cell.set_edgecolor("#CBD5E1")
            
            if j == 0:
                cell.set_text_props(fontweight="bold", color="#0F172A", ha="left")
            elif j == 1:
                cell.set_text_props(color="#475569", fontfamily="monospace", fontsize=8.2)
            elif j == 2:
                cell.set_text_props(color="#64748B", fontsize=8.3)
            elif j == 3:
                cell.set_text_props(fontweight="semibold", color="#0F172A")
            elif j >= 4:
                cell.set_text_props(fontweight="semibold", color="#0F172A")

    plt.suptitle(
        "Resumen Numérico por Campo y Arquetipo de Lectura L2",
        fontsize=14.0, fontweight="bold", y=0.94, color="#0F172A"
    )
    plt.title(
        "Variables de Entrada y Parámetros del Clustering k-Means Multidimensional (N = 1,032)\nValores: Media ± Desviación Estándar (entre paréntesis: puntuación estandarizada z-score respecto a la media global)",
        fontsize=9.2, color="#475569", pad=12
    )

    plt.tight_layout()
    out_path = PLOTS_DIR / "tabla_resumen_arquetipos.png"
    plt.savefig(out_path, bbox_inches="tight", dpi=300)
    plt.close()

    shutil.copy(out_path, ARTIFACT_DIR / out_path.name)
    print(f"[success] Tabla guardada como imagen en {out_path} y copiada a {ARTIFACT_DIR / out_path.name}")


if __name__ == "__main__":
    render_table_image()

