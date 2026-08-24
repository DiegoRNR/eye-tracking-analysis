#!/usr/bin/env python3
"""Run the standalone individual-differences analysis."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.individual_differences.features import add_composites, correlation_table, standardize_within_wave
from analysis.individual_differences.io import language_summary, load_data, missingness_summary
from analysis.individual_differences.plots import plot_correlations, plot_distributions, plot_language_profiles, plot_missingness


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wave", choices=["1", "2", "both"], default="both")
    parser.add_argument("--outdir", default="analysis/individual_differences/output")
    args = parser.parse_args()

    output_dir = Path(args.outdir)
    plot_dir = output_dir / "plots"
    data = add_composites(standardize_within_wave(load_data(args.wave)))
    output_dir.mkdir(parents=True, exist_ok=True)

    data.to_csv(output_dir / "individual_differences_analysis_dataset.csv", index=False)
    missingness_summary(data).to_csv(output_dir / "missingness_summary.csv", index=False)
    language_summary(data).to_csv(output_dir / "language_summary.csv", index=False)
    correlation_table(data).to_csv(output_dir / "correlations.csv", index=False)

    figures = [plot_missingness(data, plot_dir), plot_distributions(data, plot_dir), plot_language_profiles(data, plot_dir)]
    figures.extend(plot_correlations(data, plot_dir))
    for figure in figures:
        import matplotlib.pyplot as plt
        plt.close(figure)

    report = {
        "wave": args.wave,
        "rows": int(len(data)),
        "participants": int(data["participant_id"].nunique()),
        "complete_cases_all_measures": int(data["all_measures_complete"].sum()),
        "missingness": missingness_summary(data).to_dict(orient="records"),
        "outputs": str(output_dir),
    }
    (output_dir / "analysis_summary.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
