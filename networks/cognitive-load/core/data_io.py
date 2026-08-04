"""
data_io.py

Carga y filtrado de fijaciones desde los CSV de MECO L2, y normalización
intra-sesión de PS (z-score por sesión).
"""

import csv
import os
from collections import defaultdict

import numpy as np

from .paths import resolve_wave_paths


def load_fixations(filepath, wave, uniform_id=None, lang=None, trialid=None):
    """
    Carga y filtra las fijaciones del dataset CSV en una sola pasada de streaming.

    Retorna una lista de diccionarios con los campos necesarios para construir
    la red de carga cognitiva, etiquetados con la ola de origen.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"No se encontró el archivo: {filepath}")

    fixations = []
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            uid = row.get("uniform_id") or row.get("subid")
            row_lang = row.get("lang")
            tid = row.get("trialid")

            if uniform_id and uid != uniform_id:
                continue
            if lang and row_lang != lang:
                continue
            if trialid and str(tid) != str(trialid):
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
            sentnum_raw = row.get("sentnum", "1")
            try:
                sentnum = int(float(sentnum_raw))
            except (ValueError, TypeError):
                sentnum = 1

            try:
                ps = float(row.get("ps", 0)) if row.get("ps") else 0.0
            except (ValueError, TypeError):
                ps = 0.0

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
    wave, uniform_id=None, lang=None, trialid=None, normalize="zscore"
):
    """
    Carga y concatena fijaciones de la(s) ola(s) solicitada(s).

    Si normalize='zscore' (default), cada sesión recibe un z-score por
    observación: z = (ps − μ_session) / σ_session.  Esto es 0 en el
    promedio de la sesión, +1 a una desviación estándar por encima (estrés
    elevado), −1 a una por debajo.  Cuando normalize='none' se conserva
    el PS crudo.

    Devuelve la lista combinada y la lista de rutas de origen.
    """
    paths = resolve_wave_paths(wave)
    all_fix = []
    for p in paths:
        w = 1 if "wave-1" in p else 2
        print(f"--> Cargando fijaciones desde: {p}")
        all_fix.extend(
            load_fixations(
                p, wave=w, uniform_id=uniform_id, lang=lang, trialid=trialid
            )
        )
    print(f"--> Total de fijaciones cargadas: {len(all_fix)}")
    if normalize == "zscore":
        all_fix = normalize_session_ps(all_fix)
        for f in all_fix:
            f["has_z"] = True
    elif normalize == "none":
        for f in all_fix:
            f["ps_z"] = 0.0
            f["has_z"] = False
    else:
        raise ValueError(f"normalize debe ser 'zscore' o 'none', got {normalize!r}")
    return all_fix, paths


def normalize_session_ps(fixations):
    """
    Aplica z-score por sesión a cada valor de `ps` y guarda el resultado
    en el campo `ps_z` de cada fijación. El campo `ps` original se conserva.
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
    Recarga fijaciones desde el CSV original aplicando los mismos filtros
    declarados en metadata.json (subid, lang, trialid).

    Devuelve lista vacía si el archivo no existe, a diferencia de
    load_fixations que lanza FileNotFoundError.
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

    La construcción de aristas siempre parte de sesiones individuales por
    participante, de modo que `count` y `n_sessions` reflejen cuántas
    observaciones reales (por participante) apoyan cada transición. El
    parámetro `groupby` se preserva en los metadatos pero no afecta el
    conteo de aristas: la agregación por L1 o por participante se obtiene
    filtrando los datos de antemano con --lang o --subid.
    """
    return (fix["uniform_id"], fix["lang"], fix["trialid"], fix["wave"])
