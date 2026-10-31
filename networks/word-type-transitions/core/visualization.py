"""
networks/word-type-transitions/core/visualization.py

Suite de figuras PER LENGUA PER MODO (matplotlib, publicación). Todas las
figuras se guardan en output/<lang>/<mode>/figures/:

1. `accuracy_box.png` — box plot de accuracy por celda del 2×2
   (L1-Q1, L1-Q4, L2-Q1, L2-Q4) con puntos por sujeto (jitter).
2. `transitions_bar.png` — top-N transiciones clase→clase por CONTEOS pooled
   (n de transiciones), un panel por condición {L1,L2}×{Q1,Q4}.
3. `fixations_bar.png` — n de fijaciones por clase de palabra, 4 series
   (una por condición) agrupadas por nodo.
4. `heatmap_bestworst.png` — matrices DIFERENCIA Q4−Q1 para L1 y L2
   (divergente, escala compartida): mejores vs peores dentro de la misma sesión.
5. `heatmap_l1vl2.png` — matrices DIFERENCIA L1−L2 dentro de Q4 y dentro de Q1
   (divergente, escala compartida): nativo vs inglés en el mismo cuartil.
6. `network.png` — grafo dirigido clase→clase en layout circular FIJO
   (orden FUSED, comparable entre paneles): ancho/alpha de arista = P(v|u),
   tamaño de nodo = dwell share, color de nodo = duración media (viridis
   compartido), auto-bucles curvos.

Las comparaciones L1vL2 (figs 1, 5) usan textos distintos por diseño MECO.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import Normalize
from matplotlib.patches import FancyArrowPatch

from .label_map import FUSED_ORDER
from .paths import (
    CH_VARIANTS,
    CONDITION_LANGS,
    LANGS_W1,
    figures_dir,
    lang_dir,
    mode_dir,
)
from .persistence import load_condition_summary

# Paleta
C_Q1 = "#d95f02"  # peor comprensión
C_Q4 = "#1b9e77"  # mejor comprensión
C_L1 = "#377eb8"  # nativo
C_L2 = "#e41a1c"  # inglés (L2)

NODE_PALETTE = {
    "NOUN": "#377eb8",
    "VERB": "#e41a1c",
    "ADJ": "#4daf4a",
    "ADV": "#984ea3",
    "PRON": "#ff7f00",
    "ADP": "#a65628",
    "PTCL": "#f781bf",
    "CONJ": "#999999",
    "NUM": "#ffd92f",
    "X": "#8dd3c7",
    "PUNCT": "#b3b3b3",
}

QUARTILE_COLORS = {"Q1": C_Q1, "Q4": C_Q4}
SESSION_COLORS = {"L1": C_L1, "L2": C_L2}
CMAP_DUR = plt.get_cmap("viridis")

LANG_NAMES = {
    "du": "Neerlandés",
    "ee": "Estonio",
    "en": "Inglés",
    "fi": "Finés",
    "ge": "Alemán",
    "gr": "Griego",
    "he": "Hebreo",
    "it": "Italiano",
    "no": "Noruego",
    "ru": "Ruso",
    "sp": "Español",
    "tr": "Turco",
    "ch_s": "Chino Simplificado",
    "ch_t": "Chino Tradicional",
    "ba": "Vasco",
    "bp": "Portugués (Brasil)",
    "da": "Danés",
    "en_uk": "Inglés UK",
    "ge_po": "Alemán (Potsdam)",
    "ge_zu": "Alemán (Zúrich)",
    "hi_iiith": "Hindi (IIITH)",
    "hi_iitk": "Hindi (IITK)",
    "ic": "Islandés",
    "ru_mo": "Ruso (w2)",
    "se": "Serbio",
    "sp_ch": "Español (Chile)",
    "no_w2": "Noruego (w2)",
    "tr_w2": "Turco (w2)",
}

CONTRASTS = [
    ("Q4vQ1_L1", "Q4", "Q1", "L1"),
    ("Q4vQ1_L2", "Q4", "Q1", "L2"),
    ("L1vL2_Q4", "L1", "L2", "Q4"),
    ("L1vL2_Q1", "L1", "L2", "Q1"),
]
CONTRAST_TITLES = {
    "Q4vQ1_L1": "Q4 − Q1 · L1 nativo",
    "Q4vQ1_L2": "Q4 − Q1 · L2 inglés",
    "L1vL2_Q4": "L1 − L2 · mejores (Q4)",
    "L1vL2_Q1": "L1 − L2 · peores (Q1)",
}

CELLS = [("L1", "Q1"), ("L1", "Q4"), ("L2", "Q1"), ("L2", "Q4")]


def _cond(session: str, lang: str, quartile: str) -> str:
    return f"{session}-{lang}-{quartile}"


def _load_matrix(lang: str, mode: str, session: str, quartile: str) -> Optional[pd.DataFrame]:
    p = mode_dir(lang, mode) / f"matrix_{_cond(session, lang, quartile)}.csv"
    if not p.exists():
        return None
    return pd.read_csv(p, index_col=0)


def _load_node_attrs(lang: str, mode: str, session: str, quartile: str) -> Optional[pd.DataFrame]:
    p = mode_dir(lang, mode) / f"node_attributes_{_cond(session, lang, quartile)}.csv"
    if not p.exists():
        return None
    return pd.read_csv(p, index_col=0)


def _load_counts(lang: str, mode: str, session: str, quartile: str) -> Optional[pd.DataFrame]:
    p = mode_dir(lang, mode) / f"counts_{_cond(session, lang, quartile)}.csv"
    if not p.exists():
        return None
    return pd.read_csv(p, index_col=0)


def _load_comparison(lang: str, mode: str, contrast: str) -> Optional[pd.DataFrame]:
    p = mode_dir(lang, mode) / f"comparison_{contrast}.csv"
    if not p.exists():
        return None
    return pd.read_csv(p)


def _fpath(lang: str, mode: str, name: str):
    return figures_dir(lang, mode) / name


# ---------------------------------------------------------------------------
# 1. Box plot de accuracy por celda
# ---------------------------------------------------------------------------

def plot_accuracy_box(lang: str) -> Optional[Path]:
    """Box plot: accuracy por celda {L1,L2}×{Q1,Q4} con puntos por sujeto."""
    p = lang_dir(lang) / "accuracy_subjects.csv"
    if not p.exists():
        return None
    df = pd.read_csv(p)
    if df.empty:
        return None

    fig, ax = plt.subplots(figsize=(8.2, 5.0))
    cells = [("L1", "Q1"), ("L1", "Q4"), ("L2", "Q1"), ("L2", "Q4")]
    data, positions, colors = [], [], []
    for i, (session, q) in enumerate(cells):
        vals = df[(df["session"] == session) & (df["quartile"] == q)]["accuracy"].values
        data.append(vals)
        positions.append(i)
        colors.append(SESSION_COLORS[session])
        if len(vals):
            jitter = np.random.default_rng(i).uniform(-0.12, 0.12, len(vals))
            ax.scatter(i + jitter, vals, s=16, color=QUARTILE_COLORS[q], alpha=0.75,
                       edgecolors="none", zorder=3)
    bp = ax.boxplot(
        data,
        positions=positions,
        widths=0.5,
        patch_artist=True,
        showfliers=False,
        medianprops=dict(color="#222222", lw=1.4),
        whiskerprops=dict(color="#444444"),
        capprops=dict(color="#444444"),
    )
    for patch, c in zip(bp["boxes"], colors):
        patch.set_facecolor(c)
        patch.set_alpha(0.35)
        patch.set_edgecolor(c)

    labels = []
    for session, q in cells:
        n = len(df[(df["session"] == session) & (df["quartile"] == q)])
        labels.append(f"{session}-{'peor' if q == 'Q1' else 'mejor'}\n(n={n})")
    ax.set_xticks(positions, labels, fontsize=9)
    ax.set_ylabel("Accuracy de comprensión")
    ax.set_title(f"Accuracy por celda del 2×2 — {LANG_NAMES.get(lang, lang)}", fontsize=12)
    ax.grid(axis="y", alpha=0.25)
    handles = [
        plt.Rectangle((0, 0), 1, 1, facecolor=C_L1, alpha=0.4, label="L1 nativo"),
        plt.Rectangle((0, 0), 1, 1, facecolor=C_L2, alpha=0.4, label="L2 inglés"),
        plt.Line2D([], [], marker="o", ls="", color=C_Q1, label="Q1 (peor)"),
        plt.Line2D([], [], marker="o", ls="", color=C_Q4, label="Q4 (mejor)"),
    ]
    ax.legend(handles=handles, fontsize=8, loc="lower right")
    fig.tight_layout()
    out = _fpath(lang, "temporal", "accuracy_box.png")
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# 2. Barras de transiciones (conteos pooled) por condición
# ---------------------------------------------------------------------------

def plot_transitions_bar(lang: str, mode: str, top_k: int = 15) -> Optional[Path]:
    """Top-K transiciones clase→clase por conteo pooled, panel por condición."""
    counts = {}
    for session, q in CELLS:
        c = _load_counts(lang, mode, session, q)
        if c is None:
            return None
        counts[(session, q)] = c

    vmax = max(float(c.values.max()) for c in counts.values()) or 1.0
    fig, axes = plt.subplots(2, 2, figsize=(13, 10))
    for (session, q), ax in zip(CELLS, axes.flat):
        c = counts[(session, q)]
        edges = []
        for u in c.index:
            for v in c.columns:
                n = float(c.loc[u, v])
                if n > 0:
                    edges.append((f"{u}→{v}", n, u, u == v))
        if not edges:
            ax.axis("off")
            ax.set_title(f"{session} · {'peor' if q == 'Q1' else 'mejor'}", fontsize=10)
            continue
        edges.sort(key=lambda t: -t[1])
        edges = edges[:top_k][::-1]
        y = np.arange(len(edges))
        bar_colors = [NODE_PALETTE.get(u, "#888888") for _, _, u, _ in edges]
        ax.barh(y, [n for _, n, _, _ in edges], color=bar_colors, alpha=0.85)
        for i, (_, n, _, loop) in enumerate(edges):
            ax.text(n + vmax * 0.01, i, f"{n:,.0f}", va="center", fontsize=6.5)
        ax.set_yticks(y, [e for e, _, _, _ in edges], fontsize=7)
        ax.set_xlim(0, vmax * 1.12)
        ax.set_title(f"{session} · {'peor' if q == 'Q1' else 'mejor'}", fontsize=10)
        ax.grid(axis="x", alpha=0.2)
    fig.suptitle(
        f"Top-{top_k} transiciones entre clases (conteos pooled) — "
        f"{LANG_NAMES.get(lang, lang)} · modo {mode}",
        fontsize=12,
    )
    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=NODE_PALETTE[n], label=n) for n in FUSED_ORDER]
    fig.legend(handles=handles, loc="lower center", ncol=11, fontsize=7, title="clase origen")
    fig.tight_layout(rect=(0, 0.06, 1, 0.95))
    out = _fpath(lang, mode, "transitions_bar.png")
    fig.savefig(out, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_transitions_normalized_bar(lang: str, mode: str, top_k: int = 15) -> Optional[Path]:
    """Top-K transiciones clase→clase por probabilidad condicional P(destino | origen) (%), panel por condición."""
    matrices = {}
    for session, q in CELLS:
        m = _load_matrix(lang, mode, session, q)
        if m is None:
            return None
        matrices[(session, q)] = m

    fig, axes = plt.subplots(2, 2, figsize=(13, 10))
    for (session, q), ax in zip(CELLS, axes.flat):
        m = matrices[(session, q)]
        edges = []
        for u in m.index:
            for v in m.columns:
                pct = float(m.loc[u, v]) * 100.0
                if pct > 0:
                    edges.append((f"{u}→{v}", pct, u, u == v))
        if not edges:
            ax.axis("off")
            ax.set_title(f"{session} · {'peor' if q == 'Q1' else 'mejor'}", fontsize=10)
            continue
        edges.sort(key=lambda t: -t[1])
        edges = edges[:top_k][::-1]
        y = np.arange(len(edges))
        bar_colors = [NODE_PALETTE.get(u, "#888888") for _, _, u, _ in edges]
        ax.barh(y, [pct for _, pct, _, _ in edges], color=bar_colors, alpha=0.85)
        max_pct = max(e[1] for e in edges)
        for i, (_, pct, _, loop) in enumerate(edges):
            ax.text(pct + max_pct * 0.015, i, f"{pct:.1f}%", va="center", fontsize=6.8)
        ax.set_yticks(y, [e for e, _, _, _ in edges], fontsize=7)
        ax.set_xlim(0, max_pct * 1.15)
        ax.set_xlabel("P(destino | origen) % de salidas de la clase", fontsize=8.5)
        ax.set_title(f"{session} · {'peor' if q == 'Q1' else 'mejor'}", fontsize=10)
        ax.grid(axis="x", alpha=0.2)
    fig.suptitle(
        f"Top-{top_k} transiciones normalizadas por clase de origen P(destino | origen) — "
        f"{LANG_NAMES.get(lang, lang)} · modo {mode}\n(Controla el sesgo por frecuencia de palabras para comparar clases de forma justa)",
        fontsize=11.5,
    )
    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=NODE_PALETTE[n], label=n) for n in FUSED_ORDER]
    fig.legend(handles=handles, loc="lower center", ncol=11, fontsize=7, title="clase origen")
    fig.tight_layout(rect=(0, 0.06, 1, 0.94))
    out = _fpath(lang, mode, "transitions_normalized_bar.png")
    fig.savefig(out, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_transitions_comparison(lang: str, mode: str, top_k: int = 10) -> Optional[Path]:
    """Comparación directa lado a lado: Conteo Absoluto vs Porcentaje Normalizado P(v|u) por condición."""
    counts = {}
    matrices = {}
    for session, q in CELLS:
        c = _load_counts(lang, mode, session, q)
        m = _load_matrix(lang, mode, session, q)
        if c is None or m is None:
            return None
        counts[(session, q)] = c
        matrices[(session, q)] = m

    fig, axes = plt.subplots(4, 2, figsize=(14, 15))
    for i, (session, q) in enumerate(CELLS):
        ax_cnt = axes[i, 0]
        ax_pct = axes[i, 1]
        c = counts[(session, q)]
        m = matrices[(session, q)]

        # Conteo
        edges_c = []
        for u in c.index:
            for v in c.columns:
                n = float(c.loc[u, v])
                if n > 0:
                    edges_c.append((f"{u}→{v}", n, u))
        edges_c.sort(key=lambda t: -t[1])
        edges_c = edges_c[:top_k][::-1]
        y_c = np.arange(len(edges_c))
        ax_cnt.barh(y_c, [n for _, n, _ in edges_c], color=[NODE_PALETTE.get(u, "#888") for _, _, u in edges_c], alpha=0.85)
        for idx, (_, n, _) in enumerate(edges_c):
            ax_cnt.text(n + edges_c[-1][1] * 0.02, idx, f"{n:,.0f}", va="center", fontsize=6.5)
        ax_cnt.set_yticks(y_c, [e for e, _, _ in edges_c], fontsize=7)
        ax_cnt.set_title(f"{session} {'peor (Q1)' if q == 'Q1' else 'mejor (Q4)'} · Conteos Absolutos (n)", fontsize=9.5, fontweight="bold")
        ax_cnt.grid(axis="x", alpha=0.2)

        # Normalizado
        edges_p = []
        for u in m.index:
            for v in m.columns:
                p = float(m.loc[u, v]) * 100.0
                if p > 0:
                    edges_p.append((f"{u}→{v}", p, u))
        edges_p.sort(key=lambda t: -t[1])
        edges_p = edges_p[:top_k][::-1]
        y_p = np.arange(len(edges_p))
        ax_pct.barh(y_p, [p for _, p, _ in edges_p], color=[NODE_PALETTE.get(u, "#888") for _, _, u in edges_p], alpha=0.85)
        for idx, (_, p, _) in enumerate(edges_p):
            ax_pct.text(p + edges_p[-1][1] * 0.02, idx, f"{p:.1f}%", va="center", fontsize=6.5)
        ax_pct.set_yticks(y_p, [e for e, _, _ in edges_p], fontsize=7)
        ax_pct.set_title(f"{session} {'peor (Q1)' if q == 'Q1' else 'mejor (Q4)'} · Tasa Normalizada P(destino|origen) %", fontsize=9.5, fontweight="bold")
        ax_pct.grid(axis="x", alpha=0.2)

    fig.suptitle(
        f"Distribución de enlaces entre tipos de palabra: Conteo Absoluto vs Tasa Normalizada — {LANG_NAMES.get(lang, lang)} ({mode})\n"
        f"(El panel izquierdo refleja el volumen dominado por clases frecuentes; el derecho mide la probabilidad de transición relativa)",
        fontsize=11.5,
    )
    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=NODE_PALETTE[n], label=n) for n in FUSED_ORDER]
    fig.legend(handles=handles, loc="lower center", ncol=11, fontsize=7, title="clase origen")
    fig.tight_layout(rect=(0, 0.04, 1, 0.96))
    out = _fpath(lang, mode, "transitions_comparison.png")
    fig.savefig(out, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# 3. Barras de fijaciones por clase
# ---------------------------------------------------------------------------

def plot_fixations_bar(lang: str, mode: str) -> Optional[Path]:
    """n de fijaciones por clase: 4 series (una por condición del 2×2)."""
    attrs = {}
    for session, q in CELLS:
        a = _load_node_attrs(lang, mode, session, q)
        if a is None:
            return None
        attrs[(session, q)] = a

    nodes = [n for n in FUSED_ORDER if any(n in a.index for a in attrs.values())]
    if not nodes:
        return None
    x = np.arange(len(nodes))
    width = 0.2

    fig, ax = plt.subplots(figsize=(11, 5))
    for k, (session, q) in enumerate(CELLS):
        a = attrs[(session, q)]
        vals = [float(a.loc[n, "n_fixations"]) if n in a.index else 0.0 for n in nodes]
        ax.bar(x + (k - 1.5) * width, vals, width, label=f"{session}-{'peor' if q == 'Q1' else 'mejor'}",
               color=SESSION_COLORS[session], alpha=0.55 if q == "Q1" else 0.95,
               edgecolor=QUARTILE_COLORS[q], linewidth=0.8 if q == "Q1" else 0.0)
    ax.set_xticks(x, nodes, fontsize=9)
    ax.set_ylabel("n de fijaciones (pooled)")
    ax.set_title(f"Fijaciones por clase de palabra — {LANG_NAMES.get(lang, lang)} · modo {mode}", fontsize=12)
    ax.grid(axis="y", alpha=0.25)
    handles = [
        plt.Rectangle((0, 0), 1, 1, facecolor=C_L1, alpha=0.55, edgecolor=C_Q1, label="L1 · peor (Q1)"),
        plt.Rectangle((0, 0), 1, 1, facecolor=C_L1, alpha=0.95, edgecolor=C_Q4, label="L1 · mejor (Q4)"),
        plt.Rectangle((0, 0), 1, 1, facecolor=C_L2, alpha=0.55, edgecolor=C_Q1, label="L2 · peor (Q1)"),
        plt.Rectangle((0, 0), 1, 1, facecolor=C_L2, alpha=0.95, edgecolor=C_Q4, label="L2 · mejor (Q4)"),
    ]
    ax.legend(handles=handles, fontsize=8, ncol=2)
    fig.tight_layout()
    out = _fpath(lang, mode, "fixations_bar.png")
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def plot_fixations_normalized_bar(lang: str, mode: str) -> Optional[Path]:
    """Porcentaje de fijaciones por clase sobre el total de la condición: 4 series (2×2)."""
    attrs = {}
    for session, q in CELLS:
        a = _load_node_attrs(lang, mode, session, q)
        if a is None:
            return None
        attrs[(session, q)] = a

    nodes = [n for n in FUSED_ORDER if any(n in a.index for a in attrs.values())]
    if not nodes:
        return None
    x = np.arange(len(nodes))
    width = 0.2

    fig, ax = plt.subplots(figsize=(11, 5.5))
    max_pct = 0.0
    for k, (session, q) in enumerate(CELLS):
        a = attrs[(session, q)]
        total_fix = float(a["n_fixations"].sum()) if "n_fixations" in a.columns else 0.0
        vals = [
            (float(a.loc[n, "n_fixations"]) / total_fix * 100.0) if (n in a.index and total_fix > 0) else 0.0
            for n in nodes
        ]
        if vals:
            max_pct = max(max_pct, max(vals))
        bars = ax.bar(
            x + (k - 1.5) * width, vals, width, label=f"{session}-{'peor' if q == 'Q1' else 'mejor'}",
            color=SESSION_COLORS[session], alpha=0.55 if q == "Q1" else 0.95,
            edgecolor=QUARTILE_COLORS[q], linewidth=0.8 if q == "Q1" else 0.0,
        )
        for bar, v in zip(bars, vals):
            if v >= 2.0:
                ax.text(bar.get_x() + bar.get_width() / 2.0, v + 0.5, f"{v:.1f}%",
                        ha="center", va="bottom", fontsize=5.8, rotation=90)

    ax.set_xticks(x, nodes, fontsize=9)
    ax.set_ylabel("% de fijaciones (sobre el total de la condición)", fontsize=9.5)
    ax.set_ylim(0, max_pct * 1.18 if max_pct > 0 else 100.0)
    ax.set_title(
        f"Distribución porcentual de fijaciones por clase de palabra — {LANG_NAMES.get(lang, lang)} · modo {mode}\n"
        f"(Normalizado: las barras de cada condición suman 100% para comparar de forma justa)",
        fontsize=11.5,
    )
    ax.grid(axis="y", alpha=0.25)
    handles = [
        plt.Rectangle((0, 0), 1, 1, facecolor=C_L1, alpha=0.55, edgecolor=C_Q1, label="L1 · peor (Q1)"),
        plt.Rectangle((0, 0), 1, 1, facecolor=C_L1, alpha=0.95, edgecolor=C_Q4, label="L1 · mejor (Q4)"),
        plt.Rectangle((0, 0), 1, 1, facecolor=C_L2, alpha=0.55, edgecolor=C_Q1, label="L2 · peor (Q1)"),
        plt.Rectangle((0, 0), 1, 1, facecolor=C_L2, alpha=0.95, edgecolor=C_Q4, label="L2 · mejor (Q4)"),
    ]
    ax.legend(handles=handles, fontsize=8, ncol=2)
    fig.tight_layout()
    out = _fpath(lang, mode, "fixations_normalized_bar.png")
    fig.savefig(out, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_fixations_comparison(lang: str, mode: str) -> Optional[Path]:
    """Comparación vertical directa: Conteos Absolutos (arriba) vs Porcentaje Normalizado (abajo)."""
    attrs = {}
    for session, q in CELLS:
        a = _load_node_attrs(lang, mode, session, q)
        if a is None:
            return None
        attrs[(session, q)] = a

    nodes = [n for n in FUSED_ORDER if any(n in a.index for a in attrs.values())]
    if not nodes:
        return None
    x = np.arange(len(nodes))
    width = 0.2

    fig, (ax_cnt, ax_pct) = plt.subplots(2, 1, figsize=(12, 9), sharex=True)

    # 1. Conteos absolutos
    for k, (session, q) in enumerate(CELLS):
        a = attrs[(session, q)]
        vals = [float(a.loc[n, "n_fixations"]) if n in a.index else 0.0 for n in nodes]
        ax_cnt.bar(
            x + (k - 1.5) * width, vals, width,
            color=SESSION_COLORS[session], alpha=0.55 if q == "Q1" else 0.95,
            edgecolor=QUARTILE_COLORS[q], linewidth=0.8 if q == "Q1" else 0.0,
        )
    ax_cnt.set_ylabel("n de fijaciones (pooled)", fontsize=9.5)
    ax_cnt.set_title("Conteos Absolutos (n fijaciones por clase)", fontsize=10.5, fontweight="bold")
    ax_cnt.grid(axis="y", alpha=0.25)

    # 2. Porcentajes normalizados
    max_p = 0.0
    for k, (session, q) in enumerate(CELLS):
        a = attrs[(session, q)]
        total_fix = float(a["n_fixations"].sum()) if "n_fixations" in a.columns else 0.0
        vals = [
            (float(a.loc[n, "n_fixations"]) / total_fix * 100.0) if (n in a.index and total_fix > 0) else 0.0
            for n in nodes
        ]
        if vals:
            max_p = max(max_p, max(vals))
        bars = ax_pct.bar(
            x + (k - 1.5) * width, vals, width,
            color=SESSION_COLORS[session], alpha=0.55 if q == "Q1" else 0.95,
            edgecolor=QUARTILE_COLORS[q], linewidth=0.8 if q == "Q1" else 0.0,
        )
        for bar, v in zip(bars, vals):
            if v >= 2.0:
                ax_pct.text(bar.get_x() + bar.get_width() / 2.0, v + 0.4, f"{v:.1f}%",
                            ha="center", va="bottom", fontsize=5.8, rotation=90)

    ax_pct.set_xticks(x, nodes, fontsize=9)
    ax_pct.set_ylabel("% de fijaciones (suma = 100%)", fontsize=9.5)
    ax_pct.set_ylim(0, max_p * 1.18 if max_p > 0 else 100.0)
    ax_pct.set_title("Tasa Normalizada (% sobre el total de fijaciones de cada condición)", fontsize=10.5, fontweight="bold")
    ax_pct.grid(axis="y", alpha=0.25)

    handles = [
        plt.Rectangle((0, 0), 1, 1, facecolor=C_L1, alpha=0.55, edgecolor=C_Q1, label="L1 · peor (Q1)"),
        plt.Rectangle((0, 0), 1, 1, facecolor=C_L1, alpha=0.95, edgecolor=C_Q4, label="L1 · mejor (Q4)"),
        plt.Rectangle((0, 0), 1, 1, facecolor=C_L2, alpha=0.55, edgecolor=C_Q1, label="L2 · peor (Q1)"),
        plt.Rectangle((0, 0), 1, 1, facecolor=C_L2, alpha=0.95, edgecolor=C_Q4, label="L2 · mejor (Q4)"),
    ]
    fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.98, 0.98), fontsize=8, ncol=2)

    fig.suptitle(
        f"Fijaciones por clase de palabra: Conteo Absoluto vs Porcentaje Normalizado — {LANG_NAMES.get(lang, lang)} · modo {mode}",
        fontsize=12, fontweight="bold", y=0.99
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    out = _fpath(lang, mode, "fixations_comparison.png")
    fig.savefig(out, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# 4/5. Heatmaps de DIFERENCIA (divergentes, escala compartida)
# ---------------------------------------------------------------------------

def _union_index(lang: str, mode: str) -> List[str]:
    mats = []
    for session in ("L1", "L2"):
        for q in ("Q1", "Q4"):
            m = _load_matrix(lang, mode, session, q)
            if m is not None:
                mats.append(m)
    nodes = [n for n in FUSED_ORDER if any(n in m.index for m in mats)]
    return nodes or FUSED_ORDER


def _diff_panel(ax, diff: pd.DataFrame, nodes: List[str], vmin: float, vmax: float, title: str):
    diff_norm = Normalize(vmin=vmin, vmax=vmax)
    im = ax.imshow(diff.values, cmap="RdBu_r", norm=diff_norm)
    ax.set_xticks(range(len(nodes)), nodes, rotation=45, ha="right", fontsize=7.5)
    ax.set_yticks(range(len(nodes)), nodes, fontsize=7.5)
    # rejilla sutil entre celdas
    for k in range(len(nodes) + 1):
        ax.axhline(k - 0.5, color="#dddddd", lw=0.4, zorder=3)
        ax.axvline(k - 0.5, color="#dddddd", lw=0.4, zorder=3)
    ax.set_title(title, fontsize=10)
    return im


def plot_diff_heatmaps(lang: str, mode: str) -> Tuple[Optional[Path], Optional[Path]]:
    """
    Dos figuras divergentes de diferencias:
    - bestworst: Q4−Q1 panel L1 + panel L2 (mejores vs peores, misma sesión)
    - l1vl2: L1−L2 panel Q4 + panel Q1 (nativo vs inglés, mismo cuartil)
    """
    mats = {}
    for session, q in CELLS:
        m = _load_matrix(lang, mode, session, q)
        if m is None:
            return (None, None)
        mats[(session, q)] = m

    out_best = out_l1l2 = None

    # --- best vs worst -----------------------------------------------------
    nodes_bw = _union_index(lang, mode)
    d1 = (mats[("L1", "Q4")].reindex(index=nodes_bw, columns=nodes_bw)
          - mats[("L1", "Q1")].reindex(index=nodes_bw, columns=nodes_bw)).fillna(0.0)
    d2 = (mats[("L2", "Q4")].reindex(index=nodes_bw, columns=nodes_bw)
          - mats[("L2", "Q1")].reindex(index=nodes_bw, columns=nodes_bw)).fillna(0.0)
    lim = max(abs(d1.values).max(), abs(d2.values).max()) or 0.1
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.8))
    for ax, d, session in ((axes[0], d1, "L1"), (axes[1], d2, "L2")):
        im = _diff_panel(
            ax, d, nodes_bw, -lim, lim,
            f"{'Nativo (L1)' if session == 'L1' else 'Inglés (L2)'}: Q4 (mejor) − Q1 (peor)",
        )
    cbar = fig.colorbar(im, ax=axes, fraction=0.03, pad=0.02)
    cbar.set_label("Δ P(transición | origen): positivo = mayor en mejores (Q4)")
    fig.suptitle(
        f"Mejores vs peores lectores (Q4−Q1) — {LANG_NAMES.get(lang, lang)} · modo {mode}",
        fontsize=12,
    )
    out_best = _fpath(lang, mode, "heatmap_bestworst.png")
    fig.savefig(out_best, dpi=160, bbox_inches="tight")
    plt.close(fig)

    # --- L1 vs L2 ----------------------------------------------------------
    nodes_ll = _union_index(lang, mode)
    d3 = (mats[("L1", "Q4")].reindex(index=nodes_ll, columns=nodes_ll)
          - mats[("L2", "Q4")].reindex(index=nodes_ll, columns=nodes_ll)).fillna(0.0)
    d4 = (mats[("L1", "Q1")].reindex(index=nodes_ll, columns=nodes_ll)
          - mats[("L2", "Q1")].reindex(index=nodes_ll, columns=nodes_ll)).fillna(0.0)
    lim2 = max(abs(d3.values).max(), abs(d4.values).max()) or 0.1
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.8))
    for ax, (q, title) in zip(
        axes,
        [("Q4", "Mejores lectores (Q4): L1 nativo − L2 inglés"), ("Q1", "Peores lectores (Q1): L1 nativo − L2 inglés")],
    ):
        im = _diff_panel(ax, d3 if q == "Q4" else d4, nodes_ll, -lim2, lim2, title)
    cbar = fig.colorbar(im, ax=axes, fraction=0.03, pad=0.02)
    cbar.set_label("Δ P(transición | origen): positivo = mayor en L1 nativo")
    fig.suptitle(
        f"Nativo vs inglés en el mismo cuartil (L1−L2) — {LANG_NAMES.get(lang, lang)} · modo {mode}",
        fontsize=12,
    )
    out_l1l2 = _fpath(lang, mode, "heatmap_l1vl2.png")
    fig.savefig(out_l1l2, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return out_best, out_l1l2


# ---------------------------------------------------------------------------
# 6. Grafo de red (layout circular fijo)
# ---------------------------------------------------------------------------

def _node_xy(order: List[str]) -> Dict[str, Tuple[float, float]]:
    """Posiciones en círculo (mismo orden en todos los paneles)."""
    n = len(order)
    return {
        node: (0.5 + 0.42 * np.cos(2 * np.pi * i / n - np.pi / 2),
               0.5 + 0.42 * np.sin(2 * np.pi * i / n - np.pi / 2))
        for i, node in enumerate(order)
    }


def _draw_network_panel(ax, matrix: pd.DataFrame, attrs: pd.DataFrame, nodes: List[str],
                        pos: Dict[str, Tuple[float, float]], dur_norm, title: str,
                        dwell_max: Optional[float] = None):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    dwell = {n: float(attrs.loc[n, "dwell_share"]) for n in nodes if n in attrs.index}
    mdur = {n: float(attrs.loc[n, "mean_dur_ms"]) for n in nodes if n in attrs.index}
    dw_max = dwell_max if dwell_max else max(dwell.values(), default=1.0) or 1.0

    edges = []
    for u in nodes:
        for v in nodes:
            w = float(matrix.loc[u, v]) if (u in matrix.index and v in matrix.columns) else 0.0
            if w > 0:
                edges.append((u, v, w))
    wmax = max((w for _, _, w in edges), default=1.0) or 1.0

    for u, v, w in edges:
        if u == v:
            continue
        frac = w / wmax
        arr = FancyArrowPatch(
            pos[u], pos[v],
            connectionstyle="arc3,rad=0.18",
            arrowstyle="-|>",
            mutation_scale=6 + 14 * frac,
            linewidth=0.6 + 4.2 * frac,
            color=NODE_PALETTE.get(u, "#888888"),
            alpha=0.15 + 0.7 * frac,
            shrinkA=18, shrinkB=16,
            zorder=1,
        )
        ax.add_patch(arr)

    # auto-bucles: arco pequeño que sale y vuelve al propio nodo
    for u in nodes:
        ws = float(matrix.loc[u, u]) if u in matrix.index else 0.0
        if ws <= 0:
            continue
        frac = min(ws / wmax, 1.0)
        x, y = pos[u]
        dx, dy = x - 0.5, y - 0.5
        L = (dx**2 + dy**2) ** 0.5 or 1.0
        ux, uy = dx / L, dy / L
        arr = FancyArrowPatch(
            (x + ux * 0.045 - uy * 0.030, y + uy * 0.045 + ux * 0.030),
            (x + ux * 0.045 + uy * 0.030, y + uy * 0.045 - ux * 0.030),
            connectionstyle="arc3,rad=-4.2",
            arrowstyle="-|>",
            mutation_scale=5 + 8 * frac,
            linewidth=0.5 + 2.2 * frac,
            color=NODE_PALETTE.get(u, "#888888"),
            alpha=0.35 + 0.5 * frac,
            zorder=1,
        )
        ax.add_patch(arr)

    # nodos: etiqueta + dwell % dentro del círculo (texto según luminancia);
    # clases SIN datos en la condición (ej. PUNCT en L2) → huecas grises
    import matplotlib.colors as _mc

    for n in nodes:
        x, y = pos[n]
        present = n in dwell and dwell.get(n, 0.0) > 0
        r = 0.042 + 0.050 * (dwell.get(n, 0.0) / dw_max)
        dur_ok = present and mdur.get(n, np.nan) == mdur.get(n, np.nan)
        if dur_ok:
            color = CMAP_DUR(dur_norm(mdur[n]))
            face, edge, lw, ls = color, "#222222", 0.7, "-"
        else:
            face, edge, lw, ls = "none", "#999999", 1.1, (0, (3, 2))
        ax.add_patch(plt.Circle((x, y), r, facecolor=face, edgecolor=edge, lw=lw,
                                linestyle=ls, zorder=2))
        if dur_ok:
            rgb = _mc.to_rgb(color)
            lum = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
            txt_color = "#ffffff" if lum < 0.55 else "#1a1a1a"
            ax.text(x, y + r * 0.28, n, ha="center", va="center", fontsize=6.2,
                    fontweight="bold", color=txt_color, zorder=3)
            ax.text(x, y - r * 0.30, f"{dwell.get(n, 0)*100:.0f}%", ha="center", va="center",
                    fontsize=5.4, color=txt_color, alpha=0.9, zorder=3)
        else:
            ax.text(x, y + r * 0.28, n, ha="center", va="center", fontsize=6.2,
                    fontweight="bold", color="#8a8a8a", zorder=3)
            ax.text(x, y - r * 0.30, "sin datos", ha="center", va="center",
                    fontsize=4.8, color="#8a8a8a", style="italic", zorder=3)
    ax.set_title(title, fontsize=10)


def plot_network(lang: str, mode: str) -> Optional[Path]:
    """Grafo dirigido clase→clase, 2×2 condiciones, layout circular compartido."""
    mats, attrs = {}, {}
    for session, q in CELLS:
        m = _load_matrix(lang, mode, session, q)
        a = _load_node_attrs(lang, mode, session, q)
        if m is None or a is None:
            return None
        mats[(session, q)] = m
        attrs[(session, q)] = a

    nodes = [n for n in FUSED_ORDER if any(n in m.index for m in mats.values())]
    if not nodes:
        return None
    mats = {k: m.reindex(index=nodes, columns=nodes).fillna(0.0) for k, m in mats.items()}
    pos = _node_xy(nodes)

    durs = np.concatenate([a["mean_dur_ms"].dropna().values for a in attrs.values()])
    dmin, dmax = float(durs.min()), float(durs.max()) or 1.0
    if dmax <= dmin:
        dmax = dmin + 1.0
    dur_norm = Normalize(vmin=dmin, vmax=dmax)
    dwell_max = max(float(a["dwell_share"].max()) for a in attrs.values()) or 1.0

    fig, axes = plt.subplots(2, 2, figsize=(13, 11.5))
    fig.subplots_adjust(left=0.02, right=0.86, top=0.88, bottom=0.02, hspace=0.14, wspace=0.08)
    cs = load_condition_summary(lang)
    for (session, q), ax in zip(CELLS, axes.flat):
        n = None
        if len(cs):
            row = cs[(cs["condition"] == _cond(session, lang, q)) & (cs["mode"] == mode)]
            if len(row):
                n = int(row["n_subjects"].iloc[0])
        title = f"{'Nativo (L1)' if session == 'L1' else 'Inglés (L2)'} · {'peor' if q == 'Q1' else 'mejor'}" + (f" (n={n})" if n else "")
        _draw_network_panel(ax, mats[(session, q)], attrs[(session, q)], nodes, pos, dur_norm, title,
                            dwell_max=dwell_max)
    sm = plt.cm.ScalarMappable(cmap=CMAP_DUR, norm=dur_norm)
    cbar_ax = fig.add_axes([0.885, 0.14, 0.022, 0.70])
    cbar = fig.colorbar(sm, cax=cbar_ax)
    cbar.set_label("Duración media de fijación (ms) — color de nodo", fontsize=9)
    fig.suptitle(
        f"Red de transiciones entre clases — {LANG_NAMES.get(lang, lang)} · modo {mode}\n"
        "ancho/alpha de arista = P(v|u) pooled · tamaño de nodo = dwell share · color = duración media",
        fontsize=12,
    )
    out = _fpath(lang, mode, "network.png")
    fig.savefig(out, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# 6b. Grafo de red INTERACTIVO (pyvis / vis.js)
# ---------------------------------------------------------------------------

def _viridis_hex(t: float) -> str:
    r, g, b, _ = CMAP_DUR(float(np.clip(t, 0.0, 1.0)))
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"


def _build_pyvis_condition(session: str, q: str, lang: str, mode: str, title: str,
                           matrix: pd.DataFrame, counts: Optional[pd.DataFrame],
                           attrs: pd.DataFrame, metrics: Optional[pd.DataFrame],
                           nodes: List[str], pos: Dict[str, Tuple[float, float]],
                           dur_norm, dwell_max: float) -> "pyvis.network.Network":
    """Red pyvis de UNA condición: layout circular fijo, tooltips, satélites self-loop."""
    from pyvis.network import Network

    net = Network(height="700px", width="100%", directed=True, bgcolor="#ffffff",
                  cdn_resources="remote", notebook=False)
    net.heading = title
    net.toggle_physics(False)

    CX = CY = 350.0
    R = 230.0

    def xy(n: str) -> Tuple[float, float]:
        # vis.js invierte el eje y: y_px = cy - R*sin → misma orientación que el PNG
        x, y = pos[n]
        return (CX + (x - 0.5) * 2 * R, CY - (y - 0.5) * 2 * R)

    dwell = {n: float(attrs.loc[n, "dwell_share"]) for n in nodes if n in attrs.index}
    mdur = {n: float(attrs.loc[n, "mean_dur_ms"]) for n in nodes if n in attrs.index}
    nfix = {n: float(attrs.loc[n, "n_fixations"]) for n in nodes if n in attrs.index}
    pr = {}
    if metrics is not None and len(metrics):
        pr = {n: float(metrics.loc[n, "pagerank"]) for n in nodes if n in metrics.index}

    wmax = float(matrix.values.max()) or 1.0

    for n in nodes:
        x, y = xy(n)
        present = n in dwell and dwell.get(n, 0.0) > 0
        dur_ok = present and mdur.get(n, np.nan) == mdur.get(n, np.nan)
        size = 12 + 60 * (dwell.get(n, 0.0) / dwell_max)
        if dur_ok:
            fill = _viridis_hex(dur_norm(mdur[n]))
            font_color = "#ffffff" if dur_norm(mdur[n]) < 0.55 else "#1a1a1a"
            border = "#222222"
        else:
            fill = "#ffffff"
            font_color = "#8a8a8a"
            border = "#999999"
        tip = f"<b>{n}</b>"
        if present:
            tip += (f"<br>dwell: {dwell[n]*100:.1f}%"
                    + (f"<br>duración media: {mdur[n]:.0f} ms" if dur_ok else "")
                    + f"<br>n fijaciones: {nfix[n]:,.0f}")
            if n in pr:
                tip += f"<br>PageRank: {pr[n]:.4f}"
            ws = float(matrix.loc[n, n]) if n in matrix.index else 0.0
            if ws > 0:
                tip += f"<br>self-loop P(u|u): {ws:.3f}"
        else:
            tip += "<br><i>sin fijaciones clasificadas en esta condición</i>"
        node_kw = dict(label=n, x=x, y=y, size=size, title=tip, physics=False,
                       shape="dot", font={"size": 15, "color": font_color, "face": "Arial"},
                       color={"background": fill, "border": border,
                              "highlight": {"background": fill, "border": "#000000"}},
                       border_width=2)
        if not present:
            node_kw["shapeProperties"] = {"borderDashes": [4, 3]}
        net.add_node(n, **node_kw)

    for u in nodes:
        for v in nodes:
            w = float(matrix.loc[u, v]) if (u in matrix.index and v in matrix.columns) else 0.0
            if w <= 0:
                continue
            frac = w / wmax
            col = NODE_PALETTE.get(u, "#888888")
            n_uv = float(counts.loc[u, v]) if (counts is not None and u in counts.index and v in counts.columns) else None
            tip = f"{u} → {v}<br>P(v|u) = {w:.3f}"
            if n_uv is not None:
                tip += f"<br>n = {n_uv:,.0f}"
            if u != v:
                net.add_edge(u, v, width=1.0 + 16.0 * frac, title=tip,
                             color={"color": col, "opacity": 0.10 + 0.72 * frac,
                                    "highlight": col},
                             arrows={"to": {"enabled": True, "scaleFactor": 0.45}},
                             smooth={"enabled": True, "type": "curvedCW", "roundness": 0.16})

    # satélites de self-loop: segundo endpoint para dibujar u→u
    for u in nodes:
        ws = float(matrix.loc[u, u]) if u in matrix.index else 0.0
        if ws <= 0:
            continue
        frac = min(ws / wmax, 1.0)
        x, y = xy(u)
        dx, dy = x - CX, y - CY
        L = (dx**2 + dy**2) ** 0.5 or 1.0
        sx, sy = CX + dx / L * (R + 62), CY + dy / L * (R + 62)
        sat = f"{u}↺"
        col = NODE_PALETTE.get(u, "#888888")
        tip = f"{u} → {u} (self-bucle)<br>P(u|u) = {ws:.3f}"
        n_uu = float(counts.loc[u, u]) if (counts is not None and u in counts.index) else None
        if n_uu is not None:
            tip += f"<br>n = {n_uu:,.0f}"
        net.add_node(sat, label="", x=sx, y=sy, size=6, title=tip, physics=False,
                     shape="dot", color={"background": col, "opacity": 0.55, "border": col})
        for a, b in ((u, sat), (sat, u)):
            net.add_edge(a, b, width=0.8 + 9.0 * frac, title=tip,
                         color={"color": col, "opacity": 0.30 + 0.55 * frac, "highlight": col},
                         arrows={"to": {"enabled": True, "scaleFactor": 0.4}}, dashed=True,
                         smooth={"enabled": False})

    return net


def _network_wrapper(lang: str, mode: str, cells: List[Tuple[str, str, str]], out: Path,
                     dmin: float, dmax: float) -> Path:
    """HTML contenedor: grilla 2×2 de iframes + leyenda compartida."""
    legend = " ".join(
        f'<span style="margin-right:10px"><span style="display:inline-block;width:11px;height:11px;'
        f'background:{NODE_PALETTE[n]};border-radius:3px;margin-right:4px;vertical-align:middle"></span>'
        f"<small>{n}</small></span>"
        for n in FUSED_ORDER
    )
    frames = "\n".join(
        f'<div style="background:#fff;border:1px solid #ddd;border-radius:6px;overflow:hidden">'
        f'<iframe src="./network/{cid}.html" style="width:100%;height:640px;border:0"></iframe></div>'
        for _, _, cid in cells
    )
    cell_titles = "\n".join(
        f'<div style="grid-row:{i // 2 + 2};grid-column:{i % 2 + 1};text-align:center;'
        f'font-weight:600;padding:4px">{t}</div>'
        for i, (_, t, _) in enumerate(cells)
    )
    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<title>Red interactiva — {LANG_NAMES.get(lang, lang)} · {mode}</title></head>
<body style="font-family:Arial,Helvetica,sans-serif;margin:18px;background:#fafafa">
<h2 style="margin:0 0 2px">Red de transiciones entre clases — {LANG_NAMES.get(lang, lang)} · modo {mode}</h2>
<p style="margin:4px 0 10px;color:#444">
  Tamaño de nodo = dwell share · color de nodo = duración media de fijación ·
  ancho/opacity de arista = P(v|u) pooled · <b>nodo hueco</b> = sin datos en esa condición ·
  <b>nodo satélite punteado</b> = self-bucle u→u · pasa el cursor para estadísticas; arrastra nodos si lo necesitas.
</p>
<div style="margin:6px 0 12px">{legend}</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px 10px;max-width:1500px">
  {cell_titles}
  {frames}
</div>
<div style="margin-top:14px;display:flex;align-items:center;gap:10px">
  <small>duración media (ms):</small>
  <span style="width:220px;height:12px;border:1px solid #ccc;border-radius:3px;display:inline-block;
    background:linear-gradient(to right,#440154,#3b528b,#21918c,#5ec962,#fde725)"></span>
  <small>{dmin:.0f} ms</small><span style="flex:1"></span><small>{dmax:.0f} ms</small>
</div>
</body></html>"""
    out.write_text(html, encoding="utf-8")
    return out


