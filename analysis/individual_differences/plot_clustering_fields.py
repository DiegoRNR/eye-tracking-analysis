"""
analysis/individual_differences/plot_clustering_fields.py

Genera una figura de alta resolución (300 DPI) que detalla explícitamente:
1. Los 5 campos utilizados en el clustering k-Means de arquetipos lectores.
2. Los valores asociados (media, desviación estándar y z-score) para la muestra global y cada arquetipo.
3. Un gráfico de perfiles de centroides que ilustra visualmente la separación en cada dimensión.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch
from scipy.cluster.vq import kmeans2

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "analysis" / "individual_differences" / "output"
PLOTS_DIR = OUTPUT_DIR / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACT_DIR = Path("/Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177")


def generate_clustering_fields_plot():
    # 1. Cargar dataset y preparar variables
    df_path = OUTPUT_DIR / "master_multilevel_dataset.csv"
    df = pd.read_csv(df_path)

    cluster_cols = ["vocab.t2.5", "lextale", "mean_fix_dur", "regression_rate", "accuracy"]
    sub = df.dropna(subset=cluster_cols).copy()

    # Estandarizar
    Z = np.zeros((len(sub), len(cluster_cols)))
    for i, c in enumerate(cluster_cols):
        Z[:, i] = (sub[c] - sub[c].mean()) / sub[c].std()

    # Clustering reproducible
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
    arch_colors = {
        "Nativoide / Eficiente": "#10B981",
        "Estratégico / Compensador": "#8B5CF6",
        "Intermedio / Moderado": "#3B82F6",
        "Bloqueado / Con Dificultad": "#EF4444"
    }

    # 2. Configurar la figura (2 paneles: Tabla arriba, Gráfico de perfiles abajo)
    fig = plt.figure(figsize=(13.5, 9.2), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    gs = fig.add_gridspec(2, 1, height_ratios=[1.1, 1.0], hspace=0.32)

    # -----------------------------------------------------------------------
    # PANEL SUPERIOR: TABLA DE CAMPOS Y VALORES ASOCIADOS
    # -----------------------------------------------------------------------
    ax_table = fig.add_subplot(gs[0])
    ax_table.axis("off")

    fields_meta = [
        {
            "col": "vocab.t2.5",
            "name": "Vocabulario Receptivo (Nation)",
            "construct": "Amplitud de Léxico L2",
            "unit": "Escala 0 - 40",
            "format": lambda m, s: f"{m:.1f} ± {s:.1f}"
        },
        {
            "col": "lextale",
            "name": "Proficiencia Léxica (LexTALE)",
            "construct": "Acceso Léxico y Fluidez",
            "unit": "Porcentaje (0 - 100%)",
            "format": lambda m, s: f"{m:.1f}% ± {s:.1f}%"
        },
        {
            "col": "mean_fix_dur",
            "name": "Duración Media de Fijación",
            "construct": "Carga de Procesamiento Local",
            "unit": "Milisegundos (ms)",
            "format": lambda m, s: f"{m:.1f} ± {s:.1f} ms"
        },
        {
            "col": "regression_rate",
            "name": "Tasa de Regresiones Sacádicas",
            "construct": "Monitoreo y Relectura",
            "unit": "Porcentaje (0 - 100%)",
            "format": lambda m, s: f"{m*100:.1f}% ± {s*100:.1f}%"
        },
        {
            "col": "accuracy",
            "name": "Precisión de Comprensión",
            "construct": "Construcción del Significado L2",
            "unit": "Porcentaje (0 - 100%)",
            "format": lambda m, s: f"{m*100:.1f}% ± {s*100:.1f}%"
        },
    ]

    # Construir datos para la tabla
    headers = [
        "Campo Utilizado",
        "Constructo Evaluado",
        "Unidad",
        "Muestra Global\n(N = 1,032)",
        "Nativoide\n(N = 286, 27.7%)",
        "Estratégico\n(N = 245, 23.7%)",
        "Intermedio\n(N = 332, 32.2%)",
        "Bloqueado\n(N = 169, 16.4%)"
    ]

    cell_data = []
    for f in fields_meta:
        col = f["col"]
        global_m = sub[col].mean()
        global_s = sub[col].std()
        row = [
            f["name"],
            f["construct"],
            f["unit"],
            f["format"](global_m, global_s)
        ]
        for arch in arch_order:
            sub_a = sub[sub["archetype_name"] == arch][col]
            m = sub_a.mean()
            s = sub_a.std()
            z = (m - global_m) / global_s
            val_str = f["format"](m, s)
            z_str = f"({z:+.2f} z)"
            row.append(f"{val_str}\n{z_str}")
        cell_data.append(row)

    table = ax_table.table(
        cellText=cell_data,
        colLabels=headers,
        loc="center",
        cellLoc="center"
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8.5)
    table.scale(1.0, 2.1)

    # Estilizar la tabla
    header_color = "#1E293B"
    for j in range(len(headers)):
        cell = table[0, j]
        cell.set_facecolor(header_color)
        cell.set_text_props(color="#FFFFFF", fontweight="bold", fontsize=9.0)
        cell.set_edgecolor("#CBD5E1")

    # Colores por columna de arquetipo en encabezados
    arch_header_colors = ["#059669", "#7C3AED", "#2563EB", "#DC2626"]
    for j, c in enumerate(arch_header_colors, start=4):
        cell = table[0, j]
        cell.set_facecolor(c)

    # Filas alternas y formato
    for i in range(1, len(fields_meta) + 1):
        bg = "#F8FAFC" if i % 2 == 1 else "#FFFFFF"
        for j in range(len(headers)):
            cell = table[i, j]
            cell.set_facecolor(bg)
            cell.set_edgecolor("#E2E8F0")
            if j == 0:
                cell.set_text_props(fontweight="bold", ha="left")
            elif j in [1, 2]:
                cell.set_text_props(color="#475569")
            elif j == 3:
                cell.set_text_props(fontweight="semibold", color="#0F172A")
            elif j >= 4:
                # Subrayar los valores según arquetipo
                cell.set_text_props(fontweight="semibold")

    ax_table.set_title(
        "A. Matriz de Variables del Clustering k-Means: Definición y Valores Asociados por Arquetipo",
        fontsize=12, fontweight="bold", pad=12, color="#0F172A", loc="left"
    )

    # -----------------------------------------------------------------------
    # PANEL INFERIOR: PERFILES DE CENTROIDES (Z-SCORES)
    # -----------------------------------------------------------------------
    ax_bar = fig.add_subplot(gs[1])
    ax_bar.set_facecolor("#FAFAFA")

    # Calcular z-scores de centroides
    dim_names = [
        "Vocabulario\n(vocab.t2.5)",
        "LexTALE\n(lextale)",
        "Fijación Ocular\n(mean_fix_dur)",
        "Regresiones\n(regression_rate)",
        "Comprensión\n(accuracy)"
    ]
    x = np.arange(len(dim_names))
    width = 0.19

    for i, arch in enumerate(arch_order):
        sub_a = sub[sub["archetype_name"] == arch]
        z_scores = []
        for col in cluster_cols:
            m = sub_a[col].mean()
            gm = sub[col].mean()
            gsd = sub[col].std()
            z_scores.append((m - gm) / gsd)

        pos = x + (i - 1.5) * width
        bars = ax_bar.bar(
            pos, z_scores, width=width,
            color=arch_colors[arch],
            label=f"{arch} (N = {len(sub_a)})",
            alpha=0.90, edgecolor="#FFFFFF", linewidth=1.2
        )

        # Anotación numérica sobre/debajo de cada barra
        for bar, z in zip(bars, z_scores):
            va = "bottom" if z >= 0 else "top"
            offset = 0.05 if z >= 0 else -0.05
            ax_bar.text(
                bar.get_x() + bar.get_width() / 2,
                z + offset,
                f"{z:+.2f}",
                ha="center", va=va,
                fontsize=7.8, fontweight="bold",
                color="#1E293B"
            )

    ax_bar.axhline(0, color="#64748B", linestyle="--", linewidth=1.0, alpha=0.8)
    ax_bar.set_ylabel("Puntuación Estandarizada (z-score)", fontsize=10, fontweight="bold", color="#1E293B")
    ax_bar.set_xticks(x)
    ax_bar.set_xticklabels(dim_names, fontsize=9.5, fontweight="semibold", color="#0F172A")
    ax_bar.set_ylim(-2.3, 1.8)
    ax_bar.grid(axis="y", linestyle=":", alpha=0.5)
    ax_bar.legend(loc="upper right", framealpha=0.95, facecolor="#FFFFFF", edgecolor="#CBD5E1", fontsize=8.8)
    ax_bar.set_title(
        "B. Perfiles Comparativos de los Centroides (Magnitud del Efecto en Desviaciones Estándar)",
        fontsize=12, fontweight="bold", pad=10, color="#0F172A", loc="left"
    )

    plt.suptitle(
        "Variables de Entrada del Clustering de Lectores L2 y Desglose Cuantitativo por Arquetipo",
        fontsize=14, fontweight="bold", y=0.98, color="#0F172A"
    )

    out_path = PLOTS_DIR / "clustering_fields_and_values.png"
    plt.savefig(out_path, bbox_inches="tight", dpi=300)
    plt.close()

    shutil.copy(out_path, ARTIFACT_DIR / out_path.name)
    print(f"[success] Figura guardada en {out_path} y copiada a {ARTIFACT_DIR / out_path.name}")


if __name__ == "__main__":
    generate_clustering_fields_plot()

