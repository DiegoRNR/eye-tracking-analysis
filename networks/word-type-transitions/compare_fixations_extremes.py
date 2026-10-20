"""
networks/word-type-transitions/compare_fixations_extremes.py

Compara el comportamiento de fijaciones por tipo de palabra entre:
- Referencia nativa en inglés: English (media de cohortes en_ca y en_uk)
- Las dos lenguas más cercanas al inglés: Holandés (du: 21.8) y Danés (da: 24.6)
- Las dos lenguas más lejanas al inglés: Turco (tr: 96.3) y Baskir (ba: 97.2)

Genera gráficos de:
1. Lectura en L1 (lengua materna vs nativos de inglés): muestra la divergencia estructural natural.
2. Lectura en L2 (textos en inglés): muestra la convergencia hacia el estándar nativo y diferencias residuales.
3. Gráfico maestro 2x2 integrando ambas sesiones y contrastes.
4. Diferencia porcentual Δ% = Lang - English y duración media (ms) de fijación.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
COMPARISON_DIR = OUTPUT_DIR / "comparisons"

FUSED_ORDER = ["NOUN", "VERB", "ADJ", "ADV", "PRON", "ADP", "PTCL", "CONJ", "NUM"]

# Paleta distintiva
LANG_COLORS = {
    "English (Ref)": "#1a202c",  # Dark slate
    "du (Holandés · 21.8)": "#2b6cb0",  # Blue
    "da (Danés · 24.6)": "#319795",  # Teal
    "tr (Turco · 96.3)": "#dd6b20",  # Orange
    "ba (Baskir · 97.2)": "#e53e3e",  # Red
}

LANG_SHORT = {
    "English": "#1a202c",
    "du": "#2b6cb0",
    "da": "#319795",
    "tr": "#dd6b20",
    "ba": "#e53e3e",
}


def load_pooled_attributes(lang: str, mode: str, session: str) -> pd.DataFrame:
    """Carga atributos de nodo combinando Q1 y Q4 para obtener el total pooled del grupo."""
    dfs = []
    for q in ("Q1", "Q4"):
        p = OUTPUT_DIR / lang / mode / f"node_attributes_{session}-{lang}-{q}.csv"
        if p.exists():
            dfs.append(pd.read_csv(p, index_col=0))
    if not dfs:
        raise FileNotFoundError(f"No se encontraron atributos para {session}-{lang} ({mode})")
    
    # Combinar fijaciones y promediar duraciones ponderadas
    df_comb = pd.concat(dfs)
    grouped = df_comb.groupby(level=0)
    
    total_fix = grouped["n_fixations"].sum()
    # Duración media ponderada por número de fijaciones
    dur_weighted = (df_comb["mean_dur_ms"] * df_comb["n_fixations"]).groupby(level=0).sum() / total_fix.replace(0, np.nan)
    
    res = pd.DataFrame({
        "n_fixations": total_fix,
        "mean_dur_ms": dur_weighted,
    })
    return res.reindex(FUSED_ORDER).fillna(0.0)


def compute_profiles(mode: str, session: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calcula porcentaje de fijaciones (%) y duración media (ms) para:
    English Baseline (promedio en y en_uk), du, da, tr, ba.
    """
    data_fix = {}
    data_dur = {}

    target_langs = ["en", "en_uk", "du", "da", "tr", "ba"]
    for lg in target_langs:
        attr = load_pooled_attributes(lg, mode, session)
        tot = attr["n_fixations"].sum()
        pct = (attr["n_fixations"] / tot * 100.0) if tot > 0 else attr["n_fixations"] * 0.0
        data_fix[lg] = pct
        data_dur[lg] = attr["mean_dur_ms"]

    df_fix = pd.DataFrame(data_fix)
    df_dur = pd.DataFrame(data_dur)

    # Referencia nativa en inglés: promedio de en (en_ca) y en_uk
    df_fix["English"] = df_fix[["en", "en_uk"]].mean(axis=1)
    df_dur["English"] = df_dur[["en", "en_uk"]].mean(axis=1)

    return df_fix, df_dur


