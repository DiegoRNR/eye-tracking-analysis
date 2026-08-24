"""Load and validate the standalone individual-differences datasets."""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SOURCE_FILES = {
    1: ROOT / "data/MECO-L2_version-2.2/wave-1/primary-data/individual-differences/joint.ind.diff.l2.individual.clean.csv",
    2: ROOT / "data/MECO-L2_version-2.2/wave-2/primary-data/individual-differences/joint.ind.diff.l2.w2.individual.clean.csv",
}
MEASURES = [
    "spelling", "motiv", "lextale", "TOWRE_word", "TOWRE_nonword",
    "vocab", "vocab.t2.5", "cft20",
]


def load_data(wave="both"):
    waves = [1, 2] if wave == "both" else [int(wave)]
    frames = []
    for current_wave in waves:
        path = SOURCE_FILES[current_wave]
        if not path.exists():
            raise FileNotFoundError(
                f"Missing {path}. Run scripts/preprocess_individual_differences.py first."
            )
        data = pd.read_csv(path, low_memory=False)
        data["wave"] = current_wave
        frames.append(data)
    data = pd.concat(frames, ignore_index=True)
    missing = set(MEASURES).difference(data.columns)
    if missing:
        raise ValueError(f"Missing individual-difference columns: {sorted(missing)}")
    if data.duplicated(["wave", "participant_id"]).any():
        raise ValueError("Participant IDs must be unique within each wave")
    return data


def missingness_summary(data):
    rows = []
    for wave, group in data.groupby("wave", observed=True):
        for measure in MEASURES:
            rows.append({
                "wave": wave,
                "measure": measure,
                "n": len(group),
                "missing": int(group[measure].isna().sum()),
                "missing_proportion": float(group[measure].isna().mean()),
            })
    return pd.DataFrame(rows)


def language_summary(data):
    return (
        data.groupby(["wave", "lang"], observed=True)[MEASURES]
        .agg(["count", "mean", "std"])
        .reset_index()
    )