def plot_network_interactive(lang: str, mode: str) -> Optional[Path]:
    """Red interactiva 2×2 (pyvis): network/<cond>.html + wrapper network.html."""
    try:
        import pyvis  # noqa: F401
    except ImportError:
        print("[viz] pyvis no instalado — red interactiva omitida")
        return None

    mats, attrs, counts = {}, {}, {}
    for session, q in CELLS:
        m = _load_matrix(lang, mode, session, q)
        a = _load_node_attrs(lang, mode, session, q)
        if m is None or a is None:
            return None
        mats[(session, q)] = m
        attrs[(session, q)] = a
        counts[(session, q)] = _load_counts(lang, mode, session, q)

    nodes = [n for n in FUSED_ORDER if any(n in m.index for m in mats.values())]
    if not nodes:
        return None
    mats = {k: m.reindex(index=nodes, columns=nodes).fillna(0.0) for k, m in mats.items()}
    pos = _node_xy(nodes)

    durs = np.concatenate([a["mean_dur_ms"].dropna().values for a in attrs.values()])
    dmin = float(durs.min()) if len(durs) else 0.0
    dmax = float(durs.max()) or 1.0
    if dmax <= dmin:
        dmax = dmin + 1.0
    dur_norm = Normalize(vmin=dmin, vmax=dmax)
    dwell_max = max(float(a["dwell_share"].max()) for a in attrs.values()) or 1.0

    cs = load_condition_summary(lang)
    net_dir = figures_dir(lang, mode) / "network"
    net_dir.mkdir(parents=True, exist_ok=True)

    cells = []
    for session, q in CELLS:
        cid = _cond(session, lang, q)
        n = None
        if len(cs):
            row = cs[(cs["condition"] == cid) & (cs["mode"] == mode)]
            if len(row):
                n = int(row["n_subjects"].iloc[0])
        title = (f"{'Nativo (L1)' if session == 'L1' else 'Inglés (L2)'} · "
                 f"{'peor' if q == 'Q1' else 'mejor'}" + (f" (n={n})" if n else ""))
        mpath = mode_dir(lang, mode) / f"node_metrics_{cid}.csv"
        metrics = pd.read_csv(mpath, index_col=0) if mpath.exists() else None
        net = _build_pyvis_condition(session, q, lang, mode, title, mats[(session, q)],
                                     counts[(session, q)], attrs[(session, q)], metrics,
                                     nodes, pos, dur_norm, dwell_max)
        net.write_html(str(net_dir / f"{cid}.html"), open_browser=False, notebook=False)
        cells.append((cid, title, cid))
    out = figures_dir(lang, mode) / "network.html"
    _network_wrapper(lang, mode, cells, out, dmin, dmax)
    return out


