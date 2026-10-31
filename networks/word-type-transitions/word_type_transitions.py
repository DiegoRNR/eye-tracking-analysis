"""
networks/word-type-transitions/word_type_transitions.py

Entry point CLI. La lógica vive en core/.

Ejecución PER LENGUA: cada lenguaje escribe en su propio árbol
output/<lang>/<mode>/ (temporal, regression), sin mezclar salidas.

Subcomandos:
- build:    construye las redes del 2×2 ({L1,L2} × {Q1,Q4}) por modo y guarda
            CSVs + atributos de nodo (carga cognitiva = duración) + accuracy
            por sujeto para el box plot.
- compare:  contrastes del 2×2 (permutación + BH-FDR) -> comparison_<c>.csv.
- figures:  suite de figuras (accuracy box, barras de transiciones/fijaciones,
            heatmaps best-vs-worst y L1-vs-L2, grafo de red).
- animate:  redes ANIMADAS en el tiempo (pyvis): network_anim.html 2×2 por
            lengua/modo; las aristas aparecen en orden de lectura. Opt-in
            (recarga fijaciones crudas), no forma parte de `all`.
- report:   output/<lang>/REPORT.md.
- all:      build + compare + figures + report.

Uso:
    python word_type_transitions.py all --lang du
    python word_type_transitions.py build --lang ee,fi --mode temporal
    python word_type_transitions.py all --lang all
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def _modes(arg: str) -> list[str]:
    return ["temporal", "regression"] if arg == "both" else [arg]


def _langs(arg: str) -> list[str]:
    from core.paths import CH_VARIANTS, CONDITION_LANGS

    if arg == "all":
        return list(CONDITION_LANGS)
    sel = [s.strip() for s in arg.split(",") if s.strip()]
    valid = set(CONDITION_LANGS)
    bad = [s for s in sel if s not in valid]
    if bad:
        sys.exit(
            f"[error] lenguas desconocidas: {bad}. Válidas: {CONDITION_LANGS}"
        )
    return sel


def cmd_build(langs: list[str], modes: list[str]) -> None:
    import pandas as pd

    from core.data_io import load_accuracy
    from core.grouping import quartile_groups
    from core.network_builder import build_condition
    from core.paths import MIN_GROUP_N, prepare_lang_dirs
    from core.persistence import (
        save_accuracy_subjects,
        save_condition,
        save_condition_summary,
        save_node_metrics,
        write_metadata,
    )
    from core.stats import graph_metrics

    for lang in langs:
        prepare_lang_dirs(lang, modes)
        print(f"[build] === {lang} ===")
        rows = []
        acc_rows = []
        for session in ("L1", "L2"):
            acc = load_accuracy(session, lang)
            groups, gsum = quartile_groups(acc, min_n=MIN_GROUP_N)
            for uid in sorted(groups):
                acc_rows.append(
                    {
                        "uniform_id": uid,
                        "session": session,
                        "accuracy": float(acc[uid]),
                        "quartile": groups[uid],
                    }
                )
        if acc_rows:
            save_accuracy_subjects(lang, acc_rows)
        for session, quartile in (("L1", "Q1"), ("L1", "Q4"), ("L2", "Q1"), ("L2", "Q4")):
            cond_id = f"{session}-{lang}-{quartile}"
            for mode in modes:
                res = build_condition(session, lang, quartile, mode)
                nodes = res["group_matrix"].index
                counts = pd.DataFrame(0.0, index=nodes, columns=nodes)
                for (u, v), n in res["pooled_counts"].items():
                    if u in counts.index and v in counts.columns:
                        counts.loc[u, v] = float(n)
                res["counts_matrix"] = counts
                save_condition(cond_id, lang, mode, res)
                metrics, density = graph_metrics(res["group_matrix"])
                save_node_metrics(lang, mode, cond_id, metrics, density)
                gsum = res["summary"]["acc_quartiles"]
                rows.append(
                    {
                        "condition": cond_id,
                        "session": session,
                        "quartile": quartile,
                        "mode": mode,
                        "n_subjects": res["summary"]["n_subjects"],
                        "acc_Q1": gsum.get("acc_mean_Q1"),
                        "acc_Q4": gsum.get("acc_mean_Q4"),
                        "n_edges": res["summary"]["n_edges"],
                        "group_edges_nonzero": res["summary"]["group_edges_nonzero"],
                    }
                )
                print(
                    f"[build] {cond_id} ({mode}): n={res['summary']['n_subjects']} "
                    f"edges={res['summary']['group_edges_nonzero']}"
                )
        save_condition_summary(lang, rows)
        print(f"[build] {lang}: condition_summary.csv + accuracy_subjects.csv")
    write_metadata()
    print("[build] metadata.json")


def cmd_compare(langs: list[str], modes: list[str]) -> None:
    import pandas as pd

    from core.persistence import save_comparison
    from core.stats import compare_conditions

    contrasts = [
        ("Q4vQ1_L1", ("L1", "Q4"), ("L1", "Q1"), "Q4", "Q1"),
        ("Q4vQ1_L2", ("L2", "Q4"), ("L2", "Q1"), "Q4", "Q1"),
        ("L1vL2_Q4", ("L1", "Q4"), ("L2", "Q4"), "L1", "L2"),
        ("L1vL2_Q1", ("L1", "Q1"), ("L2", "Q1"), "L1", "L2"),
    ]
    for lang in langs:
        print(f"[compare] === {lang} ===")
        for mode in modes:
            md = Path("output") / lang / mode
            for contrast, (sa, qa), (sb, qb), la, lb in contrasts:
                pa = md / f"per_participant_{sa}-{lang}-{qa}.csv"
                pb = md / f"per_participant_{sb}-{lang}-{qb}.csv"
                if not pa.exists() or not pb.exists():
                    print(f"[compare] {lang} {contrast} ({mode}): faltan per_participant")
                    continue
                pp_a = pd.read_csv(pa, index_col=0)
                pp_b = pd.read_csv(pb, index_col=0)
                df = compare_conditions(pp_a, pp_b, la, lb)
                save_comparison(lang, mode, contrast, df)
                n_sig = int(df["significant_fdr_0.05"].sum())
                print(f"[compare] {lang} {contrast} ({mode}): {n_sig}/{len(df)} FDR-sig")
    print("[compare] listo")


def cmd_figures(langs: list[str], modes: list[str]) -> None:
    from core.visualization import generate_all_figures

    generate_all_figures(langs, modes)


def cmd_animate(langs: list[str], modes: list[str]) -> None:
    from core.temporal_viz import generate_all_animations

    generate_all_animations(langs, modes)


def cmd_report(langs: list[str], modes: list[str]) -> None:
    from core.report import generate_report

    for lang in langs:
        out = generate_report(lang, modes)
        print(f"[report] {out}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("subcommand", choices=["build", "compare", "figures", "animate", "report", "all"])
    parser.add_argument("--mode", choices=["temporal", "regression", "both"], default="both")
    parser.add_argument(
        "--lang",
        default="all",
        help="código de lengua (du, ee, ... ch_t), varios separados por coma, o 'all'.",
    )
    args = parser.parse_args()
    modes = _modes(args.mode)
    langs = _langs(args.lang)

    if args.subcommand in ("build", "all"):
        cmd_build(langs, modes)
    if args.subcommand in ("compare", "all"):
        cmd_compare(langs, modes)
    if args.subcommand in ("figures", "all"):
        cmd_figures(langs, modes)
    if args.subcommand == "animate":
        cmd_animate(langs, modes)
    if args.subcommand in ("report", "all"):
        cmd_report(langs, modes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
