"""
networks/reading-pattern-mds/core/app.py

Orquestación:
- build_all(mode): genera perfiles (full + cuartiles) y matrices de distancia.
- figures_all(mode): genera TODAS las variantes de figuras MDS.

Variantes (spec del usuario):
1. L1-vs-nativos y L2-vs-nativos, todos los grupos en un plot por sesión
   (referencias: cohortes en_ca/en_uk de la MISMA sesión).
2. Por lengua, ambas sesiones vs ambas cohortes nativos (plot por lengua,
   6 puntos; distancias J-S anotadas).
3. Repetición de 1 y 2 con división Q1/Q4 (2 marcas por lengua:
   lang-Q1, lang-Q4 + en_*-Q1, en_*-Q4).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd

from . import distances, paths, profiles, viz


def build_all(mode: str) -> dict:
    meta = {"profiles": {}, "mode": mode, "generated": datetime.now(timezone.utc).isoformat()}
    full_df, quart_df = profiles.build_profiles(mode, meta)
    langs = paths.target_langs()

    D_full = distances.pairwise_js_matrix(full_df, list(full_df.index))
    distances.save_distance_matrix(D_full, "full_all", mode)

    D_quart = distances.pairwise_js_matrix(quart_df, list(quart_df.index))
    distances.save_distance_matrix(D_quart, "quartile_all", mode)

    # distancias de cada grupo a los cohortes nativos (misma sesión / mismo cuartil)
    rows = []
    for lang in langs:
        for session in ("L1", "L2"):
            for quart in (None, "Q1", "Q4"):
                base = profiles.condition_name(session, lang, quart)
                src, D = (full_df, D_full) if quart is None else (quart_df, D_quart)
                if base not in src.index:
                    continue
                row = {"lang": lang, "session": session, "quartile": quart or "all"}
                for ref, ref_code in paths.EN_REFS.items():
                    refc = f"{session}-{ref_code}" + (f"-{quart}" if quart else "")
                    if refc in D.columns:
                        row[f"jsd_{ref}"] = round(float(D.loc[base, refc]), 4)
                rows.append(row)
    pd.DataFrame(rows).to_csv(paths.distances_dir(mode) / "distance_to_native.csv", index=False)

    meta["n_profiles_full"] = int(D_full.shape[0])
    meta["n_profiles_quartile"] = int(D_quart.shape[0])
    out = paths.OUTPUT_DIR / "metadata.json"
    out.write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"[build] {out}")
    return meta


def figures_all(mode: str) -> dict:
    meta = {"figures": {}}
    paths.ensure_dirs(mode)
    full_df = pd.read_csv(paths.profiles_dir(mode) / "profiles_full.csv", index_col=0)
    quart_df = pd.read_csv(paths.profiles_dir(mode) / "profiles_quartile.csv", index_col=0)
    D_full = distances.pairwise_js_matrix(full_df, list(full_df.index))
    D_quart = distances.pairwise_js_matrix(quart_df, list(quart_df.index))
    langs = paths.target_langs()
    refs = paths.EN_REFS  # en_ca -> "en", en_uk -> "en_uk"

    def existing(df: pd.DataFrame, conds: list[str]) -> list[str]:
        return [c for c in conds if c in df.index]

    def ref_conds(df, session, quart=None):
        q = f"-{quart}" if quart else ""
        return existing(df, [f"{session}-{refs[r]}{q}" for r in refs])

    emb_rows: list[pd.DataFrame] = []

    # --- variante 1: sesión-matched, todos los grupos -----------------------
    for session, suffix in (("L1", "l1"), ("L2", "l2")):
        conds = (
            existing(full_df, [f"{session}-{lg}" for lg in langs])
            + ref_conds(full_df, session)
        )
        f = paths.figures_dir(mode) / f"{suffix}_vs_native.png"
        s = viz.plot_variant(
            D_full, conds,
            f"{session.upper()} de cada lengua vs lectores nativos (en_ca, en_uk)",
            f, link="sessions", embeddings_out=emb_rows, fig_name=f"{suffix}_vs_native",
        )
        meta["figures"][f.name] = {"stress": s, "n_points": len(conds)}
        print(f"[figures] {f.name} n={len(conds)} stress={s:.3f}")

    # --- variante 2: por lengua, ambas sesiones vs ambas cohortes -----------
    for lang in langs:
        conds = existing(full_df, [
            f"L1-{lang}", f"L2-{lang}",
            f"L1-{refs['en_ca']}", f"L2-{refs['en_ca']}",
            f"L1-{refs['en_uk']}", f"L2-{refs['en_uk']}",
        ])
        if len(conds) < 4:
            print(f"[figures] lang_{lang}: datos insuficientes ({len(conds)} condiciones), skip")
            continue
        f = paths.figures_dir(mode) / f"lang_{lang}.png"
        s = viz.plot_variant(
            D_full, conds,
            f"{paths.fig_label(lang)}: lectura nativa (L1) y en inglés (L2) vs nativos en_ca/en_uk",
            f, link="sessions", annotate_refs_dist=True,
            embeddings_out=emb_rows, fig_name=f"lang_{lang}",
        )
        meta["figures"][f.name] = {"stress": s, "n_points": len(conds)}
        print(f"[figures] {f.name} n={len(conds)} stress={s:.3f}")

    # --- variante 3: cuartiles ---------------------------------------------
    for session, suffix in (("L1", "l1"), ("L2", "l2")):
        conds = existing(quart_df, [f"{session}-{lg}-Q1" for lg in langs])
        conds += existing(quart_df, [f"{session}-{lg}-Q4" for lg in langs])
        conds += ref_conds(quart_df, session, "Q1") + ref_conds(quart_df, session, "Q4")
        f = paths.figures_dir(mode) / f"q_{suffix}_vs_native.png"
        s = viz.plot_variant(
            D_quart, conds,
            f"{session.upper()} por cuartil de comprensión (Q1 peor, Q4 mejor) vs nativos",
            f, link="quartiles", embeddings_out=emb_rows, fig_name=f"q_{suffix}_vs_native",
        )
        meta["figures"][f.name] = {"stress": s, "n_points": len(conds)}
        print(f"[figures] {f.name} n={len(conds)} stress={s:.3f}")

    for lang in langs:
        conds = []
        for session in ("L1", "L2"):
            conds += existing(quart_df, [f"{session}-{lang}-Q1", f"{session}-{lang}-Q4"])
            conds += ref_conds(quart_df, session, "Q1") + ref_conds(quart_df, session, "Q4")
        conds = list(dict.fromkeys(conds))
        if len(conds) < 8:
            print(f"[figures] q_lang_{lang}: datos insuficientes ({len(conds)}), skip")
            continue
        f = paths.figures_dir(mode) / f"q_lang_{lang}.png"
        s = viz.plot_variant(
            D_quart, conds,
            f"{paths.fig_label(lang)} por cuartil vs nativos (mismo tipo de sesión)",
            f, link="quartiles", annotate_refs_dist=True,
            embeddings_out=emb_rows, fig_name=f"q_lang_{lang}",
        )
        meta["figures"][f.name] = {"stress": s, "n_points": len(conds)}
        print(f"[figures] {f.name} n={len(conds)} stress={s:.3f}")

    if emb_rows:
        pd.concat(emb_rows, ignore_index=True).to_csv(
            paths.distances_dir(mode) / "embeddings.csv", index=False
        )
    meta["generated"] = datetime.now(timezone.utc).isoformat()
    meta_path = paths.OUTPUT_DIR / "figures_metadata.json"
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    return meta
