"""
networks/word-type-transitions/core/data_io.py

Carga de fijaciones (dur incluida), accuracy de comprensión, benchmarks de
tipificación y mapeo itemid→texto.

Fuentes:
- L1 nativo wave 1 (12 lenguas): `joint_l1_fixation_report_2.1.rda` → export R
  con cache CSV. La identidad del texto es `itemid`, mapeada a índice de texto
  1..12 con los CSV `itemid_to_text_<lang>.csv` generados por
  `scripts/classify_words_l1_all_languages.py` (ee/ru rotan orden; el resto es
  identidad).
- L1 nativo wave 2: chino (ch_s/ch_t) + 14 variantes (`W2_VARIANTS`) desde
  `joint_fix_trimmed_l1_wave2_version2.1.rda` → export cache `l1_wave2_fix.csv`.
  Chino: itemid == trialid. Variantes: `itemid` mapeado con
  `l1_tokens_w2/itemid_to_text_<code>.csv` (ic y en_uk rotan orden).
  NOTA: los cohortes noruego/turco wave 2 aparecen como lang "no"/"tr" en los
  datos crudos (alias DATA_LANG_ALIAS -> grupos no_w2/tr_w2).
- L2 inglés wave 1 (12 lenguas) y wave 2 (chino + variantes): CSVs
  `*.comprehension.clean.csv` (incluyen `dur`, `ianum` = IA del texto inglés,
  `type`, `blink`).
- Accuracy: L1 `joint_l1_acc.rda` (w1) / `joint_comp_L1_Wave2_trimmed.rda` (w2);
  L2 `joint.comp.l2.csv` (w1) / `joint_comp_L2_Wave2_trimmed.csv` (w2).
- Benchmarks: L1 alfabético `words_classified_<lang>_l1.csv` (trialid=índice de
  texto, wordnum); chino wave 2 `words_classified_chinese_*_wave2.csv`;
  variantes wave 2 `words_classified_<code>_w2l1.csv`;
  L2 `words_classified.csv` (trialid, ianum).
"""

from __future__ import annotations

import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd

from .label_map import map_label
from .paths import (
    CH_BENCH,
    CH_VARIANTS,
    ITEM_MAP_DIR,
    ITEM_MAP_DIR_W2,
    L1_ACC_EXPORT,
    L1_BENCH,
    L1_FIX_EXPORT_DIR,
    L1_W1_ACC_RDA,
    L1_W1_FIX_RDA,
    L1_W2_ACC_RDA,
    L1_W2_BENCH,
    L1_W2_FIX_RDA,
    L2_BENCH,
    L2_W1_ACC_CSV,
    L2_W1_FIX_CSV,
    L2_W2_ACC_CSV,
    L2_W2_FIX_CSV,
    W2_DATA_CODES,
    W2_VARIANTS,
    data_lang,
    l1_wave,
    l2_wave,
)

FIX_COLS = ["lang", "trialid", "itemid", "uniform_id", "fixid", "start", "dur", "wordnum", "blink", "type"]


# ---------------------------------------------------------------------------
# Exportaciones R (fijaciones L1 y accuracy L1) con cache CSV
# ---------------------------------------------------------------------------

def _run_r(code: str, cache: Path, marker: str) -> None:
    cache.mkdir(parents=True, exist_ok=True)
    if (cache / marker).exists():
        return
    res = subprocess.run(["Rscript", "-e", code], capture_output=True, text=True, timeout=1200)
    if not (cache / marker).exists():
        raise RuntimeError(f"Exportación R falló:\n{res.stdout}\n{res.stderr}")


