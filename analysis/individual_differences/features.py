"""Derived scores for individual-differences exploration."""

import pandas as pd

from .io import MEASURES


def standardize_within_wave(data):
    result = data.copy()
    for measure in MEASURES:
        result[f"z_{measure}"] = result.groupby("wave", observed=True)[measure].transform(
            lambda values: (values - values.mean()) / values.std(ddof=0)
        )
    return result


def add_composites(data):
    result = data.copy()
    language_components = ["z_lextale", "z_vocab.t2.5", "z_TOWRE_word", "z_TOWRE_nonword"]
    result["language_skill_composite"] = result[language_components].mean(axis=1, skipna=False)
    result["cognitive_skill"] = result["z_cft20"]
    result["motivation_standardized"] = result["z_motiv"]
    result["spelling_standardized"] = result["z_spelling"]
    return result


def correlation_table(data):
    rows = []
    for wave, group in data.groupby("wave", observed=True):
        correlations = group[MEASURES].corr()
        rows.append(correlations.assign(wave=wave).reset_index(names="measure"))
    return pd.concat(rows, ignore_index=True)
