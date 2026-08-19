#!/usr/bin/env python3
"""
preprocesamiento_cogload.py

Script de preprocesamiento de datos de fijaciones para la red de carga
cognitiva. Genera archivos .clean.csv a partir de los CSV originales,
aplicando limpieza, validación y normalización de identificadores.

Uso:
    python scripts/preprocesamiento_cogload.py --wave 1
    python scripts/preprocesamiento_cogload.py --wave 2
    python scripts/preprocesamiento_cogload.py --wave both
"""

import argparse
import csv
import json
import os
import re
from collections import defaultdict
from datetime import datetime, timezone

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import median_abs_deviation

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_DIR = os.path.join(_ROOT, "data")
_BENCHMARK_CSV = os.path.join(_DATA_DIR, "benchmark", "L2 word length and frequency.csv")

_RAW_FILES = {
    1: os.path.join(
        _DATA_DIR,
        "MECO-L2_version-2.2",
        "wave-1",
        "primary-data",
        "eye-tracking",
        "joint_l2_fixation_trimmed_report_2.2.csv",
    ),
    2: os.path.join(
        _DATA_DIR,
        "MECO-L2_version-2.2",
        "wave-2",
        "primary-data",
        "eye-tracking",
        "joint_fix_trimmed_L2_wave2_version2.2.csv",
    ),
}

_VALIDATION_DIR = os.path.join(_ROOT, "validation")


# ---------------------------------------------------------------------------
# 1. Benchmark
# ---------------------------------------------------------------------------

