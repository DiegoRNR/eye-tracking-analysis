"""
networks/word-type-transitions/core/persistence.py

Escritura de salidas CSV y metadata (sha256 de entradas). Estructura
PER LENGUA y PER MODO:

output/
├── metadata.json                                   # global (entradas compartidas)
└── <lang>/                                         # ej. du, ee, ru, ch_s, ch_t
    ├── condition_summary.csv                       # n sujetos y QA por celda/modo
    ├── accuracy_subjects.csv                       # accuracy + quartile por sujeto (L1/L2)
    ├── accuracy_box.png \                          # figuras del modo ...
    │   figures/                                    #   (temporal/)
    ├── REPORT.md                                   # reporte de la lengua
    ├── temporal/
    │   ├── per_participant_<cond>.csv              # sujeto × arista (probabilidades)
    │   ├── transitions_<cond>.csv                  # probabilidades POOLED de grupo
    │   ├── counts_<cond>.csv                       # matriz NxN conteos POOLED
    │   ├── matrix_<cond>.csv                       # matriz NxN probabilidades
    │   ├── node_attributes_<cond>.csv              # mean_dur, dwell_share, n_fix
    │   ├── node_metrics_<cond>.csv                 # pagerank, strengths, densidad
    │   ├── comparison_<contrast>.csv               # test por arista + BH-FDR
    │   └── figures/*.png                           # suite de figuras del modo
    └── regression/                                 # idem temporal/
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .paths import (
    BENCH_DIR,
    CH_BENCH,
    ITEM_MAP_DIR,
    ITEM_MAP_DIR_W2,
    L1_BENCH,
    L1_FIX_EXPORT_DIR,
    L1_W2_BENCH,
    L2_BENCH,
    L2_W1_ACC_CSV,
    L2_W1_FIX_CSV,
    L2_W2_ACC_CSV,
    L2_W2_FIX_CSV,
    OUTPUT_DIR,
    lang_dir,
    mode_dir,
    short_sha,
)


def save_accuracy_subjects(lang: str, rows: list[dict]) -> None:
    """Guarda accuracy + cuartil por sujeto (L1/L2) para el box plot."""
    out = lang_dir(lang) / "accuracy_subjects.csv"
    pd.DataFrame(rows).to_csv(out, index=False)


def save_condition(cond_id: str, lang: str, mode: str, result: dict) -> None:
    d = mode_dir(lang, mode)
    r = result
    r["per_participant"].to_csv(d / f"per_participant_{cond_id}.csv")
    r["group"].to_csv(d / f"transitions_{cond_id}.csv")
    r["group_matrix"].to_csv(d / f"matrix_{cond_id}.csv")
    r["node_attrs"].to_csv(d / f"node_attributes_{cond_id}.csv")
    counts = r.get("counts_matrix")
    if counts is not None:
        counts.to_csv(d / f"counts_{cond_id}.csv")


def save_node_metrics(lang: str, mode: str, cond_id: str, metrics: pd.DataFrame, density: float) -> None:
    out = metrics.copy()
    out["density"] = density
    out.to_csv(mode_dir(lang, mode) / f"node_metrics_{cond_id}.csv")


def save_comparison(lang: str, mode: str, contrast: str, df: pd.DataFrame) -> Path:
    out = mode_dir(lang, mode) / f"comparison_{contrast}.csv"
    df.to_csv(out, index=False)
    return out


def save_condition_summary(lang: str, rows: list[dict]) -> None:
    pd.DataFrame(rows).to_csv(lang_dir(lang) / "condition_summary.csv", index=False)


def load_condition_summary(lang: str) -> pd.DataFrame:
    p = lang_dir(lang) / "condition_summary.csv"
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p)


def write_metadata() -> None:
    """metadata.json GLOBAL: hashes de entradas compartidas entre lenguas."""
    inputs = {}
    for p in [
        *L1_BENCH.values(),
        *CH_BENCH.values(),
        *L1_W2_BENCH.values(),
        L2_BENCH,
        L2_W1_FIX_CSV,
        L2_W2_FIX_CSV,
        L2_W1_ACC_CSV,
        L2_W2_ACC_CSV,
    ]:
        if p.exists():
            inputs[str(p.relative_to(BENCH_DIR.parents[1]))] = short_sha(p)
    for p in sorted(L1_FIX_EXPORT_DIR.glob("*.csv")) if L1_FIX_EXPORT_DIR.exists() else []:
        inputs[str(p.relative_to(BENCH_DIR.parents[1]))] = short_sha(p)
    for p in sorted(ITEM_MAP_DIR.glob("itemid_to_text_*.csv")):
        inputs[str(p.relative_to(BENCH_DIR.parents[1]))] = short_sha(p)
    for p in sorted(ITEM_MAP_DIR_W2.glob("itemid_to_text_*.csv")):
        inputs[str(p.relative_to(BENCH_DIR.parents[1]))] = short_sha(p)
    with open(OUTPUT_DIR / "metadata.json", "w", encoding="utf-8") as f:
        json.dump({"network": "word-type-transitions", "inputs_sha256_16": inputs}, f, indent=2)


def inputs_ready() -> bool:
    """True si los caches/exportaciones ya existen (para no repetir R)."""
    return L1_FIX_EXPORT_DIR.exists() and (L1_FIX_EXPORT_DIR / "l1_wave1_fix.csv").exists()
