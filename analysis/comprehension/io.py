"""Input loading and validation for the comprehension analysis."""

import math
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
COUNT_FILES = {
    1: ROOT / "validation" / "comprehension_fixation_counts_w1.csv",
    2: ROOT / "validation" / "comprehension_fixation_counts_w2.csv",
}


def load_counts(wave="both"):
    waves = [1, 2] if wave == "both" else [int(wave)]
    frames = []
    for current_wave in waves:
        path = COUNT_FILES[current_wave]
        if not path.exists():
            raise FileNotFoundError(
                f"Missing {path}. Run scripts/prepare_comprehension_fixations.py first."
            )
        frame = pd.read_csv(path)
        frame["wave"] = current_wave
        frames.append(frame)

    data = pd.concat(frames, ignore_index=True)
    required = {
        "subid", "uniform_id_resolved", "lang", "text_id",
        "valid_fixation_events", "text_length_words", "fixations_per_word",
        "comprehension_score", "comprehension_match",
    }
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    data = data[data["comprehension_match"]].copy()
    data["participant_id"] = data["uniform_id_resolved"].fillna(data["subid"])
    data["text_id"] = pd.to_numeric(data["text_id"], errors="raise").astype(int)
    data["comprehension_score"] = pd.to_numeric(data["comprehension_score"], errors="raise")
    data["comprehension_proportion"] = data["comprehension_score"] / 2.0
    data["valid_fixation_events"] = pd.to_numeric(
        data["valid_fixation_events"], errors="raise"
    ).astype(int)
    data["text_length_words"] = pd.to_numeric(data["text_length_words"], errors="raise")
    data["log_text_length"] = data["text_length_words"].map(math.log)

    key = ["participant_id", "wave", "text_id"]
    if data.duplicated(key).any():
        raise ValueError(f"Duplicate participant-text rows found for key {key}")
    if (data["text_length_words"] <= 0).any():
        raise ValueError("Text lengths must be positive")
    if not data["comprehension_score"].between(0, 2).all():
        raise ValueError("Comprehension scores must be between 0 and 2")
    return data.sort_values(key).reset_index(drop=True)


def sample_summary(data):
    return (
        data.groupby(["wave", "lang"], observed=True)
        .agg(
            participants=("participant_id", "nunique"),
            participant_text_rows=("text_id", "size"),
            texts=("text_id", "nunique"),
            mean_comprehension=("comprehension_proportion", "mean"),
            mean_fixations_per_word=("fixations_per_word", "mean"),
        )
        .reset_index()
    )
