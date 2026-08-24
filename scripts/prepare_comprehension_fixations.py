#!/usr/bin/env python3
"""Prepare fixation events and participant-text counts for comprehension analyses.

This is deliberately separate from ``preprocess_fixation_data.py``. The latter
is pupil-oriented and removes rows with missing or extreme ``ps`` values. Those
rows must not be removed when the outcome is fixation count.

The script writes new files with the ``.comprehension.clean.csv`` suffix and
does not modify the existing ``*.clean.csv`` files.
"""

import argparse
import json
import os

import pandas as pd


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
DEFAULT_VALIDATION_DIR = os.path.join(ROOT, "validation")

FIXATION_FILES = {
    1: os.path.join(
        DATA_DIR,
        "MECO-L2_version-2.2",
        "wave-1",
        "primary-data",
        "eye-tracking",
        "joint_l2_fixation_trimmed_report_2.2.csv",
    ),
    2: os.path.join(
        DATA_DIR,
        "MECO-L2_version-2.2",
        "wave-2",
        "primary-data",
        "eye-tracking",
        "joint_fix_trimmed_L2_wave2_version2.2.csv",
    ),
}

COMPREHENSION_FILES = {
    1: os.path.join(
        DATA_DIR,
        "MECO-L2_version-2.2",
        "wave-1",
        "primary-data",
        "comprehension",
        "joint_l2_acc_breakdown.csv",
    ),
    2: os.path.join(
        DATA_DIR,
        "MECO-L2_version-2.2",
        "wave-2",
        "primary-data",
        "comprehension",
        "joint_l2_Wave2_acc_breakdown_trimmed.csv",
    ),
}

BENCHMARK_FILE = os.path.join(DATA_DIR, "benchmark", "L2 word length and frequency.csv")


def read_comprehension(wave):
    comp = pd.read_csv(COMPREHENSION_FILES[wave], low_memory=False)
    comp["number"] = pd.to_numeric(comp["number"], errors="coerce").astype("Int64")
    comp["ACCURACY"] = pd.to_numeric(comp["ACCURACY"], errors="coerce")
    return comp


def resolve_participant_ids(df, comp):
    """Resolve missing fixation uniform IDs only through the comprehension file."""
    comp_by_subject = (
        comp[["subject", "uniform_id", "lang"]]
        .drop_duplicates()
        .rename(columns={"subject": "subid", "lang": "comp_lang"})
    )
    df = df.copy()
    df["subid"] = df["subid"].astype(str).str.strip()
    df["lang"] = df["lang"].astype(str).str.strip()
    df["uniform_id_original"] = df["uniform_id"] if "uniform_id" in df else pd.NA
    df["uniform_id_original"] = df["uniform_id_original"].where(
        df["uniform_id_original"].notna(), pd.NA
    )
    df["uniform_id_original"] = df["uniform_id_original"].astype("string").str.strip()

    missing = df["uniform_id_original"].isna() | (df["uniform_id_original"] == "")
    subject_matches = df[["subid", "lang"]].merge(
        comp_by_subject, on="subid", how="left"
    )
    valid_subject_match = subject_matches["comp_lang"].eq(subject_matches["lang"])
    subject_uniform = pd.Series(
        subject_matches["uniform_id"].where(valid_subject_match).to_numpy(),
        index=df.index,
    )

    df["uniform_id_resolved"] = df["uniform_id_original"]
    df.loc[missing, "uniform_id_resolved"] = subject_uniform[missing].to_numpy()
    df["id_resolution_status"] = "from_fixation_file"
    df.loc[missing & df["uniform_id_resolved"].notna(), "id_resolution_status"] = (
        "resolved_from_comprehension_subject"
    )
    df.loc[df["uniform_id_resolved"].isna(), "id_resolution_status"] = "unresolved"
    return df


def load_text_lengths():
    benchmark = pd.read_csv(BENCHMARK_FILE, low_memory=False)
    benchmark["trialid"] = pd.to_numeric(benchmark["trialid"], errors="coerce").astype("Int64")
    return benchmark.groupby("trialid")["ianum"].nunique().rename("text_length_words")


