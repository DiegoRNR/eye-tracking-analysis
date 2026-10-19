"""
networks/word-type-transitions/core/report.py

Genera output/<lang>/REPORT.md: resumen metodológico, QA por condición,
contrastes del 2×2 y figuras embebidas — SOLO para esa lengua.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd

from .paths import lang_dir, mode_dir
from .visualization import CONTRASTS, CONTRAST_TITLES, LANG_NAMES


def generate_report(lang: str, modes=("temporal", "regression")) -> Path:
    ld = lang_dir(lang)
    lines: List[str] = [
        f"# Red de transición entre tipos de palabra — {LANG_NAMES.get(lang, lang)}",
        "",
        "Diseño 2×2: {L1 nativo, L2 inglés} × {Q1 (accuracy ≤ p25), Q4 (accuracy ≥ p75)}"
        " calculado DENTRO del grupo. Nodos = tipos de palabra (fused); aristas ="
        " transiciones entre fijaciones consecutivas (blink excluido).",
        "**Carga cognitiva de nodo = duración media de fijación (ms)** (más dwell_share).",
        "",
        "Contrastes (permutación, emparejada por sujeto cuando ≥5 pares; BH-FDR):",
        "Q4−Q1 en L1, Q4−Q1 en L2, L1−L2 en Q4, L1−L2 en Q1.",
        "",
    ]

    cs_path = ld / "condition_summary.csv"
    if cs_path.exists():
        cs = pd.read_csv(cs_path)
        if len(cs):
            lines += [
                "## Condiciones (n sujetos por celda)",
                "",
                "| Condición | Modo | n | acc Q1 | acc Q4 | aristas >0 |",
                "| :--- | :--- | ---: | ---: | ---: | ---: |",
            ]
            for _, r in cs.iterrows():
                acc_q1 = r.get("acc_Q1")
                acc_q4 = r.get("acc_Q4")
                acc_q1_txt = f"{acc_q1:.2f}" if pd.notna(acc_q1) else ""
                acc_q4_txt = f"{acc_q4:.2f}" if pd.notna(acc_q4) else ""
                lines.append(
                    f"| {r['condition']} | {r['mode']} | {int(r['n_subjects'])} | "
                    f"{acc_q1_txt} | {acc_q4_txt} | {int(r['group_edges_nonzero'])} |"
                )
            lines.append("")

    for mode in modes:
        md = ld / mode
        if not md.exists():
            continue
        lines += [f"## Contrastes (modo {mode})", ""]
        any_comp = False
        for contrast, la, lb, _ in CONTRASTS:
            p = md / f"comparison_{contrast}.csv"
            if not p.exists():
                continue
            df = pd.read_csv(p)
            sig = df[df["significant_fdr_0.05"]]
            note = f"{len(sig)} aristas FDR-significativas de {len(df)}"
            lines.append(f"- **{CONTRAST_TITLES[contrast]}**: {note}.")
            top = sig.reindex(sig["diff"].abs().sort_values(ascending=False).index).head(3)
            for _, r in top.iterrows():
                lines.append(
                    f"  - `{r['edge']}`: Δ={r['diff']:+.3f} "
                    f"({la}={r[f'mean_{la}']:.3f} vs {lb}={r[f'mean_{lb}']:.3f}, p_BH={r['p_bh']:.3f})"
                )
            any_comp = True
        if not any_comp:
            lines.append("- (sin comparison_*.csv; ejecuta `compare`)")
        lines.append("")

        # --- figuras del modo
        lines += [f"### Figuras (modo {mode})", ""]
        for name, label in [
            ("transitions_bar", "Top transiciones clase→clase (bar)"),
            ("fixations_bar", "n de fijaciones por clase (bar)"),
            ("heatmap_bestworst", "Heatmap Q4−Q1 (mejores vs peores)"),
            ("heatmap_l1vl2", "Heatmap L1−L2 (mismo cuartil)"),
            ("network", "Grafo de red 2×2 (PNG)"),
            ("network.html", "Grafo de red 2×2 (interactivo, hover por arista/nodo)"),
        ]:
            if name.endswith(".html"):
                rel = f"{mode}/figures/{name}"
            else:
                rel = f"{mode}/figures/{name}.png"
            lines.append(f"- {label}: [{name}]({rel})")
        lines.append("")

    # accuracy box (compartido entre modos, vive en temporal/)
    if (ld / "temporal" / "figures" / "accuracy_box.png").exists():
        lines += [
            "### Accuracy",
            "",
            "- Box plot por celda: [accuracy_box](temporal/figures/accuracy_box.png)",
            "",
        ]

    lines += [
        "## Notas metodológicas",
        "",
        f"- Tokens tipificados con `data/benchmark/words_classified_{lang}_l1.csv` (L1)"
        " y `words_classified.csv` (L2 inglés).",
        "- Duraciones: `dur` del reporte de fijaciones (ms); nodos con n_fix>0.",
        "- Las comparaciones L1 vs L2 usan textos distintos (nativos vs ingleses) por diseño MECO.",
        "",
        "Fin del reporte.",
    ]

    out = ld / "REPORT.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out