def ensure_l1_exports() -> None:
    """Exporta fijaciones L1 (dur incluida) y accuracy L1 a CSVs de cache."""
    w1_csv = L1_FIX_EXPORT_DIR / "l1_wave1_fix.csv"
    code_w1 = f"""
e <- new.env()
load({str(L1_W1_FIX_RDA)!r}, envir=e)
d <- get("joint.fix", envir=e)
cols <- c({", ".join(repr(c) for c in FIX_COLS)})
d <- d[!is.na(d$wordnum), cols]
write.csv(d, {str(w1_csv)!r}, row.names=FALSE, fileEncoding="UTF-8")
acc_e <- new.env()
load({str(L1_W1_ACC_RDA)!r}, envir=acc_e)
acc <- get("joint.acc", envir=acc_e)
write.csv(acc, {str(L1_ACC_EXPORT["wave1"])!r}, row.names=FALSE, fileEncoding="UTF-8")
cat("exported\\n")
"""
    _run_r(code_w1, L1_FIX_EXPORT_DIR, "l1_wave1_fix.csv")

    # Wave 2: chino + TODAS las variantes (grupos separados, sin fusiones)
    w2_csv = L1_FIX_EXPORT_DIR / "l1_wave2_fix.csv"
    w2_codes = ", ".join(repr(c) for c in W2_DATA_CODES)
    code_w2 = f"""
e <- new.env()
load({str(L1_W2_FIX_RDA)!r}, envir=e)
d <- get("joint.fix", envir=e)
cols <- c({", ".join(repr(c) for c in FIX_COLS)})
d <- d[d$lang %in% c({w2_codes}) & !is.na(d$wordnum), cols]
write.csv(d, {str(w2_csv)!r}, row.names=FALSE, fileEncoding="UTF-8")
acc_e <- new.env()
load({str(L1_W2_ACC_RDA)!r}, envir=acc_e)
acc <- get(ls(acc_e)[1], envir=acc_e)
write.csv(acc, {str(L1_ACC_EXPORT["wave2"])!r}, row.names=FALSE, fileEncoding="UTF-8")
cat("exported\\n")
"""
    _run_r(code_w2, L1_FIX_EXPORT_DIR, "l1_wave2_fix.csv")


# ---------------------------------------------------------------------------
# Mapeo itemid -> índice de texto (L1 wave 1; chino wave 2 = identidad)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=None)
def itemid_to_text(lang: str) -> Dict[int, int]:
    if lang in CH_VARIANTS:
        return {i: i for i in range(1, 13)}
    mdir = ITEM_MAP_DIR_W2 if lang in W2_VARIANTS else ITEM_MAP_DIR
    df = pd.read_csv(mdir / f"itemid_to_text_{lang}.csv")
    return {int(r["itemid"]): int(r["text_index"]) for _, r in df.iterrows()}


# ---------------------------------------------------------------------------
# Fijaciones
# ---------------------------------------------------------------------------

def _clean_fix(df: pd.DataFrame, wordnum_col: str = "wordnum") -> pd.DataFrame:
    df = df[df["type"] == "in"].copy()
    df = df.dropna(subset=[wordnum_col, "uniform_id"])
    df[wordnum_col] = df[wordnum_col].astype(int)
    df["blink"] = df["blink"].fillna(0).astype(int)
    df["dur"] = df["dur"].astype(float)
    df["start"] = df["start"].astype(float)
    return df


# ---------------------------------------------------------------------------
# Caches de lectura cruda (los CSV L2 son 400-535 MB: leer UNA vez por wave)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _raw_l1_w1() -> pd.DataFrame:
    df = pd.read_csv(
        L1_FIX_EXPORT_DIR / "l1_wave1_fix.csv",
        usecols=["lang", "itemid", "uniform_id", "fixid", "start", "dur", "wordnum", "blink", "type"],
        low_memory=False,
    )
    return df


@lru_cache(maxsize=1)
def _raw_l1_w2() -> pd.DataFrame:
    return pd.read_csv(
        L1_FIX_EXPORT_DIR / "l1_wave2_fix.csv",
        usecols=["lang", "trialid", "itemid", "uniform_id", "fixid", "start", "dur", "wordnum", "blink", "type"],
        low_memory=False,
    )


@lru_cache(maxsize=1)
def _raw_l2(wave: int) -> pd.DataFrame:
    src = L2_W1_FIX_CSV if wave == 1 else L2_W2_FIX_CSV
    df = pd.read_csv(
        src,
        usecols=["lang", "trialid", "uniform_id", "fixid", "start", "dur", "ianum", "blink", "type"],
        low_memory=False,
    )
    if wave == 2:
        df = df[df["lang"].isin(W2_DATA_CODES)].copy()
    return df


