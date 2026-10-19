"""
networks/reading-pattern-mds/core/lingdistance.py

Distancia lingüística al inglés (repo: lang_to_en.csv, porcentajes 0-100,
raíz del proyecto) mapeada a los códigos de grupo del diseño, y relación
con la distancia de lectura (J-S a los cohortes nativos):

- load_distances()     -> {group_code: ling_distance}
- save_table(mode)     -> distances/lang_linguistic_distance.csv
- correlations(mode)   -> distances/corr_linguistic_reading.csv
  (Pearson r/p + Spearman ρ/p por sesión {L1, L2} × cuartil {all, Q1, Q4},
  y agregado de cohortes mean|en_ca|en_uk)
"""

from __future__ import annotations

import pandas as pd

from . import paths, profiles  # profiles reutiliza el bootstrap del core wtt

REPO_ROOT = paths.REPO_ROOT
LING_CSV = REPO_ROOT / "lang_to_en.csv"

# fila de lang_to_en.csv (minúscula) -> códigos de grupo del diseño
_ROW_TO_GROUPS: dict[str, list[str]] = {
    "du": ["du"],
    "da": ["da"],
    "no": ["no", "no_w2"],
    "ge": ["ge", "ge_po", "ge_zu"],
    "ic": ["ic"],
    "it": ["it"],
    "ru": ["ru", "ru_mo"],
    "se": ["se"],
    "bp": ["bp"],
    "sp": ["sp", "sp_ch"],
    "hi": ["hi_iiith", "hi_iitk"],
    "gr": ["gr"],
    "ee": ["ee"],
    "fi": ["fi"],
    "ch": ["ch_s", "ch_t"],
    "he": ["he"],
    "tr": ["tr", "tr_w2"],
    "ba": ["ba"],
    "kr": [],  # koreano: sin grupo (excluido del diseño)
}


def load_distances() -> dict[str, float]:
    """{group_code: distancia lingüística} para todos los grupos con fila mapeada."""
    df = pd.read_csv(LING_CSV)
    out: dict[str, float] = {}
    for _, r in df.iterrows():
        key = str(r["lang"]).strip().lower()
        groups = _ROW_TO_GROUPS.get(key)
        if groups is None:
            raise KeyError(f"lang_to_en.csv: fila '{r['lang']}' sin mapeo a grupos")
        for g in groups:
            out[g] = float(r["distance"])
    missing = [g for g in paths.target_langs() if g not in out]
    if missing:
        raise KeyError(f"grupos sin distancia lingüística: {missing}")
    return out


def save_table(mode: str) -> pd.DataFrame:
    dist = load_distances()
    df = pd.DataFrame(
        {"group": sorted(dist), "ling_distance": [dist[g] for g in sorted(dist)]}
    )
    out = paths.distances_dir(mode) / "lang_linguistic_distance.csv"
    df.to_csv(out, index=False)
    return df


def _read_native_distances(mode: str) -> pd.DataFrame:
    df = pd.read_csv(paths.distances_dir(mode) / "distance_to_native.csv")
    df = df[df["lang"] != "en"]  # en/es refs por si acaso (target langs only table inputs)
    df = df[~df["lang"].isin(paths.EN_REFS.values())]
    df["jsd_mean"] = df[[c for c in ("jsd_en_ca", "jsd_en_uk") if c in df.columns]].mean(axis=1)
    ling = load_distances()
    df["ling_distance"] = df["lang"].map(ling)
    return df.dropna(subset=["ling_distance", "jsd_mean"])


def correlations(mode: str) -> pd.DataFrame:
    """
    Correlación distancia lingüística ↔ distancia de lectura (J-S a nativos).
    Una fila por (session, quartile, aggregate); retorna tabla y la guarda.
    """
    from scipy import stats

    df = _read_native_distances(mode)
    rows = []
    for session in ("L1", "L2"):
        for quartile in ("all", "Q1", "Q4"):
            sub = df[(df["session"] == session) & (df["quartile"] == quartile)]
            if len(sub) < 5:
                continue
            x = sub["ling_distance"]
            for agg in ("mean", "en_ca", "en_uk"):
                ycol = "jsd_mean" if agg == "mean" else f"jsd_{agg}"
                if ycol not in sub.columns:
                    continue
                y = sub[ycol]
                pr, pp = stats.pearsonr(x, y)
                sr, sp = stats.spearmanr(x, y)
                rows.append(
                    {
                        "session": session,
                        "quartile": quartile,
                        "aggregate": agg,
                        "n": len(sub),
                        "pearson_r": round(float(pr), 4),
                        "pearson_p": round(float(pp), 4),
                        "spearman_rho": round(float(sr), 4),
                        "spearman_p": round(float(sp), 4),
                    }
                )
    out = pd.DataFrame(rows)
    paths.ensure_dirs(mode)
    out.to_csv(paths.distances_dir(mode) / "corr_linguistic_reading.csv", index=False)
    return out