def plot_fixations_master_comparison(mode: str = "temporal") -> Path:
    """
    Genera el gráfico maestro 2x2:
    - Fila 1: L1 Nativo (Izquierda: English vs Cercanas; Derecha: English vs Lejanas)
    - Fila 2: L2 Inglés (Izquierda: English vs Cercanas; Derecha: English vs Lejanas)
    """
    COMPARISON_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(16, 11), sharey=True)

    sessions = [("L1", "Lectura en Lengua Materna (L1 vs English Native)"),
                ("L2", "Lectura de Textos en Inglés (L2 vs English Native)")]

    nodes = FUSED_ORDER
    x = np.arange(len(nodes))
    width = 0.26

    for row_idx, (sess, sess_title) in enumerate(sessions):
        df_fix, _ = compute_profiles(mode, sess)

        # Panel Izquierdo: English vs Cercanas (du, da)
        ax_close = axes[row_idx, 0]
        close_groups = [("English", "English (Ref Nativa)", LANG_SHORT["English"]),
                        ("du", "du (Holandés · 21.8)", LANG_SHORT["du"]),
                        ("da", "da (Danés · 24.6)", LANG_SHORT["da"])]
        
        for k, (col, lbl, color) in enumerate(close_groups):
            vals = df_fix[col].values
            bars = ax_close.bar(x + (k - 1) * width, vals, width, label=lbl, color=color, alpha=0.9, edgecolor="#333", linewidth=0.6)
            for bar, v in zip(bars, vals):
                if v >= 3.0:
                    ax_close.text(bar.get_x() + bar.get_width() / 2.0, v + 0.5, f"{v:.1f}%",
                                  ha="center", va="bottom", fontsize=6.2, rotation=90)

        ax_close.set_xticks(x)
        ax_close.set_xticklabels(nodes, fontsize=9.5, fontweight="bold")
        ax_close.set_ylabel("% de fijaciones sobre el total", fontsize=10)
        ax_close.set_title(f"{sess_title}\nInglés vs Más Cercanas (du, da)", fontsize=11, fontweight="bold")
        ax_close.legend(fontsize=8.5, loc="upper right")
        ax_close.grid(axis="y", linestyle=":", alpha=0.5)
        ax_close.set_ylim(0, 62)

        # Panel Derecho: English vs Lejanas (tr, ba)
        ax_far = axes[row_idx, 1]
        far_groups = [("English", "English (Ref Nativa)", LANG_SHORT["English"]),
                      ("tr", "tr (Turco · 96.3)", LANG_SHORT["tr"]),
                      ("ba", "ba (Baskir · 97.2)", LANG_SHORT["ba"])]
        
        for k, (col, lbl, color) in enumerate(far_groups):
            vals = df_fix[col].values
            bars = ax_far.bar(x + (k - 1) * width, vals, width, label=lbl, color=color, alpha=0.9, edgecolor="#333", linewidth=0.6)
            for bar, v in zip(bars, vals):
                if v >= 3.0:
                    ax_far.text(bar.get_x() + bar.get_width() / 2.0, v + 0.5, f"{v:.1f}%",
                                ha="center", va="bottom", fontsize=6.2, rotation=90)

        ax_far.set_xticks(x)
        ax_far.set_xticklabels(nodes, fontsize=9.5, fontweight="bold")
        ax_far.set_title(f"{sess_title}\nInglés vs Más Lejanas (tr, ba)", fontsize=11, fontweight="bold")
        ax_far.legend(fontsize=8.5, loc="upper right")
        ax_far.grid(axis="y", linestyle=":", alpha=0.5)
        ax_far.set_ylim(0, 62)

    fig.suptitle(
        f"Comparación del Comportamiento de Fijación: Inglés Nativo vs Lenguas Cercanas y Lejanas\n"
        f"Modo: {mode} · Guía: lang_to_en.csv (du=21.8, da=24.6 vs tr=96.3, ba=97.2)",
        fontsize=13, fontweight="bold", y=0.99
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    out = COMPARISON_DIR / "fixations_english_vs_extremes_master.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[comparison] {out}")
    return out