def load_fixations(session: str, lang: str) -> pd.DataFrame:
    """
    Fijaciones 'in' de una sesión (L1 nativo | L2 inglés) para un grupo.
    Retorna columnas: uniform_id, textid (índice de texto 1..12), fixid, start,
    dur, wordnum (IA dentro del texto), blink. Ordenadas temporalmente.
    """
    ensure_l1_exports()
    if session == "L1":
        if l1_wave(lang) == 1:
            raw = _raw_l1_w1()
            raw = raw[raw["lang"] == lang]
            imap = itemid_to_text(lang)
            raw = raw[raw["itemid"].isin(imap)]
            raw = _clean_fix(raw)
            raw["textid"] = raw["itemid"].map(imap)
        else:
            raw = _raw_l1_w2()
            raw = raw[raw["lang"] == data_lang(lang)]
            if lang in CH_VARIANTS:
                # chino wave 2: itemid == trialid (12 textos, sin rotación)
                raw = _clean_fix(raw)
                raw["textid"] = raw["trialid"].astype(int)
            else:
                imap = itemid_to_text(lang)
                raw = raw[raw["itemid"].isin(imap)]
                raw = _clean_fix(raw)
                raw["textid"] = raw["itemid"].map(imap)
    else:
        raw = _raw_l2(l2_wave(lang))
        raw = raw[raw["lang"] == data_lang(lang)]
        raw = _clean_fix(raw, wordnum_col="ianum")
        raw = raw.rename(columns={"ianum": "wordnum"})
        raw["textid"] = raw["trialid"].astype(int)

    return raw[["uniform_id", "textid", "fixid", "start", "dur", "wordnum", "blink"]].sort_values(
        ["uniform_id", "textid", "start", "fixid"]
    )


# ---------------------------------------------------------------------------
# Accuracy de comprensión
# ---------------------------------------------------------------------------

def load_accuracy(session: str, lang: str) -> pd.Series:
    """accuracy por uniform_id (minúsculas) para el grupo `lang` en la sesión dada."""
    ensure_l1_exports()
    dl = data_lang(lang)
    if session == "L1":
        src = L1_ACC_EXPORT["wave1"] if l1_wave(lang) == 1 else L1_ACC_EXPORT["wave2"]
        df = pd.read_csv(src, usecols=["lang", "uniform_id", "accuracy"])
    else:
        src = L2_W1_ACC_CSV if l2_wave(lang) == 1 else L2_W2_ACC_CSV
        df = pd.read_csv(src, usecols=["lang", "uniform_id", "accuracy"])
    df = df[df["lang"] == dl].copy()
    df["uniform_id"] = df["uniform_id"].astype(str).str.strip().str.lower()
    # Algunos sujetos tienen filas duplicadas en los accuracy (ej. ch_t_43,
    # sp_ch_1 en wave 2): se promedian para garantizar índice único.
    return df.groupby("uniform_id", sort=True)["accuracy"].mean().astype(float)


# ---------------------------------------------------------------------------
# Benchmarks de tipos
# ---------------------------------------------------------------------------

@lru_cache(maxsize=None)
def load_type_map(session: str, lang: str) -> Dict[Tuple[int, int], str]:
    """Mapa (textid, wordnum) -> nodo fused."""
    if session == "L1":
        if lang in CH_VARIANTS:
            bench = CH_BENCH[lang]
        elif lang in W2_VARIANTS:
            bench = L1_W2_BENCH[lang]
        else:
            bench = L1_BENCH[lang]
        df = pd.read_csv(bench, usecols=["trialid", "wordnum", "pos_tag_universal"])
        key = "wordnum"
    else:
        df = pd.read_csv(L2_BENCH, usecols=["trialid", "ianum", "pos_tag_universal"])
        key = "ianum"
    out = {}
    for _, r in df.iterrows():
        lab = map_label(r["pos_tag_universal"])
        if lab is not None:
            out[(int(r["trialid"]), int(r[key]))] = lab
    return out
