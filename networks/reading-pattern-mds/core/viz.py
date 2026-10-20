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


def plot_closeness_vs_comprehension(mode: str) -> tuple[Path, Path]:
    """
    Genera figuras de correlación entre cercanía a nativos de inglés (1 - J-S)
    y comprensión lectora (accuracy %) para los cortes: all, Q1 y Q4.

    Retorna:
    1. closeness_vs_comprehension_all_q1_q4.png (3 paneles: L2 en all, Q1, Q4)
    2. closeness_vs_comprehension_full_comparison.png (2x3: L2 arriba vs L1 abajo)
    """
    from scipy import stats

    df_path = paths.distances_dir(mode) / "distance_to_native.csv"
    if not df_path.exists():
        raise FileNotFoundError(f"No se encontró {df_path}")
    df = pd.read_csv(df_path)

    langs = paths.target_langs()
    palette = _lang_palette(langs)

    # -------------------------------------------------------------------------
    # Figura 1: L2 (Lectura en inglés) - 3 paneles: all, Q1, Q4
    # -------------------------------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.5), sharey=True)
    quartiles = [("all", "Todos los sujetos"), ("Q1", "Cuartil bajo (Q1)"), ("Q4", "Cuartil alto (Q4)")]

    for i, (q, q_title) in enumerate(quartiles):
        ax = axes[i]
        sub = df[(df["session"] == "L2") & (df["quartile"] == q)].dropna(subset=["accuracy", "closeness_mean"])

        xs = sub["accuracy"].values * 100.0  # en %
        ys = sub["closeness_mean"].values
        lgs = sub["lang"].values

        for x, y, lg in zip(xs, ys, lgs):
            c = palette.get(lg, "#4a5568")
            lbl = paths.fig_label(lg)
            ax.scatter(x, y, color=c, s=55, alpha=0.9, edgecolors="#333", linewidth=0.6, zorder=4)
            ax.annotate(lbl, (x, y), xytext=(3, 3), textcoords="offset points", fontsize=7.2, color="#2d3748")

        # Referencias nativas
        ref_accs = []
        for ref_col in ("acc_en_ca", "acc_en_uk"):
            if ref_col in sub.columns and not sub[ref_col].dropna().empty:
                ref_accs.append(sub[ref_col].dropna().iloc[0] * 100.0)
        for r_idx, r_acc in enumerate(ref_accs):
            r_name = "en_ca" if r_idx == 0 else "en_uk"
            ax.scatter(r_acc, 1.0, marker="*", s=130, color="#d69e2e", edgecolors="#1a202c", linewidth=0.8, zorder=5)
            ax.annotate(f"★ {r_name} (ref)", (r_acc, 1.0), xytext=(-15, -12), textcoords="offset points",
                        fontsize=7.5, fontweight="bold", color="#744210")

        # Línea de regresión OLS y estadísticas
        if len(sub) > 2:
            r, p_val = stats.pearsonr(sub["accuracy"], sub["closeness_mean"])
            rho, sp_val = stats.spearmanr(sub["accuracy"], sub["closeness_mean"])

            slope, intercept = np.polyfit(xs, ys, 1)
            x_line = np.linspace(xs.min(), xs.max(), 100)
            y_line = slope * x_line + intercept
            ax.plot(x_line, y_line, color="#2b6cb0", linestyle="--", linewidth=1.8, label="Tendencia OLS", zorder=3)

            signif = " (p < 0.01)" if p_val < 0.01 else (" (p < 0.05)" if p_val < 0.05 else " (n.s.)")
            stat_box = (
                f"Pearson r = {r:+.3f}{signif}\n"
                f"p-valor = {p_val:.4f}\n"
                f"Spearman ρ = {rho:+.3f} (p={sp_val:.4f})\n"
                f"n = {len(sub)} lenguas"
            )
            ax.text(0.04, 0.06, stat_box, transform=ax.transAxes, fontsize=8.0,
                    verticalalignment="bottom", bbox=dict(boxstyle="round,pad=0.4", facecolor="#edf2f7", edgecolor="#cbd5e0", alpha=0.9))

        ax.set_title(f"L2 inglés · {q_title}", fontsize=11, fontweight="bold")
        ax.set_xlabel("Comprensión lectora (% accuracy)", fontsize=9.5)
        if i == 0:
            ax.set_ylabel("Cercanía a nativos de inglés (1 − JSD)", fontsize=9.5)
        ax.grid(True, linestyle=":", alpha=0.4)
        ax.set_ylim(0.80, 1.02)

    fig.suptitle(
        f"Correlación: Comprensión Lectora vs Cercanía a Lectores Nativos de Inglés (L2)\n"
        f"Modo: {mode} · Cortes: Todos los sujetos, Cuartil Bajo (Q1) y Cuartil Alto (Q4)",
        fontsize=13, fontweight="bold", y=1.02
    )
    fig.tight_layout()
    out1 = paths.figures_dir(mode) / "closeness_vs_comprehension_all_q1_q4.png"
    fig.savefig(out1, dpi=200, bbox_inches="tight")
    plt.close(fig)

    # -------------------------------------------------------------------------
    # Figura 2: 2x3 completo (L2 inglés arriba vs L1 nativo abajo)
    # -------------------------------------------------------------------------
    fig2, axes2 = plt.subplots(2, 3, figsize=(16, 10), sharey="row")
    sessions = [("L2", "Lectura en inglés (L2)"), ("L1", "Lectura en lengua nativa (L1)")]

    for row_idx, (sess, sess_title) in enumerate(sessions):
        for col_idx, (q, q_title) in enumerate(quartiles):
            ax = axes2[row_idx, col_idx]
            sub = df[(df["session"] == sess) & (df["quartile"] == q)].dropna(subset=["accuracy", "closeness_mean"])
            xs = sub["accuracy"].values * 100.0
            ys = sub["closeness_mean"].values
            lgs = sub["lang"].values

            for x, y, lg in zip(xs, ys, lgs):
                c = palette.get(lg, "#4a5568")
                lbl = paths.fig_label(lg)
                ax.scatter(x, y, color=c, s=50, alpha=0.9, edgecolors="#333", linewidth=0.6, zorder=4)
                ax.annotate(lbl, (x, y), xytext=(3, 3), textcoords="offset points", fontsize=6.8, color="#2d3748")

            if sess == "L2":
                ref_accs = []
                for ref_col in ("acc_en_ca", "acc_en_uk"):
                    if ref_col in sub.columns and not sub[ref_col].dropna().empty:
                        ref_accs.append(sub[ref_col].dropna().iloc[0] * 100.0)
                for r_acc in ref_accs:
                    ax.scatter(r_acc, 1.0, marker="*", s=110, color="#d69e2e", edgecolors="#1a202c", linewidth=0.8, zorder=5)

            if len(sub) > 2:
                r, p_val = stats.pearsonr(sub["accuracy"], sub["closeness_mean"])
                rho, sp_val = stats.spearmanr(sub["accuracy"], sub["closeness_mean"])
                slope, intercept = np.polyfit(xs, ys, 1)
                x_line = np.linspace(xs.min(), xs.max(), 100)
                y_line = slope * x_line + intercept
                line_color = "#2b6cb0" if sess == "L2" else "#718096"
                ax.plot(x_line, y_line, color=line_color, linestyle="--", linewidth=1.6, zorder=3)

                signif = " (p < 0.01)" if p_val < 0.01 else (" (p < 0.05)" if p_val < 0.05 else " (n.s.)")
                stat_box = (
                    f"r = {r:+.3f}{signif}\n"
                    f"p = {p_val:.4f}\n"
                    f"ρ = {rho:+.3f}"
                )
                ax.text(0.04, 0.06, stat_box, transform=ax.transAxes, fontsize=7.5,
                        verticalalignment="bottom", bbox=dict(boxstyle="round,pad=0.3", facecolor="#edf2f7", edgecolor="#cbd5e0", alpha=0.9))

            ax.set_title(f"{sess_title} · {q_title}", fontsize=10.5, fontweight="bold")
            ax.set_xlabel("Comprensión lectora (% accuracy)", fontsize=9)
            if col_idx == 0:
                ax.set_ylabel("Cercanía a nativos (1 − JSD)", fontsize=9)
            ax.grid(True, linestyle=":", alpha=0.4)

    fig2.suptitle(
        f"Contraste: Comprensión vs Cercanía a Nativos de Inglés — Modo {mode}\n"
        f"(Arriba: L2 inglés muestra correlación significativa en all y Q1; Abajo: L1 nativo muestra especificidad sin correlación)",
        fontsize=12.5, fontweight="bold", y=1.01
    )
    fig2.tight_layout()
    out2 = paths.figures_dir(mode) / "closeness_vs_comprehension_full_comparison.png"
    fig2.savefig(out2, dpi=200, bbox_inches="tight")
    plt.close(fig2)

    return out1, out2
