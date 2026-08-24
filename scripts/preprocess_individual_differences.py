#!/usr/bin/env python3
"""Validate and prepare MECO-L2 individual-difference tables.

The source files are never modified. The generated files retain the original
scores, add normalized numeric columns and quality flags, and are intended for
the standalone individual-differences analysis.
"""

import argparse
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data" / "MECO-L2_version-2.2"
VALIDATION_ROOT = ROOT / "validation"

SOURCE_FILES = {
    1: DATA_ROOT / "wave-1/primary-data/individual-differences/joint.ind.diff.l2.csv",
    2: DATA_ROOT / "wave-2/primary-data/individual-differences/joint.ind.diff.l2.w2.csv",
}

# These are conservative plausibility checks, not deletion rules. Some source
# score definitions require confirmation from the original study materials.
PLAUSIBLE_RANGES = {
    "motiv": (1, 5),
    "lextale": (0, 100),
    "vocab.t2.5": (0, 40),
    "cft20": (0, 20),
}


def prepare_wave(wave):
    source = SOURCE_FILES[wave]
    raw = pd.read_csv(source, low_memory=False)
    original_columns = list(raw.columns)
    id_column = "uniform_id"
    numeric_columns = [column for column in raw.columns if column not in {"subid", "uniform_id", "lang"}]
    data = raw.copy()

    for column in numeric_columns:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data["wave"] = wave
    data["participant_id"] = data[id_column].astype("string").str.strip()
    data["id_valid"] = data["participant_id"].notna() & data["participant_id"].ne("")
    data["lang_id_consistent"] = data.apply(
        lambda row: str(row["participant_id"]).startswith(f"{row['lang']}_")
        or str(row["participant_id"]) == str(row["lang"]),
        axis=1,
    )
    data["all_measures_complete"] = data[numeric_columns].notna().all(axis=1)
    conversion_issue = pd.Series(False, index=data.index)
    for column in numeric_columns:
        conversion_issue |= raw[column].notna() & data[column].isna()
    data["numeric_conversion_issue"] = conversion_issue

    for column in numeric_columns:
        data[f"{column}_missing"] = data[column].isna()
        data[f"{column}_zero_score"] = data[column].eq(0)
        if column in PLAUSIBLE_RANGES:
            lower, upper = PLAUSIBLE_RANGES[column]
            data[f"{column}_out_of_plausible_range"] = data[column].notna() & ~data[column].between(lower, upper)
        else:
            data[f"{column}_out_of_plausible_range"] = data[column].lt(0)

    duplicate_rows = int(data.duplicated().sum())
    duplicate_ids = int(data.duplicated("participant_id").sum())
    invalid_ranges = {
        column: int(data[f"{column}_out_of_plausible_range"].sum())
        for column in numeric_columns
        if data[f"{column}_out_of_plausible_range"].any()
    }

    output_name = source.stem + ".individual.clean.csv"
    output = source.with_name(output_name)
    data.to_csv(output, index=False)

    report = {
        "wave": wave,
        "source_file": str(source.relative_to(ROOT)),
        "output_file": str(output.relative_to(ROOT)),
        "original_columns": original_columns,
        "rows": int(len(data)),
        "columns_before": int(len(original_columns)),
        "columns_after": int(len(data.columns)),
        "id_column": id_column,
        "unique_participants": int(data["participant_id"].nunique()),
        "duplicate_rows": duplicate_rows,
        "duplicate_participant_ids": duplicate_ids,
        "invalid_ids": int((~data["id_valid"]).sum()),
        "language_id_mismatches": int((~data["lang_id_consistent"]).sum()),
        "complete_cases": int(data["all_measures_complete"].sum()),
        "missing_by_variable": {column: int(data[column].isna().sum()) for column in numeric_columns},
        "numeric_conversion_issues": int(data["numeric_conversion_issue"].sum()),
        "plausibility_flags_by_variable": invalid_ranges,
        "zero_scores_by_variable": {
            column: int(data[f"{column}_zero_score"].sum())
            for column in numeric_columns
            if data[f"{column}_zero_score"].any()
        },
        "ranges": {
            column: {
                "min": float(data[column].min()) if data[column].notna().any() else None,
                "max": float(data[column].max()) if data[column].notna().any() else None,
            }
            for column in numeric_columns
        },
        "correlations": data[numeric_columns].corr().round(4).to_dict(),
    }
    return data, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wave", choices=["1", "2", "both"], default="both")
    args = parser.parse_args()
    VALIDATION_ROOT.mkdir(parents=True, exist_ok=True)
    waves = [1, 2] if args.wave == "both" else [int(args.wave)]
    reports = []
    for wave in waves:
        _, report = prepare_wave(wave)
        report_path = VALIDATION_ROOT / f"individual_differences_quality_w{wave}.json"
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        reports.append(report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
    (VALIDATION_ROOT / "individual_differences_summary.json").write_text(
        json.dumps(reports, indent=2, ensure_ascii=False)
    )


if __name__ == "__main__":
    main()
