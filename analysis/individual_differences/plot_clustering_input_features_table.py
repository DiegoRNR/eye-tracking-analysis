"""
analysis/individual_differences/plot_clustering_input_features_table.py

Genera una imagen en alta resolución (300 DPI) con la tabla metodológica
de variables de entrada utilizadas para construir el clustering k-Means,
sin desglose por arquetipos.
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


def render_input_features_table():
    df_path = OUTPUT_DIR / "master_multilevel_dataset.csv"
    df = pd.read_csv(df_path)

    cluster_cols = ["vocab.t2.5", "lextale", "mean_fix_dur", "regression_rate", "accuracy"]
    sub = df.dropna(subset=cluster_cols).copy()

    # Definición de filas metodológicas
    rows = [
        [
            "vocab.t2.5",
            "Vocabulario Receptivo (Nation)",
            "Amplitud de Léxico L2",
            "Test Nation (40 ítems)",
            "Escala 0 - 40",
            f"{sub['vocab.t2.5'].mean():.1f} ± {sub['vocab.t2.5'].std():.1f}\n[Min: 3.0, Max: 40.0]",
            "Captura la disponibilidad de representaciones léxicas en memoria semántica."
        ],
        [
            "lextale",
            "Proficiencia Léxica (LexTALE)",
            "Acceso y Fluidez Léxica L2",
            "LexTALE Test",
            "Porcentaje (0 - 100%)",
            f"{sub['lextale'].mean():.1f}% ± {sub['lextale'].std():.1f}%\n[Min: 45.0%, Max: 100.0%]",
            "Mide la rapidez y precisión en la discriminación de palabras reales vs. pseudopalabras."
        ],
        [
            "mean_fix_dur",
            "Duración Media de Fijación",
            "Esfuerzo de Procesamiento Local",
            "Eye-Tracking (MECO L2)",
            "Milisegundos (ms)",
            f"{sub['mean_fix_dur'].mean():.1f} ± {sub['mean_fix_dur'].std():.1f} ms\n[Min: 144.9, Max: 453.8]",
            "Refleja el tiempo cognitivo requerido para decodificar e integrar cada palabra fijada."
        ],
        [
            "regression_rate",
            "Tasa de Regresiones Sacádicas",
            "Monitoreo y Relectura",
            "Eye-Tracking (MECO L2)",
            "Porcentaje (0 - 100%)",
            f"{sub['regression_rate'].mean()*100:.1f}% ± {sub['regression_rate'].std()*100:.1f}%\n[Min: 4.0%, Max: 34.0%]",
            "Identifica comportamientos de inspección regresiva para resolver rupturas de comprensión."
        ],
        [
            "accuracy",
            "Precisión de Comprensión",
            "Construcción del Modelo de Situación",
            "Cuestionario MECO L2",
            "Porcentaje (0 - 100%)",
            f"{sub['accuracy'].mean()*100:.1f}% ± {sub['accuracy'].std()*100:.1f}%\n[Min: 8.3%, Max: 100.0%]",
            "Mide el éxito final de comprensión global del texto en segunda lengua."
        ]
    ]

    headers = [
        "Variable (Código)",
        "Nombre Descriptivo",
        "Constructo Evaluado",
        "Instrumento / Fuente",
        "Rango / Unidad",
        "Media ± DE Global\n(N = 1,032)",
        "Justificación Teórica en el Modelo de Clustering"
    ]

    fig, ax = plt.subplots(figsize=(15.8, 5.8), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    ax.axis("off")

    col_widths = [0.12, 0.17, 0.16, 0.13, 0.10, 0.12, 0.20]

    table = ax.table(
        cellText=rows,
        colLabels=headers,
        colWidths=col_widths,
        loc="center",
        cellLoc="center"
    )

    table.auto_set_font_size(False)
    table.set_fontsize(8.6)
    table.scale(1.0, 2.3)

    # Estilo del encabezado
    header_color = "#1E293B"
    for j in range(len(headers)):
        cell = table[0, j]
        cell.set_facecolor(header_color)
        cell.set_text_props(color="#FFFFFF", fontweight="bold", fontsize=9.0)
        cell.set_edgecolor("#94A3B8")

    # Filas alternas y formato
    for i in range(1, len(rows) + 1):
        bg = "#F8FAFC" if i % 2 == 1 else "#FFFFFF"
        for j in range(len(headers)):
            cell = table[i, j]
            cell.set_facecolor(bg)
            cell.set_edgecolor("#CBD5E1")

            if j == 0:
                cell.set_text_props(fontweight="bold", fontfamily="monospace", color="#0F172A", fontsize=8.6)
            elif j in [1, 2]:
                cell.set_text_props(ha="left", color="#1E293B", fontweight="semibold" if j == 1 else "normal")
            elif j == 3:
                cell.set_text_props(color="#475569")
            elif j == 4:
                cell.set_text_props(color="#64748B", fontsize=8.2)
            elif j == 5:
                cell.set_text_props(fontweight="bold", color="#0F172A")
            elif j == 6:
                cell.set_text_props(ha="left", color="#334155", fontsize=8.0)

    plt.suptitle(
        "Variables de Entrada para la Construcción del Clustering de Lectores L2",
        fontsize=14.0, fontweight="bold", y=0.95, color="#0F172A"
    )
    plt.title(
        "Dimensiones utilizadas para la estandarización z-score y el particionamiento k-Means (N = 1,032 participantes)\nCada variable representa un pilar cognitivo: léxico previo, procesamiento ocular online o resultado de comprensión.",
        fontsize=9.2, color="#475569", pad=12
    )

    plt.tight_layout()
    out_path = PLOTS_DIR / "campos_clustering_input.png"
    plt.savefig(out_path, bbox_inches="tight", dpi=300)
    plt.close()

    shutil.copy(out_path, ARTIFACT_DIR / out_path.name)
    print(f"[success] Tabla guardada como imagen en {out_path} y copiada a {ARTIFACT_DIR / out_path.name}")


if __name__ == "__main__":
    render_input_features_table()