def prepare_wave(wave, text_lengths):
    fixation_path = FIXATION_FILES[wave]
    df = pd.read_csv(fixation_path, low_memory=False)
    comp = read_comprehension(wave)
    raw_rows = len(df)

    duplicate_mask = df.duplicated(keep="first")
    df = df.loc[~duplicate_mask].copy()
    removed_duplicates = int(duplicate_mask.sum())

    df = resolve_participant_ids(df, comp)
    df["wave"] = wave
    df["trialid"] = pd.to_numeric(df["trialid"], errors="coerce").astype("Int64")
    df["itemid"] = pd.to_numeric(df["itemid"], errors="coerce").astype("Int64")
    df["fixid"] = pd.to_numeric(df["fixid"], errors="coerce").astype("Int64")

    # itemid identifies the text reliably; trialid is retained as experimental position.
    df["text_id"] = df["itemid"]
    df["ps_missing"] = df["ps"].isna()
    df["type_out"] = df["type"].astype("string").str.lower().eq("out")
    df["duration_extreme"] = pd.to_numeric(df["dur"], errors="coerce").gt(2000)
    df["has_word_assignment"] = df["wordnum"].notna() & df["ianum"].notna()
    df["valid_text_fixation"] = (
        ~df["type_out"] & df["has_word_assignment"] & df["text_id"].notna()
    )
    df["text_length_words"] = df["text_id"].map(text_lengths)

    # One fixation event is identified by participant, text, and fixid.
    group_cols = ["subid", "uniform_id_resolved", "lang", "wave", "text_id"]
    valid = df[df["valid_text_fixation"]].copy()
    counts = (
        df.groupby(group_cols, dropna=False, sort=False)
        .agg(
            raw_rows=("fixid", "size"),
            unique_fixation_events=("fixid", "nunique"),
            out_rows=("type_out", "sum"),
            ps_missing_rows=("ps_missing", "sum"),
            duration_extreme_rows=("duration_extreme", "sum"),
            valid_text_rows=("valid_text_fixation", "sum"),
        )
        .reset_index()
    )
    valid_events = (
        valid.groupby(group_cols, dropna=False, sort=False)["fixid"]
        .nunique()
        .rename("valid_fixation_events")
        .reset_index()
    )
    counts = counts.merge(valid_events, on=group_cols, how="left")
    counts["valid_fixation_events"] = counts["valid_fixation_events"].fillna(0).astype(int)
    counts["text_length_words"] = counts["text_id"].map(text_lengths)
    counts["fixations_per_word"] = counts["valid_fixation_events"] / counts["text_length_words"]

    comp_join = comp[["uniform_id", "number", "ACCURACY"]].rename(
        columns={"number": "text_id", "ACCURACY": "comprehension_score"}
    )
    counts = counts.merge(
        comp_join,
        left_on=["uniform_id_resolved", "text_id"],
        right_on=["uniform_id", "text_id"],
        how="left",
    ).drop(columns=["uniform_id"])
    counts["comprehension_match"] = counts["comprehension_score"].notna()

    output_dir = os.path.dirname(fixation_path)
    stem = os.path.splitext(os.path.basename(fixation_path))[0]
    event_path = os.path.join(output_dir, f"{stem}.comprehension.clean.csv")
    df.to_csv(event_path, index=False)

    report = {
        "wave": wave,
        "raw_rows": raw_rows,
        "removed_exact_duplicates": removed_duplicates,
        "output_rows": len(df),
        "type_out_rows": int(df["type_out"].sum()),
        "ps_missing_rows_retained": int(df["ps_missing"].sum()),
        "duration_extreme_rows_flagged": int(df["duration_extreme"].sum()),
        "valid_text_fixation_rows": int(df["valid_text_fixation"].sum()),
        "unresolved_participants": int(
            df.loc[df["uniform_id_resolved"].isna(), "subid"].nunique()
        ),
        "participant_text_rows": len(counts),
        "participant_text_rows_with_comprehension": int(counts["comprehension_match"].sum()),
        "event_output": event_path,
    }
    return df, counts, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wave", choices=["1", "2", "both"], default="both")
    parser.add_argument("--output-dir", default=DEFAULT_VALIDATION_DIR)
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    text_lengths = load_text_lengths()
    waves = [1, 2] if args.wave == "both" else [int(args.wave)]
    reports = []
    for wave in waves:
        _, counts, report = prepare_wave(wave, text_lengths)
        counts_path = os.path.join(args.output_dir, f"comprehension_fixation_counts_w{wave}.csv")
        counts.to_csv(counts_path, index=False)
        report["counts_output"] = counts_path
        reports.append(report)
        print(json.dumps(report, indent=2))

    report_path = os.path.join(args.output_dir, "comprehension_fixation_preprocessing.json")
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(reports, handle, indent=2, ensure_ascii=False)
    print(f"[OK] Report saved to: {report_path}")


if __name__ == "__main__":
    main()
