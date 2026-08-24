"""Plots for the standalone individual-differences analysis."""

from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns

from .io import MEASURES, missingness_summary


def _save(figure, output_dir, filename):
    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        figure.savefig(output_dir / filename, dpi=160, bbox_inches="tight")
    return figure


def plot_missingness(data, output_dir=None):
    summary = missingness_summary(data).pivot(index="measure", columns="wave", values="missing_proportion")
    figure, axis = plt.subplots(figsize=(8, 5))
    sns.heatmap(summary, annot=True, fmt=".1%", cmap="Reds", vmin=0, vmax=1, ax=axis)
    axis.set(title="Missing individual-difference scores", xlabel="Wave", ylabel="Measure")
    figure.tight_layout()
    return _save(figure, output_dir, "missingness.png")


def plot_distributions(data, output_dir=None):
    long = data.melt(id_vars=["wave", "lang"], value_vars=MEASURES, var_name="measure", value_name="score")
    grid = sns.displot(long, x="score", col="measure", hue="wave", col_wrap=3, height=3, facet_kws={"sharex": False, "sharey": False})
    grid.fig.suptitle("Individual-difference score distributions", y=1.02)
    return _save(grid.fig, output_dir, "distributions.png")


def plot_correlations(data, output_dir=None):
    figures = []
    for wave, group in data.groupby("wave", observed=True):
        figure, axis = plt.subplots(figsize=(8, 7))
        sns.heatmap(group[MEASURES].corr(), vmin=-1, vmax=1, center=0, cmap="vlag", annot=True, fmt=".2f", ax=axis)
        axis.set(title=f"Score correlations: Wave {wave}")
        figure.tight_layout()
        figures.append(_save(figure, output_dir, f"correlations_w{wave}.png"))
    return figures


def plot_language_profiles(data, output_dir=None):
    standardized = data.copy()
    for measure in MEASURES:
        standardized[measure] = standardized.groupby("wave", observed=True)[measure].transform(
            lambda values: (values - values.mean()) / values.std(ddof=0)
        )
    long = standardized.melt(id_vars=["wave", "lang"], value_vars=MEASURES, var_name="measure", value_name="z_score")
    summary = long.groupby(["wave", "lang", "measure"], observed=True)["z_score"].mean().reset_index()
    grid = sns.catplot(data=summary, x="z_score", y="measure", col="wave", kind="bar", sharex=True, height=5, aspect=1.1)
    grid.set_axis_labels("Mean within-wave z-score", "Measure")
    return _save(grid.fig, output_dir, "language_profiles.png")
