"""
data_io.py

Carga de fijaciones para la red de regresiones.

Diferencia crítica con `language-comparison/core/data_io.py`: aquí **no se
filtran las fijaciones por `ps`**. La red de regresiones se construye sobre el
scanpath, y descartar una fijación por no tener pupila válida rompería la
cadena temporal, inventando una transición directa entre las dos fijaciones
que la rodean. `ps` se conserva como atributo opcional.

Consecuencia: grupos sin datos de pupila (p.ej. `ch_s`, chino de Singapur en
wave 2) sí pueden analizarse con esta red.
"""

import os
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

from ._langcomp import get_langcomp_core

# Nombres originales en el CSV -> nombre interno seguro (sin puntos).
_COLUMN_MAP = {
    "uniform_id": "uniform_id",
    "subid": "subid",
    "lang": "lang",
    "trialid": "trialid",
    "fixid": "fixid",
    "start": "start",
    "dur": "dur",
    "wordnum": "wordnum",
    "word": "word",
    "ianum": "ianum",
    "ia": "ia",
    "sentnum": "sentnum",
    "ps": "ps",
    "word.reg.out": "meco_reg_out",
    "word.reg.out.to": "meco_reg_to",
    "word.run": "run",
    "word.firstskip": "firstskip",
}

# Valores que MECO usa para "sin identificador" en uniform_id / subid.
_MISSING_IDS = {"", "NA", "nan", "NaN", "None", "<NA>"}

_NUMERIC = [
    "fixid",
    "start",
    "dur",
    "wordnum",
    "ianum",
    "sentnum",
    "ps",
    "meco_reg_out",
    "meco_reg_to",
    "run",
    "firstskip",
]


def load_scanpath_fixations(wave, langs, trialid):
    """
    Carga las fijaciones de `trialid` para los códigos L1 en `langs`.

    Retorna (fixations, source_files):
      fixations: lista de dicts con `start`, para reconstruir el scanpath en
                 orden temporal.
      source_files: rutas de los CSVs usados.

    No aplica ningún filtro sobre `ps`.
    """
    get_langcomp_core()
    from langcomp_core.paths import resolve_fixation_paths, wave_of_path

    paths = resolve_fixation_paths(wave)
    langs = set(langs)
    frames = []

    for path in paths:
        if not os.path.exists(path):
            raise FileNotFoundError(f"No se encontró el archivo: {path}")
        print(f"--> Cargando fijaciones desde: {path}")
        df = pd.read_csv(
            path,
            usecols=lambda c: c in _COLUMN_MAP,
            low_memory=False,
        ).rename(columns=_COLUMN_MAP)

        for col in _COLUMN_MAP.values():
            if col not in df.columns:
                df[col] = np.nan

        df["trialid"] = df["trialid"].astype(str).str.strip()
        df = df[df["trialid"] == str(trialid)]
        df = df[df["lang"].isin(langs)]
        if df.empty:
            continue

        for col in _NUMERIC:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # OJO: pandas puede leer estas columnas con dtype `str` nullable, donde
        # un valor ausente es pd.NA y NO la cadena 'nan'. Comparar con .ne()
        # devuelve NA (no False), y `.where` conservaría el NA en lugar de caer
        # a `subid`. Eso fusionaría en una sola sesión a todos los
        # participantes sin uniform_id (17 daneses en wave 2), concatenando sus
        # scanpaths e inventando regresiones enormes en la costura.
        uid = df["uniform_id"].astype("string").str.strip()
        sub = df["subid"].astype("string").str.strip()
        has_uid = (uid.notna() & ~uid.isin(_MISSING_IDS)).fillna(False)
        has_sub = (sub.notna() & ~sub.isin(_MISSING_IDS)).fillna(False)

        df["has_uniform_id"] = has_uid.astype(bool)
        session = uid.where(has_uid, sub)
        df["session_id"] = session.astype(object).where(has_uid | has_sub, None)

        unusable = int(df["session_id"].isna().sum())
        if unusable:
            print(
                f"[!] {unusable} fijación(es) sin uniform_id ni subid utilizables; "
                f"se descartan (no son atribuibles a un participante)."
            )
            df = df[df["session_id"].notna()]

        text = df["word"].astype(str).str.strip()
        alt = df["ia"].astype(str).str.strip()
        df["word_text"] = text.where(text.ne("") & text.ne("nan"), alt)

        df = df.dropna(subset=["wordnum", "start"])
        df = df[df["wordnum"] >= 0]
        df["wave"] = wave_of_path(path)
        frames.append(df)

    if not frames:
        print("[!] No se cargó ninguna fijación con esos filtros.")
        return [], paths

    all_df = pd.concat(frames, ignore_index=True)
    print(f"--> Total de fijaciones cargadas: {len(all_df)}")

    keep = [
        "session_id", "has_uniform_id", "lang", "trialid", "wave", "fixid",
        "start", "dur", "wordnum", "ianum", "word_text", "sentnum", "ps",
        "meco_reg_out", "meco_reg_to", "run", "firstskip",
    ]
    records = all_df[keep].to_dict("records")

    fixations = []
    for r in records:
        fixations.append(
            {
                "session_id": r["session_id"],
                "has_uniform_id": bool(r["has_uniform_id"]),
                "lang": r["lang"],
                "trialid": str(r["trialid"]),
                "wave": int(r["wave"]),
                "fixid": _int_or(r["fixid"], -1),
                "start": float(r["start"]),
                "dur": _float_or(r["dur"], 0.0),
                "wordnum": int(r["wordnum"]),
                "ianum": _int_or(r["ianum"], int(r["wordnum"])),
                "word": r["word_text"],
                "sentnum": _int_or(r["sentnum"], 1),
                "ps": None if pd.isna(r["ps"]) else float(r["ps"]),
                "meco_reg_out": _int_or_none(r["meco_reg_out"]),
                "meco_reg_to": _int_or_none(r["meco_reg_to"]),
                "run": _int_or_none(r["run"]),
                "firstskip": _int_or_none(r["firstskip"]),
            }
        )
    return fixations, paths