def load_benchmark():
    """Carga el benchmark de palabras y retorna un diccionario de mapeo."""
    bm = {}
    with open(_BENCHMARK_CSV, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            trialid = int(row["trialid"])
            sentnum = int(row["sentnum"])
            ianum = int(row["ianum"])
            ia = row["ia"]
            bm[(trialid, ianum)] = {
                "sentnum": sentnum,
                "ia": ia,
                "trialid": trialid,
            }
    return bm


def build_sentnum_map(bm):
    """Construye un mapa trialid -> {ianum -> sentnum}."""
    sent_map = defaultdict(dict)
    for (trialid, ianum), info in bm.items():
        sent_map[trialid][ianum] = info["sentnum"]
    return dict(sent_map)


def build_nwords_map(bm):
    """Construye un mapa (trialid, sentnum) -> cantidad de palabras."""
    nwords = defaultdict(int)
    for (trialid, ianum), info in bm.items():
        nwords[(trialid, info["sentnum"])] += 1
    return dict(nwords)


# ---------------------------------------------------------------------------
# 2. Normalización de uniform_id
# ---------------------------------------------------------------------------

def normalize_uniform_id(row):
    """Genera uniform_id a partir de subid si no existe."""
    uid = row.get("uniform_id", "")
    if pd.notna(uid) and str(uid).strip():
        return str(uid).strip()
    subid = row.get("subid", "")
    if pd.isna(subid) or not str(subid).strip():
        return subid
    subid = str(subid).strip()
    m = re.match(r"^([A-Za-z_]+)_(\d+)$", subid)
    if m:
        lang_part = m.group(1).lower()
        num_part = m.group(2)
        return f"{lang_part}_{num_part}"
    return subid.lower()


# ---------------------------------------------------------------------------
# 3. Detección de outliers con MAD
# ---------------------------------------------------------------------------

def detect_outliers_mad(values, k=3.5):
    """
    Detecta outliers usando MAD (Median Absolute Deviation).
    Retorna una máscara booleana: True = outlier.
    """
    arr = np.array(values, dtype=float)
    med = np.median(arr)
    mad = median_abs_deviation(arr, nan_policy="omit")
    if mad == 0:
        return np.zeros(len(arr), dtype=bool)
    modified_z = 0.6745 * (arr - med) / mad
    return np.abs(modified_z) > k


# ---------------------------------------------------------------------------
# 4. Pipeline de limpieza
# ---------------------------------------------------------------------------

def clean_wave(wave, bm_map, nwords_map):
    """
    Limpia un archivo de fijaciones de una wave y retorna:
      - df: DataFrame limpio
      - quality: DataFrame de métricas de calidad por sesión
      - report: dict con contadores de cada paso de limpieza
    """
    raw_path = _RAW_FILES[wave]
    print(f"\n--> Cargando wave {wave} desde: {raw_path}")
    df = pd.read_csv(raw_path, low_memory=False)
    total_raw = len(df)
    report = {"wave": wave, "raw_rows": total_raw}

    # 1. Generar uniform_id
    df["uniform_id_clean"] = df.apply(normalize_uniform_id, axis=1)
    n_missing_uid = int(df["uniform_id"].isna().sum()) if "uniform_id" in df else total_raw
    report["missing_uniform_id"] = n_missing_uid
    report["generated_uniform_ids"] = int(
        ((df["uniform_id"].isna()) if "uniform_id" in df else pd.Series(True, index=df.index)).sum()
    )

    # 2. Eliminar ch_s
    n_before = len(df)
    df = df[df["lang"] != "ch_s"].copy()
    report["removed_ch_s"] = n_before - len(df)

    # 3. Eliminar duplicados exactos
    n_before = len(df)
    df = df.drop_duplicates()
    report["removed_duplicates"] = n_before - len(df)

    # 4. Eliminar ps ausente o cero
    n_before = len(df)
    df = df[df["ps"].notna() & (df["ps"] > 0)].copy()
    report["removed_ps_missing"] = n_before - len(df)

    # 5. Detección de outliers con MAD por sesión
    df["ps_outlier"] = False
    sessions = df.groupby(["uniform_id_clean", "trialid"], sort=False)
    outlier_mask = pd.Series(False, index=df.index)
    for (uid, tid), group in sessions:
        if len(group) < 5:
            continue
        idx = group.index
        mask = detect_outliers_mad(group["ps"].values, k=3.5)
        outlier_mask.loc[idx] = mask
    df["ps_outlier"] = outlier_mask
    report["removed_ps_outliers"] = int(outlier_mask.sum())
    df = df[~df["ps_outlier"]].copy()

    # 6. Validar sentnum contra benchmark
    df["sentnum_clean"] = df["sentnum"]
    df["sentnum_flag"] = False
    for idx, row in df.iterrows():
        trialid = int(row["trialid"]) if pd.notna(row["trialid"]) else None
        ianum = int(row["ianum"]) if pd.notna(row["ianum"]) else None
        if trialid is not None and ianum is not None and trialid in bm_map:
            expected = bm_map[trialid].get(ianum)
            if expected is not None and int(row["sentnum"]) != expected:
                df.at[idx, "sentnum_clean"] = expected
                df.at[idx, "sentnum_flag"] = True
    report["sentnum_corrected"] = int(df["sentnum_flag"].sum())

    # 7. Wave column
    df["wave"] = wave

    # 8. Session key
    df["session_key"] = (
        df["uniform_id_clean"].astype(str)
        + "|"
        + df["lang"].astype(str)
        + "|"
        + df["trialid"].astype(str)
        + "|"
        + df["wave"].astype(str)
    )

    # 9. Metadata
    df["clean_version"] = datetime.now(timezone.utc).isoformat()

    # 9. Métricas de calidad por sesión
    quality = (
        df.groupby(["uniform_id_clean", "lang", "trialid"], sort=False)
        .agg(
            n_rows=("ps", "size"),
            ps_mean=("ps", "mean"),
            ps_median=("ps", "median"),
            ps_std=("ps", "std"),
            ps_min=("ps", "min"),
            ps_max=("ps", "max"),
            sentnum_corrected=("sentnum_flag", "sum"),
            n_fixations=("fixid", "size"),
        )
        .reset_index()
    )
    quality["ps_coverage"] = 1.0  # after cleaning, all have ps > 0
    quality["wave"] = wave

    report["final_rows"] = len(df)
    report["unique_sessions"] = df.groupby(["uniform_id_clean", "trialid"]).ngroups
    report["unique_participants"] = df["uniform_id_clean"].nunique()
    report["langs"] = sorted(df["lang"].unique().tolist())

    return df, quality, report


# ---------------------------------------------------------------------------
# 5. Guardado
# ---------------------------------------------------------------------------

def save_clean_csv(df, wave):
    """Guarda el CSV limpio con el mismo nombre base + .clean.csv."""
    raw_path = _RAW_FILES[wave]
    stem = os.path.splitext(os.path.basename(raw_path))[0]
    out_dir = os.path.dirname(raw_path)
    out_path = os.path.join(out_dir, f"{stem}.clean.csv")
    df.to_csv(out_path, index=False)
    print(f"[OK] CSV limpio guardado en: {out_path}")
    return out_path


def save_validation(quality, report, wave):
    """Guarda tablas y gráficos de validación."""
    os.makedirs(_VALIDATION_DIR, exist_ok=True)

    # Tabla de calidad
    q_path = os.path.join(_VALIDATION_DIR, f"quality_by_session_w{wave}.csv")
    quality.to_csv(q_path, index=False)
    print(f"[OK] Calidad por sesión guardada en: {q_path}")

    # Reporte resumen
    r_path = os.path.join(_VALIDATION_DIR, f"preprocessing_report_w{wave}.json")
    with open(r_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"[OK] Reporte guardado en: {r_path}")

    # --- Gráficos ---
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle(f"Preprocesamiento — Wave {wave}", fontsize=14)

    # 1. Distribución de ps por lang
    langs = sorted(quality["lang"].unique())
    data_by_lang = [quality.loc[quality["lang"] == la, "ps_median"].values for la in langs]
    bp = axes[0, 0].boxplot(data_by_lang, showfliers=False)
    # Set tick labels after boxplot
    axes[0, 0].set_xticklabels(langs, rotation=45)
    axes[0, 0].set_title("PS mediana por lengua")
    axes[0, 0].set_ylabel("PS (median)")
    axes[0, 0].tick_params(axis="x", rotation=45)

    # 2. Distribución de ps global (post-limpieza)
    # Reload from quality for global
    axes[0, 1].hist(quality["ps_median"].values, bins=40, edgecolor="black", alpha=0.7)
    axes[0, 1].set_title("Distribución PS mediana global")
    axes[0, 1].set_xlabel("PS (median)")
    axes[0, 1].set_ylabel("Frecuencia")

    # 3. Coverage por lang/trialid
    pivot = quality.pivot_table(values="ps_coverage", index="lang", columns="trialid", aggfunc="mean")
    im = axes[0, 2].imshow(pivot.values, aspect="auto", cmap="RdYlGn", vmin=0, vmax=1)
    axes[0, 2].set_xticks(range(len(pivot.columns)))
    axes[0, 2].set_xticklabels(pivot.columns.astype(int))
    axes[0, 2].set_yticks(range(len(pivot.index)))
    axes[0, 2].set_yticklabels(pivot.index)
    axes[0, 2].set_title("Coverage PS (post-clean)")
    fig.colorbar(im, ax=axes[0, 2])

    # 4. Sentnum corregidos por trialid
    sent_flag = quality.groupby("trialid")["sentnum_corrected"].sum()
    axes[1, 0].bar(sent_flag.index.astype(str), sent_flag.values, color="steelblue")
    axes[1, 0].set_title("Sentnum corregidos por trialid")
    axes[1, 0].set_xlabel("trialid")
    axes[1, 0].set_ylabel("Nº filas corregidas")

    # 5. Distribución de duración
    dur_stats = quality.groupby("lang")["n_fixations"].mean()
    axes[1, 1].barh(dur_stats.index, dur_stats.values, color="coral")
    axes[1, 1].set_title("Fixaciones promedio por lengua")
    axes[1, 1].set_xlabel("Nº fixaciones")

    # 6. Resumen de limpieza
    steps = ["raw_rows", "removed_ch_s", "removed_duplicates", "removed_ps_missing", "removed_ps_outliers", "final_rows"]
    vals = [report.get(s, 0) for s in steps]
    labels = ["Raw", "-ch_s", "-duplicados", "-ps NA", "-outliers", "Final"]
    axes[1, 2].barh(labels, vals, color=["gray", "red", "orange", "yellow", "purple", "green"])
    axes[1, 2].set_title("Pipeline de limpieza")
    axes[1, 2].set_xlabel("Filas")

    plt.tight_layout()
    fig_path = os.path.join(_VALIDATION_DIR, f"preprocessing_plots_w{wave}.png")
    plt.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] Gráficos guardados en: {fig_path}")


