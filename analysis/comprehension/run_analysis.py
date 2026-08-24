#!/usr/bin/env python3
"""Run descriptive and clustered comprehension/fixation analyses."""

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scipy.stats import spearmanr

from analysis.comprehension.io import load_counts, sample_summary
from analysis.comprehension.models import (
    fit_poisson_diagnostic,
    fit_primary,
    fit_reverse,
    save_result,
)
from analysis.comprehension.plots import save_descriptive_plots


def participant_spearman(data):
    participant = (
        data.groupby("participant_id", as_index=False)
        .agg(
            mean_comprehension=("comprehension_proportion", "mean"),
            mean_fixations_per_word=("fixations_per_word", "mean"),
        )
    )
    correlation, p_value = spearmanr(
        participant["mean_comprehension"], participant["mean_fixations_per_word"]
    )
    return {
        "n_participants": int(len(participant)),
        "spearman_rho": float(correlation),
        "p_value": float(p_value),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wave", choices=["1", "2", "both"], default="both")
    parser.add_argument("--outdir", default="analysis/comprehension/output")
    args = parser.parse_args()
    output_dir = Path(args.outdir)
    data = load_counts(args.wave)

    output_dir.mkdir(parents=True, exist_ok=True)
    sample_summary(data).to_csv(output_dir / "sample_summary.csv", index=False)
    data.to_csv(output_dir / "analysis_dataset.csv", index=False)
    save_descriptive_plots(data, output_dir / "plots")

    diagnostics = participant_spearman(data)
    poisson = fit_poisson_diagnostic(data)
    primary = fit_primary(data)
    reverse = fit_reverse(data)
    diagnostics["poisson_pearson_dispersion"] = float(
        (poisson.resid_pearson**2).sum() / poisson.df_resid
    )
    diagnostics["primary_model"] = save_result(
        primary, data, "primary_negative_binomial_gee", output_dir
    )
    diagnostics["reverse_model"] = save_result(
        reverse, data, "reverse_binomial_gee", output_dir, ratio_name="odds_ratio"
    )

    sensitivity = data[data["duration_extreme_rows"] == 0].copy()
    if len(sensitivity) < len(data):
        result = fit_primary(sensitivity)
        diagnostics["duration_sensitivity"] = save_result(
            result, sensitivity, "sensitivity_no_extreme_duration", output_dir
        )

    (output_dir / "analysis_metadata.json").write_text(json.dumps(diagnostics, indent=2))
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
