#!/usr/bin/env python3
"""Run integrated moderation analyses without altering standalone analyses."""

import argparse
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.integrated.io import load_integrated, predictor_summary
from analysis.integrated.models import (
    fit_comprehension_moderation,
    fit_fixation_moderation,
    interaction_summary,
)
from analysis.integrated.plots import plot_interaction_means, plot_skill_quartiles


PREDICTORS = [
    "language_skill_composite",
    "z_lextale",
    "z_vocab.t2.5",
    "z_TOWRE_word",
    "z_TOWRE_nonword",
    "cognitive_skill",
    "motivation_standardized",
    "spelling_standardized",
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wave", choices=["1", "2", "both"], default="both")
    parser.add_argument("--outdir", default="analysis/integrated/output")
    args = parser.parse_args()
    output = Path(args.outdir)
    output.mkdir(parents=True, exist_ok=True)
    data = load_integrated(args.wave)
    data.to_csv(output / "integrated_analysis_dataset.csv", index=False)
    predictor_summary(data, PREDICTORS).to_csv(output / "predictor_summary.csv", index=False)

    results = []
    reverse_results = []
    for wave, group in data.groupby("wave", observed=True):
        for predictor in PREDICTORS:
            if group[predictor].notna().sum() < 50:
                continue
            result, model_data, formula = fit_fixation_moderation(group, predictor)
            summary = interaction_summary(result, predictor)
            summary.update({"wave": int(wave), "predictor": predictor, "n_rows": len(model_data), "formula": formula})
            results.append(summary)
        if group["language_skill_composite"].notna().sum() >= 50:
            reverse, reverse_data, reverse_formula = fit_comprehension_moderation(
                group, "language_skill_composite"
            )
            reverse_term = "fixations_per_word:language_skill_composite"
            low, high = reverse.conf_int().loc[reverse_term]
            reverse_results.append({
                "wave": int(wave),
                "predictor": "language_skill_composite",
                "n_rows": len(reverse_data),
                "term": reverse_term,
                "estimate": float(reverse.params[reverse_term]),
                "odds_ratio": float(np.exp(reverse.params[reverse_term])),
                "ci_low": float(np.exp(low)),
                "ci_high": float(np.exp(high)),
                "p_value": float(reverse.pvalues[reverse_term]),
                "formula": reverse_formula,
            })
    fixation_results = pd.DataFrame(results)
    if not fixation_results.empty:
        fixation_results["p_value_fdr"] = fixation_results.groupby("wave")["p_value"].transform(
            lambda values: multipletests(values, method="fdr_bh")[1]
        )
    fixation_results.to_csv(output / "fixation_moderation_results.csv", index=False)
    reverse_results = pd.DataFrame(reverse_results)
    if not reverse_results.empty:
        reverse_results["p_value_fdr"] = reverse_results.groupby("wave")["p_value"].transform(
            lambda values: multipletests(values, method="fdr_bh")[1]
        )
    reverse_results.to_csv(output / "comprehension_moderation_results.csv", index=False)

    figures = [
        plot_skill_quartiles(data, output / "plots"),
        plot_interaction_means(data, output / "plots"),
    ]
    import matplotlib.pyplot as plt
    for figure in figures:
        plt.close(figure)

    metadata = {
        "wave": args.wave,
        "rows": int(len(data)),
        "participants": int(data["participant_id"].nunique()),
        "models": len(results),
        "reverse_models": len(reverse_results),
        "output": str(output),
    }
    (output / "analysis_summary.json").write_text(json.dumps(metadata, indent=2))
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