def _int_or(value, default):
    return default if pd.isna(value) else int(value)


def _float_or(value, default):
    return default if pd.isna(value) else float(value)


def _int_or_none(value):
    return None if pd.isna(value) else int(value)


def filter_discordant_sessions(fixations):
    """
    Descarta las sesiones cuyo `max(ianum)` **supera** la moda del trial.

    Corrige el defecto documentado en la auditoría de language-comparison:
    `bp_23` y `se_38` tienen trialid=4 apuntando a un pasaje de 187 palabras,
    lo que mezclaba dos textos distintos en una sola red.

    Solo se descarta por exceso, nunca por defecto: un `max(ianum)` menor que
    la moda significa que ese lector no fijó las últimas palabras del pasaje
    (140 o 141 de 142 es habitual), no que haya leído otro texto.

    Retorna (fixations_filtradas, sesiones_descartadas).
    """
    max_ianum = defaultdict(int)
    for f in fixations:
        sid = f["session_id"]
        if f["ianum"] > max_ianum[sid]:
            max_ianum[sid] = f["ianum"]

    if not max_ianum:
        return fixations, []

    modal = Counter(max_ianum.values()).most_common(1)[0][0]
    discarded = sorted(sid for sid, m in max_ianum.items() if m > modal)

    if discarded:
        print(
            f"--> Filtro de texto discordante: moda de max(ianum) = {modal}; "
            f"{len(discarded)} sesión(es) descartada(s) por leer un pasaje más "
            f"largo: {', '.join(discarded)}"
        )
        drop = set(discarded)
        fixations = [f for f in fixations if f["session_id"] not in drop]

    return fixations, discarded


def load_accuracy_for(wave, langs):
    """Reutiliza la carga de comprensión global de language-comparison."""
    lc = get_langcomp_core()
    return lc.load_accuracy(wave, langs)


def summarize_accuracy_for(acc_map, session_ids):
    """
    Resume `accuracy` sobre las sesiones presentes en la red.

    Retorna (resumen, n_participants, n_with_accuracy).
    """
    session_ids = list(session_ids)
    with_acc = {sid: acc_map[sid] for sid in session_ids if sid in acc_map}
    if not with_acc:
        return (
            {"mean": None, "median": None, "std": None,
             "min": None, "max": None, "n": 0},
            len(session_ids),
            0,
        )
    vals = np.array([v["accuracy"] for v in with_acc.values()], dtype=float)
    return (
        {
            "mean": round(float(np.mean(vals)), 4),
            "median": round(float(np.median(vals)), 4),
            "std": round(float(np.std(vals, ddof=0)), 4),
            "min": round(float(np.min(vals)), 4),
            "max": round(float(np.max(vals)), 4),
            "n": int(len(vals)),
        },
        len(session_ids),
        len(with_acc),
    )
