"""
networks/reading-pattern-mds/core/viz.py

Figuras MDS (matplotlib estático):

Estilo:
- un color por grupo lingüístico (paleta determinista);
- marcador por sesión: L1 (lectura propia) = círculo, L2 (lectura inglés) = triángulo;
  cohortes nativos en_* = estrella (gris oscuro);
- cuartil: Q1 = marker hueco, Q4 = relleno (solo variantes de cuartiles);
- líneas finas: L1<->L2 de cada grupo (full) o Q1<->Q4 de cada (grupo, sesión);
- stress-1 en el título.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

from . import paths
from .mds import classical_mds

_PALETTE = (
    list(plt.cm.tab20(np.linspace(0, 1, 20)))
    + list(plt.cm.tab20b(np.linspace(0, 1, 20)))
    + list(plt.cm.tab20c(np.linspace(0, 1, 20)))
)

REF_COLOR = "#333333"


def _lang_palette(langs: list[str]) -> dict[str, tuple]:
    uniq = sorted(set(langs))
    return {lg: _PALETTE[i % len(_PALETTE)] for i, lg in enumerate(uniq)}


def parse_condition(cond: str) -> tuple[str, str, str | None]:
    parts = cond.split("-")
    session, lang = parts[0], parts[1]
    quart = parts[2] if len(parts) > 2 else None
    return session, lang, quart


def point_label(cond: str, lang: str) -> str:
    session, _, quart = parse_condition(cond)
    lbl = f"{paths.fig_label(lang)} {session}"
    return f"{lbl} {quart}" if quart else lbl


def is_ref(lang: str) -> bool:
    return lang in paths.EN_REFS.values()


def plot_variant(
    dist: pd.DataFrame,
    conditions: list[str],
    title: str,
    out_png: Path,
    link: str = "sessions",  # 'sessions' | 'quartiles'
    annotate_refs_dist: bool = False,
    embeddings_out: list | None = None,
    fig_name: str = "",
) -> float:
    emb, stress = classical_mds(dist.loc[conditions, conditions])
    langs = [parse_condition(c)[1] for c in conditions]
    palette = _lang_palette(langs)

    fig, ax = plt.subplots(figsize=(11, 9))
    ax.axhline(0, color="#cccccc", lw=0.6, zorder=1)
    ax.axvline(0, color="#cccccc", lw=0.6, zorder=1)

    # líneas de enlace
    for c in conditions:
        session, lang, quart = parse_condition(c)
        if is_ref(lang):
            continue
        if link == "sessions" and quart is None:
            other = f"L2-{lang}" if session == "L1" else f"L1-{lang}"
            pair = (c, other)
        elif link == "quartiles" and quart is not None:
            other = f"{session}-{lang}-" + ("Q4" if quart == "Q1" else "Q1")
            pair = (c, other)
        else:
            continue
        if other in emb.index:
            ax.plot(
                [emb.loc[c, "mds1"], emb.loc[other, "mds1"]],
                [emb.loc[c, "mds2"], emb.loc[other, "mds2"]],
                color=palette[lang], alpha=0.35, lw=1.0, linestyle="-", zorder=2,
            )

    # puntos
    ordered = sorted(conditions, key=lambda c: is_ref(parse_condition(c)[1]))
    ref_offsets = {}  # mismo cohorte en distinto punto: alternar offsets para evitar choque
    for c in ordered:
        session, lang, quart = parse_condition(c)
        color = REF_COLOR if is_ref(lang) else palette[lang]
        marker = "*" if is_ref(lang) else ("o" if session == "L1" else "^")
        filled = quart != "Q1"
        size = 260 if is_ref(lang) else 95
        if filled:
            ax.scatter(
                emb.loc[c, "mds1"], emb.loc[c, "mds2"], marker=marker, s=size,
                color=color, zorder=5, edgecolors="white", linewidths=0.8,
            )
        else:
            ax.scatter(
                emb.loc[c, "mds1"], emb.loc[c, "mds2"], marker=marker, s=size,
                facecolors="none", edgecolors=color, linewidths=1.6, zorder=5,
            )
        if is_ref(lang):
            ref_offsets.setdefault(lang, 0)
            ref_offsets[lang] += 1
            # en_ca arriba del punto, en_uk abajo (y alternancia por sesión)
            dy = 6 if lang == "en" else -13
            xytext = (7, dy if ref_offsets[lang] % 2 else dy - 8)
        else:
            xytext = (7, 6)
        ax.annotate(
            f"{point_label(c, lang)}",
            (emb.loc[c, "mds1"], emb.loc[c, "mds2"]),
            textcoords="offset points", xytext=xytext,
            fontsize=8 if not is_ref(lang) else 8.5,
            fontweight="bold" if is_ref(lang) else "normal",
            color=REF_COLOR if is_ref(lang) else "#222222",
        )

    # anotación de distancias a cohortes nativos (plots por lengua)
    if annotate_refs_dist:
        for c in ordered:
            session, lang, quart = parse_condition(c)
            if is_ref(lang):
                continue
            base = f"{session}-{lang}" + (f"-{quart}" if quart else "")
            parts = []
            for ref in paths.EN_REFS:  # en_ca, en_uk
                refc = f"{session}-{paths.EN_REFS[ref]}" + (f"-{quart}" if quart else "")
                if refc in dist.columns:
                    parts.append(f"{ref} d={dist.loc[base, refc]:.2f}")
            if parts:
                ax.annotate(
                    " · ".join(parts),
                    (emb.loc[c, "mds1"], emb.loc[c, "mds2"]),
                    textcoords="offset points", xytext=(6, -11),
                    fontsize=6.8, color="#555555",
                )

    # leyenda
    handles = []
    seen_lang = set()
    for lg in sorted(set(lang for lang in langs if not is_ref(lang))):
        seen_lang.add(lg)
        handles.append(Line2D([], [], marker="o", color="none", markerfacecolor=palette[lg],
                              markeredgecolor="none", markersize=8, label=paths.fig_label(lg)))
    handles += [
        Line2D([], [], marker="o", color="#222222", linestyle="none", markerfacecolor="#555555",
               markersize=8, label="L1 (lectura nativa)"),
        Line2D([], [], marker="^", color="#222222", linestyle="none", markerfacecolor="#555555",
               markersize=8, label="L2 (lectura en inglés)"),
        Line2D([], [], marker="*", color="none", markerfacecolor=REF_COLOR, markersize=11,
               label="cohortes nativos en_*"),
    ]
    if link == "quartiles":
        handles += [
            Line2D([], [], marker="o", color="#555555", linestyle="none", markerfacecolor="none",
                   markersize=8, label="Q1 (cuartil bajo)"),
            Line2D([], [], marker="o", color="#555555", linestyle="none", markerfacecolor="#555555",
                   markersize=8, label="Q4 (cuartil alto)"),
        ]
    ax.legend(handles=handles, loc="best", ncol=4, fontsize=7.5, framealpha=0.85)

    ax.set_title(f"{title}\nMDS clásico · J-S distance · stress-1 = {stress:.3f}", fontsize=12)
    ax.set_xlabel("Dimensión MDS 1")
    ax.set_ylabel("Dimensión MDS 2")
    fig.tight_layout()
    fig.savefig(out_png, dpi=200)
    plt.close(fig)

    if embeddings_out is not None:
        e = emb.reset_index().rename(columns={"index": "condition"})
        e.insert(0, "figure", fig_name)
        e.insert(1, "stress", stress)
        embeddings_out.append(e)
    return stress
