"""Load and merge participant-text outcomes with reader measures."""

from pathlib import Path

import pandas as pd

from analysis.comprehension.io import load_counts
from analysis.individual_differences.features import add_composites, standardize_within_wave
from analysis.individual_differences.io import MEASURES, load_data


ROOT = Path(__file__).resolve().parents[2]


def load_integrated(wave="both"):
    outcomes = load_counts(wave)
    individual = add_composites(standardize_within_wave(load_data(wave)))
    individual_columns = [
        "participant_id", "wave", "lang", *MEASURES,
        *(f"z_{measure}" for measure in MEASURES),
        "language_skill_composite", "cognitive_skill",
        "motivation_standardized", "spelling_standardized",
    ]
    individual = individual[individual_columns]
    merged = outcomes.merge(
        individual,
        on=["participant_id", "wave"],
        how="left",
        suffixes=("", "_individual"),
        validate="many_to_one",
    )
    if merged["language_skill_composite"].isna().all():
        raise ValueError("Integrated join produced no individual-difference data")
    return merged


def predictor_summary(data, predictors):
    rows = []
    for wave, group in data.groupby("wave", observed=True):
        for predictor in predictors:
            valid = group[predictor].notna()
            rows.append({
                "wave": wave,
                "predictor": predictor,
                "participants": int(group.loc[valid, "participant_id"].nunique()),
                "participant_text_rows": int(valid.sum()),
                "missing_rows": int((~valid).sum()),
            })
    return pd.DataFrame(rows)
