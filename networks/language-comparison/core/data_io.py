"""
data_io.py

Carga y filtrado de fijaciones por grupo de lenguas desde los CSVs de MECO L2,
y carga de la comprensión lectora global (accuracy) por participante.

Maneja los hallazgos documentados en README.md:
  - `ps` puede venir como string 'NA' (R) en wave-2 (todo ch_s). Se trata como
    inválido, igual que ps <= 0.
  - `uniform_id` puede ser 'NA' en wave-2 (daneses). Se usa `subid` como
    etiqueta de sesión, pero esos participantes no se pueden unir a
    comprensión.
"""

import csv
import os
from collections import defaultdict

import numpy as np

from .language_groups import resolve_group, langs_without_ps
from .paths import (
    resolve_comprehension_paths,
    resolve_fixation_paths,
    wave_of_path,
)


def _to_float(value):
    """Convierte a float tolerando None, '' y 'NA' (R). NaN/inf también."""
    if value is None:
        return None
    s = str(value).strip()
    if s == "" or s == "NA" or s == "NaN" or s == "nan":
        return None
    try:
        f = float(s)
    except (ValueError, TypeError):
        return None
    if f != f or f in (float("inf"), float("-inf")):
        return None
    return f


def load_fixations(filepath, wave, langs=None):
    """
    Carga y filtra las fijaciones del CSV en una sola pasada de streaming.

    Retorna lista de diccionarios con los campos necesarios para construir la
    red de carga cognitiva, etiquetados con la ola de origen.

    `langs`: conjunto de códigos L1 a incluir (None = todos).
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"No se encontró el archivo: {filepath}")

    fixations = []
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_uid = (row.get("uniform_id") or "").strip()
            uid = raw_uid if raw_uid and raw_uid != "NA" else (row.get("subid") or "").strip()
            row_lang = (row.get("lang") or "").strip()
            tid = row.get("trialid")

            if not uid:
                continue
            if langs and row_lang not in langs:
                continue

            ps = _to_float(row.get("ps"))
            if ps is None or ps <= 0:
                continue

            wordnum_raw = _to_float(row.get("wordnum", -1))
            if wordnum_raw is None or wordnum_raw < 0:
                continue
            wordnum = int(wordnum_raw)

            fixid_raw = _to_float(row.get("fixid", -1))
            fixid = int(fixid_raw) if fixid_raw is not None else -1

            dur = _to_float(row.get("dur")) or 0.0
            start = _to_float(row.get("start")) or 0.0
            sentnum_raw = _to_float(row.get("sentnum", "1"))
            sentnum = int(sentnum_raw) if sentnum_raw is not None else 1

            word_text = (row.get("word") or "").strip() or (row.get("ia") or "").strip() or f"Word_{wordnum}"

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


def load_fixations_by_group(wave, group, trialid=None):
    """
    Carga y concatena las fijaciones de todos los participantes cuyo L1
    pertenece al grupo `group` (familia o 'all'), para la(s) ola(s) `wave`.

    Retorna (fixations, source_files, langs).
      fixations: lista de fijaciones (ps > 0, filtradas por lenguas del grupo).
      source_files: rutas de los CSVs de fijación usados.
      langs: códigos L1 del grupo presentes en la ola (con datos de pupila).
    """
    fix_paths = resolve_fixation_paths(wave)
    langs = resolve_group(group, wave)

    ps_absent = set(langs_without_ps(wave))
    usable_langs = [l for l in langs if l not in ps_absent]

    if not usable_langs:
        print(
            f"[!] Grupo '{group}' no tiene lenguas con datos de pupila en "
            f"wave {wave}; no se cargan fijaciones."
        )
        return [], fix_paths, []

    all_fix = []
    for p in fix_paths:
        w = wave_of_path(p)
        print(f"--> Cargando fijaciones desde: {p}  [langs={usable_langs}]")
        all_fix.extend(load_fixations(p, wave=w, langs=set(usable_langs)))

    if trialid is not None:
        tid = str(trialid)
        all_fix = [f for f in all_fix if str(f["trialid"]) == tid]

    print(f"--> Total de fijaciones cargadas: {len(all_fix)}")
    return all_fix, fix_paths, usable_langs


def normalize_session_ps(fixations):
    """
    Aplica z-score por sesión a cada valor de `ps` y guarda el resultado en
    `ps_z`. El campo `ps` original se conserva.
    """
    by_session = defaultdict(list)
    for f in fixations:
        by_session[_session_key(f)].append(f)

    for items in by_session.values():
        ps_values = np.array([f["ps"] for f in items if f["ps"] > 0], dtype=float)
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


def load_accuracy(wave, langs):
    """
    Carga la comprensión lectora global (accuracy) de los participantes cuyos
    códigos L1 están en `langs`.

    Retorna (acc_map, source_files):
      acc_map: dict {uniform_id: {"accuracy", "correct_answer", "total_answer", "lang"}}
      source_files: rutas de los CSVs de comprensión usados.
    """
    comp_paths = resolve_comprehension_paths(wave)
    acc_map = {}
    for p in comp_paths:
        if not os.path.exists(p):
            print(f"[!] No existe CSV de comprensión: {p}")
            continue
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                uid = (row.get("uniform_id") or "").strip()
                lang = (row.get("lang") or "").strip()
                if not uid or uid == "NA":
                    continue
                if langs and lang not in langs:
                    continue
                acc = _to_float(row.get("accuracy"))
                if acc is None:
                    continue
                acc_map[uid] = {
                    "accuracy": acc,
                    "correct_answer": _to_float(row.get("correct_answer")) or 0.0,
                    "total_answer": _to_float(row.get("total_answer")) or 0.0,
                    "lang": lang,
                }
    print(f"--> Participantes con accuracy cargados: {len(acc_map)}")
    return acc_map, comp_paths


def summarize_accuracy(acc_map, fixations):
    """
    Calcula el resumen de accuracy (mean, median, std, min, max, n) sobre los
    participantes que tienen fijaciones Y accuracy.

    Retorna dict resumen + n_participants (con fijación) y n_with_accuracy.
    """
    with_acc = {}
    seen_subjects = set()
    for f in fixations:
        uid = f["uniform_id"]
        if uid not in seen_subjects:
            seen_subjects.add(uid)
            if uid in acc_map:
                with_acc[uid] = acc_map[uid]

    if not with_acc:
        return {
            "mean": None,
            "median": None,
            "std": None,
            "min": None,
            "max": None,
            "n": 0,
        }, len(seen_subjects), 0

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
        len(seen_subjects),
        len(with_acc),
    )


def load_fixations_from_cache_metadata(path, wave, metadata):
    """
    Recarga fijaciones desde el CSV original aplicando los filtros declarados
    en metadata.json (langs del grupo, trialid). Devuelve lista vacía si el
    archivo no existe.
    """
    if not os.path.exists(path):
        return []
    langs = metadata.get("languages") or None
    fix = load_fixations(path, wave=wave, langs=set(langs) if langs else None)
    tid = metadata.get("trialid")
    if tid is not None:
        fix = [f for f in fix if str(f["trialid"]) == str(tid)]
    return fix


def _session_key(fix):
    """Clave de sesión individual (participante, lengua, trial, ola)."""
    return (fix["uniform_id"], fix["lang"], fix["trialid"], fix["wave"])