# ---------------------------------------------------------------------------

def generate_all_figures(langs: Optional[List[str]] = None, modes=("temporal", "regression")) -> None:
    if langs is None:
        langs = list(CONDITION_LANGS)
    all_langs = set(CONDITION_LANGS)
    n = {"box": 0, "trans": 0, "fix": 0, "bw": 0, "l1l2": 0, "net": 0, "net_i": 0}
    for lang in langs:
        if lang not in all_langs:
            continue
        plot_accuracy_box(lang)
        n["box"] += 1
        for mode in modes:
            md = mode_dir(lang, mode)
            if not md.exists():
                print(f"[viz] {lang} ({mode}): sin build previo — omitido")
                continue
            if plot_transitions_bar(lang, mode):
                n["trans"] += 1
            plot_transitions_normalized_bar(lang, mode)
            plot_transitions_comparison(lang, mode)
            if plot_fixations_bar(lang, mode):
                n["fix"] += 1
            plot_fixations_normalized_bar(lang, mode)
            plot_fixations_comparison(lang, mode)
            bw, l1l2 = plot_diff_heatmaps(lang, mode)
            if bw:
                n["bw"] += 1
            if l1l2:
                n["l1l2"] += 1
            if plot_network(lang, mode):
                n["net"] += 1
            if plot_network_interactive(lang, mode):
                n["net_i"] += 1
        print(f"[viz] {lang}: figuras generadas")
    print(
        f"[viz] total: box={n['box']} trans={n['trans']} fix={n['fix']} "
        f"bestworst={n['bw']} l1vl2={n['l1l2']} network={n['net']} network_interactive={n['net_i']}"
    )