# ---------------------------------------------------------------------------
# 6. Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="preprocesamiento_cogload",
        description="Preprocesamiento de datos de fijaciones para la red de carga cognitiva.",
    )
    parser.add_argument(
        "--wave",
        type=str,
        default="both",
        choices=["1", "2", "both"],
        help="Wave a procesar (default: both).",
    )
    args = parser.parse_args()

    bm = load_benchmark()
    bm_map = build_sentnum_map(bm)
    nwords_map = build_nwords_map(bm)

    waves = [1, 2] if args.wave == "both" else [int(args.wave)]
    all_reports = []

    for wave in waves:
        df, quality, report = clean_wave(wave, bm_map, nwords_map)
        out_path = save_clean_csv(df, wave)
        save_validation(quality, report, wave)
        all_reports.append(report)

        # Print summary
        print(f"\n{'='*60}")
        print(f"RESUMEN PREPROCESAMIENTO — Wave {wave}")
        print(f"{'='*60}")
        for k, v in report.items():
            if isinstance(v, list):
                print(f"  {k:30s}: {v}")
            else:
                print(f"  {k:30s}: {v:,}" if isinstance(v, int) else f"  {k:30s}: {v}")
        print(f"{'='*60}\n")

    # Save combined report
    os.makedirs(_VALIDATION_DIR, exist_ok=True)
    with open(os.path.join(_VALIDATION_DIR, "preprocessing_summary.json"), "w") as f:
        json.dump(all_reports, f, indent=2, ensure_ascii=False)
    print(f"[OK] Resumen combinado guardado en: {os.path.join(_VALIDATION_DIR, 'preprocessing_summary.json')}")


if __name__ == "__main__":
    main()
