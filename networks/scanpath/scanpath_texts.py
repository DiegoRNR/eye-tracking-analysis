"""
scanpath_texts.py

Redes de scanpath POR TEXTO (sesión L2 inglés), por grupo lingüístico y
cuartil de comprensión lectora (Q1 peor / Q4 mejor, misma división que
word-type-transitions). Para cada texto (trialid 1-12) genera:

- network/<tN>.html         red estática (pyvis, layout de lectura fijo)
- network_anim/<tN>.html    red animada (reveal-once, scrubber)
- network.html / network_anim.html   wrappers con iframes

en networks/scanpath/output/<lang>/<Q1|Q4>/.

Uso:
  python scanpath_texts.py --lang du
  python scanpath_texts.py --lang du,ee --trialid 1,5
  python scanpath_texts.py --lang all
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core import (
    CONDITION_LANGS,
    MIN_GROUP_N,
    QUARTILES,
    TEXTS,
    build_text_network,
    load_l2_accuracy,
    load_l2_fixations,
    network_anim_dir,
    network_dir,
    quartile_dir,
    quartile_groups,
    write_anim_wrapper,
    write_static_wrapper,
    write_text_network_anim,
    write_text_network_static,
)


def _langs(arg: str) -> list[str]:
    if arg == "all":
        return list(CONDITION_LANGS)
    sel = [s.strip() for s in arg.split(",") if s.strip()]
    valid = set(CONDITION_LANGS)
    bad = [s for s in sel if s not in valid]
    if bad:
        sys.exit(f"[error] lenguas desconocidas: {bad}. Válidas: {CONDITION_LANGS}")
    return sel


def _texts(arg: str) -> list[int]:
    if arg == "all":
        return list(TEXTS)
    try:
        sel = sorted({int(s) for s in arg.split(",") if s.strip()})
    except ValueError:
        sys.exit("[error] --trialid debe ser 'all' o enteros separados por coma (1-12)")
    bad = [t for t in sel if t not in TEXTS]
    if bad:
        sys.exit(f"[error] textos fuera de rango: {bad}. Válidos: 1-12")
    return sel


def _quartiles(arg: str) -> list[str]:
    if arg == "both":
        return list(QUARTILES)
    q = arg.upper()
    if q not in QUARTILES:
        sys.exit(f"[error] --quartile debe ser both, q1 o q4")
    return [q]


def process_lang(lang: str, texts: list[int], quartiles: list[str]) -> bool:
    """Procesa una lengua; retorna True si generó salidas."""
    t0 = time.time()
    acc = load_l2_accuracy(lang)
    groups, gsum = quartile_groups(acc, min_n=MIN_GROUP_N)
    if not gsum.get("split"):
        print(
            f"[scanpath] {lang}: cuartiles no disponibles "
            f"(n_total={gsum.get('n_total', 0)}, Q1={gsum.get('n_Q1', 0)}, "
            f"Q4={gsum.get('n_Q4', 0)}; mínimo {MIN_GROUP_N} por celda) — omitido"
        )
        return False

    print(f"[scanpath] === {lang} === Q1={gsum['n_Q1']} · Q4={gsum['n_Q4']} "
          f"(acc {gsum['q25']:.3f} / {gsum['q75']:.3f})")
    fix_all = load_l2_fixations(lang)
    generated = False

    for quartile in quartiles:
        subjects = {u for u, g in groups.items() if g == quartile}
        fix_q = fix_all[fix_all["uniform_id"].isin(subjects)]
        if fix_q.empty:
            print(f"[scanpath] {lang} {quartile}: sin fijaciones — omitido")
            continue

        cells_static, cells_anim = [], []
        network_dir(lang, quartile).mkdir(parents=True, exist_ok=True)
        network_anim_dir(lang, quartile).mkdir(parents=True, exist_ok=True)
        for tn in texts:
            fix_t = fix_q[fix_q["textid"] == tn]
            if fix_t.empty:
                continue
            res = build_text_network(fix_t, text_label=f"scanpath_{lang}_{quartile}_t{tn}")
            G = res["G"]
            if G.number_of_nodes() == 0:
                continue
            title = f"Texto {tn} — {lang} · {quartile} (n={res['n_subjects']})"

            out_s = write_text_network_static(
                G, network_dir(lang, quartile) / f"t{tn}.html", title
            )
            out_a = write_text_network_anim(
                G, network_anim_dir(lang, quartile) / f"t{tn}.html", title
            )
            cells_static.append((f"t{tn}", f"Texto {tn} (n={res['n_subjects']})"))
            cells_anim.append((f"t{tn}", f"Texto {tn} (n={res['n_subjects']})"))
            print(
                f"[scanpath] {lang} {quartile} t{tn}: "
                f"{G.number_of_nodes()} palabras, {G.number_of_edges()} aristas, "
                f"{res['n_transitions']} transiciones"
            )

        if cells_static:
            write_static_wrapper(
                lang, quartile, "network", cells_static,
                quartile_dir(lang, quartile) / "network.html",
            )
            write_anim_wrapper(
                lang, quartile, cells_anim,
                quartile_dir(lang, quartile) / "network_anim.html",
            )
            print(
                f"[scanpath] {lang} {quartile}: {len(cells_static)} textos → "
                f"{quartile_dir(lang, quartile) / 'network.html'} + network_anim.html"
            )
            generated = True

    print(f"[scanpath] {lang}: {time.time() - t0:.1f}s")
    return generated


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Redes de scanpath por texto (L2) — estáticas y animadas."
    )
    parser.add_argument(
        "--lang", default="du",
        help="código de grupo L1 (du, ee, ... ch_t), varios por coma, o 'all'.",
    )
    parser.add_argument(
        "--trialid", default="all", help="'all' o textos separados por coma (1-12)."
    )
    parser.add_argument(
        "--quartile", default="both", choices=["both", "q1", "q4"],
        help="cuartil(es) a procesar (default: both).",
    )
    args = parser.parse_args(argv)

    langs = _langs(args.lang)
    texts = _texts(args.trialid)
    quartiles = _quartiles(args.quartile)

    ok = 0
    for lang in langs:
        if process_lang(lang, texts, quartiles):
            ok += 1
    print(f"[scanpath] listo: {ok}/{len(langs)} lengua(s) con salidas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