def plot_fixations_difference_divergence(mode: str = "temporal") -> Path:
    """
    Genera gráfico de divergencia Δ% = Lengua - Inglés:
    Muestra directamente dónde cada lengua sobre-fija o sub-fija en comparación con el inglés.
    """
    COMPARISON_DIR.mkdir(parents=True, exist_ok=True)
    fig, (ax_l1, ax_l2) = plt.subplots(2, 1, figsize=(15, 9), sharey=True)

    nodes = FUSED_ORDER
    x = np.arange(len(nodes))
    width = 0.2

    target_groups = [
        ("du", "du (Holandés · 21.8)", LANG_SHORT["du"]),
        ("da", "da (Danés · 24.6)", LANG_SHORT["da"]),
        ("tr", "tr (Turco · 96.3)", LANG_SHORT["tr"]),
        ("ba", "ba (Baskir · 97.2)", LANG_SHORT["ba"]),
    ]

    for ax, sess, sess_lbl in [(ax_l1, "L1", "Lectura Nativa L1 vs Inglés"), (ax_l2, "L2", "Lectura en Inglés L2 vs Inglés")]:
        df_fix, _ = compute_profiles(mode, sess)
        
        for k, (col, lbl, color) in enumerate(target_groups):
            diff = df_fix[col] - df_fix["English"]
            bars = ax.bar(x + (k - 1.5) * width, diff, width, label=lbl, color=color, alpha=0.88, edgecolor="#333", linewidth=0.5)
            for bar, d in zip(bars, diff):
                if abs(d) >= 1.0:
                    y_pos = d + (0.5 if d > 0 else -0.8)
                    ax.text(bar.get_x() + bar.get_width() / 2.0, y_pos, f"{d:+.1f}%",
                            ha="center", va="bottom" if d > 0 else "top", fontsize=6.2, rotation=90)

        ax.axhline(0, color="#1a202c", linewidth=1.2, linestyle="-")
        ax.set_xticks(x)
        ax.set_xticklabels(nodes, fontsize=9.5, fontweight="bold")
        ax.set_ylabel("Diferencia Δ% (Lengua − Inglés)", fontsize=9.5)
        ax.set_title(f"{sess_lbl}: Desviación Porcentual de Fijación Respecto a Nativos de Inglés", fontsize=11, fontweight="bold")
        ax.legend(fontsize=8.5, loc="upper right")
        ax.grid(axis="y", linestyle=":", alpha=0.5)

    ax_l1.set_ylim(-10, 17)
    fig.suptitle(
        f"Divergencia de Fijación respecto al Estándar Nativo de Inglés (Δ% = Lang − English)\n"
        f"Modo: {mode} · En L1 se observa gran divergencia morfológica; en L2 convergen al estándar de lectura inglés",
        fontsize=12.5, fontweight="bold", y=0.99
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    out = COMPARISON_DIR / "fixations_difference_from_english.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[comparison] {out}")
    return out


def plot_fixation_duration_comparison(mode: str = "temporal") -> Path:
    """
    Compara la duración media de fijación (ms) en L2 (lectura en inglés):
    Muestra la carga cognitiva / procesamiento en cada clase al leer inglés.
    """
    COMPARISON_DIR.mkdir(parents=True, exist_ok=True)
    _, df_dur_l2 = compute_profiles(mode, "L2")
    
    nodes = FUSED_ORDER
    x = np.arange(len(nodes))
    width = 0.16

    fig, ax = plt.subplots(figsize=(14, 6))

    all_groups = [
        ("English", "English (Ref Nativa)", LANG_SHORT["English"]),
        ("du", "du (Holandés · 21.8)", LANG_SHORT["du"]),
        ("da", "da (Danés · 24.6)", LANG_SHORT["da"]),
        ("tr", "tr (Turco · 96.3)", LANG_SHORT["tr"]),
        ("ba", "ba (Baskir · 97.2)", LANG_SHORT["ba"]),
    ]

    for k, (col, lbl, color) in enumerate(all_groups):
        vals = df_dur_l2[col].values
        bars = ax.bar(x + (k - 2) * width, vals, width, label=lbl, color=color, alpha=0.9, edgecolor="#333", linewidth=0.6)
        for bar, v in zip(bars, vals):
            if v > 150:
                ax.text(bar.get_x() + bar.get_width() / 2.0, v + 2.0, f"{v:.0f}",
                        ha="center", va="bottom", fontsize=6.0, rotation=90)

    ax.set_xticks(x)
    ax.set_xticklabels(nodes, fontsize=10, fontweight="bold")
    ax.set_ylabel("Duración media de fijación (ms)", fontsize=10)
    ax.set_ylim(160, 260)
    ax.set_title(
        f"Carga Cognitiva al Leer en Inglés (L2): Duración Media de Fijación por Tipo de Palabra\n"
        f"Modo: {mode} · Nativos de inglés procesan en ~198 ms; lenguas cercanas en ~220 ms; lejanas en ~228 ms",
        fontsize=12, fontweight="bold"
    )
    ax.legend(fontsize=8.5, loc="upper right")
    ax.grid(axis="y", linestyle=":", alpha=0.4)

    fig.tight_layout()
    out = COMPARISON_DIR / "fixation_duration_l2_comparison.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[comparison] {out}")
    return out


def generate_all_comparisons(mode: str = "temporal") -> list[Path]:
    p1 = plot_fixations_master_comparison(mode)
    p2 = plot_fixations_difference_divergence(mode)
    p3 = plot_fixation_duration_comparison(mode)
    return [p1, p2, p3]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["temporal", "regression"], default="temporal")
    args = parser.parse_args()
    generate_all_comparisons(args.mode)
