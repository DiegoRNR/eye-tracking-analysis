"""
networks/scanpath/core/data_io.py

Carga de fijaciones L2 (inglés) con texto de palabra, ps y sentnum desde los
CSVs limpios de comprensión, y accuracy de comprensión → cuartiles Q1/Q4
(misma convención que word-type-transitions: p25/p75, min 4 sujetos por celda).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Dict, Tuple

import pandas as pd

from .paths import (
    MIN_GROUP_N,
    W2_DATA_CODES,
    data_lang,
    l2_acc_csv,
    l2_fix_csv_for_wave,
    l2_wave,
)

FIX_USECOLS = [
    "lang", "uniform_id", "trialid", "fixid", "start", "dur", "ps",
    "type", "blink", "wordnum", "word", "sentnum",
]


# ---------------------------------------------------------------------------
# Fijaciones L2
# ---------------------------------------------------------------------------

@lru_cache(maxsize=2)
def _raw_l2(wave: int) -> pd.DataFrame:
    df = pd.read_csv(l2_fix_csv_for_wave(wave), usecols=FIX_USECOLS, low_memory=False)
    if wave == 2:
        df = df[df["lang"].isin(W2_DATA_CODES)].copy()
    return df


def load_l2_fixations(lang: str) -> pd.DataFrame:
    """
    Fijaciones 'in' de la sesión L2 (inglés) para el grupo `lang`.
    Retorna columnas: uniform_id, textid (trialid 1..12), fixid, start, dur,
    ps, wordnum, word, sentnum, blink. Ordenadas por (uniform_id, textid,
    start, fixid). Blink queda como columna (corta secuencias en el builder).
    """
    wave = l2_wave(lang)
    raw = _raw_l2(wave)
    raw = raw[raw["lang"] == data_lang(lang)].copy()
    raw = raw[raw["type"] == "in"].copy()
    raw = raw.dropna(subset=["uniform_id", "wordnum", "word"])
    raw["uniform_id"] = raw["uniform_id"].astype(str).str.strip().str.lower()
    raw["textid"] = raw["trialid"].astype(int)
    raw["wordnum"] = raw["wordnum"].astype(int)
    raw["fixid"] = raw["fixid"].astype(int)
    raw["start"] = raw["start"].astype(float)
    raw["dur"] = raw["dur"].astype(float)
    raw["ps"] = pd.to_numeric(raw["ps"], errors="coerce").fillna(0.0).astype(float)
    raw["sentnum"] = pd.to_numeric(raw["sentnum"], errors="coerce").fillna(1).astype(int)
    raw["blink"] = raw["blink"].fillna(0).astype(int)
    raw["word"] = raw["word"].astype(str).str.strip()
    cols = ["uniform_id", "textid", "fixid", "start", "dur", "ps", "wordnum", "word", "sentnum", "blink"]
    return raw[cols].sort_values(["uniform_id", "textid", "start", "fixid"])


# ---------------------------------------------------------------------------
# Accuracy y cuartiles
# ---------------------------------------------------------------------------

def load_l2_accuracy(lang: str) -> pd.Series:
    """accuracy por uniform_id (minúsculas) del grupo `lang`, sesión L2."""
    src = l2_acc_csv(lang)
    df = pd.read_csv(src, usecols=["lang", "uniform_id", "accuracy"])
    df = df[df["lang"] == data_lang(lang)].copy()
    df["uniform_id"] = df["uniform_id"].astype(str).str.strip().str.lower()
    return df.groupby("uniform_id", sort=True)["accuracy"].mean().astype(float)


def quartile_groups(accuracy, min_n: int = MIN_GROUP_N) -> Tuple[Dict[str, str], Dict]:
    """
    accuracy: pd.Series uniform_id -> accuracy.
    Retorna ({uniform_id: 'Q1'|'Q4'}, summary) — sujetos del centro → None.
    Q1 = accuracy <= p25 (peor), Q4 = >= p75 (mejor).
    """
    import numpy as np

    acc = pd.Series(accuracy).astype(float).dropna()
    if acc.empty:
        return {}, {"n_total": 0, "split": False}
    q1, q3 = acc.quantile(0.25), acc.quantile(0.75)
    groups: Dict[str, str] = {}
    for u, v in acc.items():
        if v <= q1:
            groups[u] = "Q1"
        elif v >= q3:
            groups[u] = "Q4"
    n_q1 = sum(1 for v in groups.values() if v == "Q1")
    n_q4 = sum(1 for v in groups.values() if v == "Q4")
    summary = {
        "n_total": int(len(acc)),
        "q25": float(q1),
        "q75": float(q3),
        "n_Q1": n_q1,
        "n_Q4": n_q4,
        "split": n_q1 >= min_n and n_q4 >= min_n,
        "acc_mean_Q1": float(acc[[u for u, g in groups.items() if g == "Q1"]].mean()) if n_q1 else None,
        "acc_mean_Q4": float(acc[[u for u, g in groups.items() if g == "Q4"]].mean()) if n_q4 else None,
    }
    return groups, summary
