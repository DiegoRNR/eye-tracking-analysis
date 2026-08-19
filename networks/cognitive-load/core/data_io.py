"""
data_io.py

Carga y filtrado de fijaciones desde los CSV preprocesados (.clean.csv)
de MECO L2, y normalización intra-sesión de PS (z-score o robust z-score).
"""

import csv
import os
from collections import defaultdict

import numpy as np
from scipy.stats import median_abs_deviation

from .paths import resolve_wave_paths


def load_fixations(filepath, wave, uniform_id=None, lang=None, trialid=None, itemid=None):
    """
    Carga y filtra las fijaciones del CSV preprocesado (.clean.csv).

    Solo carga filas donde ps > 0 (ya garantizado por preprocesamiento).
    Retorna una lista de diccionarios con los campos necesarios para
    construir la red de carga cognitiva.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"No se encontró el archivo: {filepath}")

    fixations = []
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            uid = row.get("uniform_id_clean") or row.get("uniform_id") or row.get("subid")
            row_lang = row.get("lang")
            tid = row.get("trialid")
            row_itemid = row.get("itemid")

            if uniform_id and uid != uniform_id:
                continue
            if lang and row_lang != lang:
                continue
            if trialid and str(tid) != str(trialid):
                continue
            if itemid and str(row_itemid) != str(itemid):
                continue

            try:
                wordnum = int(float(row.get("wordnum", -1)))
                fixid = int(float(row.get("fixid", -1)))
                dur = float(row.get("dur", 0)) if row.get("dur") else 0.0
                start = float(row.get("start", 0)) if row.get("start") else 0.0
            except (ValueError, TypeError):
                continue

            if wordnum < 0:
                continue

            word_text = row.get("word") or row.get("ia") or f"Word_{wordnum}"
            sentnum_raw = row.get("sentnum_clean", row.get("sentnum", "1"))
            try:
                sentnum = int(float(sentnum_raw))
            except (ValueError, TypeError):
                sentnum = 1

            try:
                ps = float(row.get("ps", 0)) if row.get("ps") else 0.0
            except (ValueError, TypeError):
                ps = 0.0

            if ps <= 0:
                continue

            fixations.append(
                {
                    "uniform_id": uid,
                    "lang": row_lang,
                    "trialid": tid,
                    "wave": wave,
                    "fixid": fixid,
                    "start": start,
                    "dur": dur,
                    "wordnum": wordnum,
                    "word": word_text,
                    "sentnum": sentnum,
                    "ps": ps,
                }
            )

    return fixations


def load_all_fixations(
    wave, uniform_id=None, lang=None, trialid=None, itemid=None, normalize="zscore"
):
    """
    Carga y concatena fijaciones de la(s) ola(s) solicitada(s).

    normalize puede ser:
      - 'zscore': z-score clásico (mean/std) por sesión.
      - 'robust': z-score robusto (median/MAD) por sesión.
      - 'none': PS crudo sin normalizar.

    Devuelve la lista combinada y la lista de rutas de origen.
    """
    paths = resolve_wave_paths(wave)
    all_fix = []
    for p in paths:
        w = 1 if "wave-1" in p else 2
        print(f"--> Cargando fijaciones desde: {p}")
        all_fix.extend(
            load_fixations(
                p, wave=w, uniform_id=uniform_id, lang=lang, trialid=trialid, itemid=itemid
            )
        )
    print(f"--> Total de fijaciones cargadas: {len(all_fix)}")

    if normalize == "zscore":
        all_fix = normalize_session_ps(all_fix, method="zscore")
        for f in all_fix:
            f["has_z"] = True
    elif normalize == "robust":
        all_fix = normalize_session_ps(all_fix, method="robust")
        for f in all_fix:
            f["has_z"] = True
    elif normalize == "none":
        for f in all_fix:
            f["ps_z"] = 0.0
            f["has_z"] = False
    else:
        raise ValueError(f"normalize debe ser 'zscore', 'robust' o 'none', got {normalize!r}")
    return all_fix, paths


def normalize_session_ps(fixations, method="zscore"):
    """
    Aplica normalización por sesión a cada valor de `ps` y guarda el
    resultado en el campo `ps_z`.

    method='zscore': z = (ps - mean) / std
    method='robust': z = (ps - median) / (0.6745 * MAD)
    """
    by_session = defaultdict(list)
    for f in fixations:
        by_session[_session_key(f, "all")].append(f)

    for sess_key, items in by_session.items():
        ps_values = np.array(
            [f["ps"] for f in items if f["ps"] > 0], dtype=float
        )
        if ps_values.size == 0:
            for f in items:
                f["ps_z"] = 0.0
            continue

        if method == "robust":
            mu = float(np.median(ps_values))
            mad = float(median_abs_deviation(ps_values, nan_policy="omit"))
            sigma = 0.6745 * mad
        else:
            mu = float(np.mean(ps_values))
            sigma = float(np.std(ps_values, ddof=0))

        for f in items:
            if f["ps"] > 0 and sigma > 0:
                f["ps_z"] = (f["ps"] - mu) / sigma
            else:
                f["ps_z"] = 0.0
    return fixations


def load_fixations_from_cache_metadata(path, wave, metadata):
    """
    Recarga fijaciones desde el CSV preprocesado aplicando los mismos filtros
    declarados en metadata.json (subid, lang, trialid).
    """
    if not os.path.exists(path):
        return []
    return load_fixations(
        path,
        wave=wave,
        uniform_id=metadata.get("subid"),
        lang=metadata.get("lang"),
        trialid=metadata.get("trialid"),
    )


def _session_key(fix, groupby):
    """
    Define la clave de sesión usada para construir aristas y normalizar PS.
    """
    return (fix["uniform_id"], fix["lang"], fix["trialid"], fix["wave"])
