"""Plots for the integrated individual-differences analysis."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def _save(figure, output_dir, filename):
    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        figure.savefig(output_dir / filename, dpi=160, bbox_inches="tight")
    return figure


def plot_skill_quartiles(data, output_dir=None, skill="language_skill_composite"):
    plot_data = data.dropna(subset=[skill]).copy()
    plot_data["skill_group"] = plot_data.groupby("wave", observed=True)[skill].transform(
        lambda values: values.rank(pct=True, method="first").map(
            lambda value: "low" if value <= 1 / 3 else "high" if value > 2 / 3 else "middle"
        )
    )
    figure, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
    for axis, (wave, group) in zip(axes, plot_data.groupby("wave", observed=True)):
        sns.pointplot(data=group, x="comprehension_score", y="fixations_per_word", hue="skill_group", errorbar=("ci", 95), ax=axis)
        axis.set_title(f"Wave {wave}")
        axis.set_xlabel("Comprehension score")
        axis.set_ylabel("Fixations per word")
    figure.tight_layout()
    return _save(figure, output_dir, "fixations_by_skill_group.png")


def plot_interaction_means(data, output_dir=None, skill="language_skill_composite"):
    plot_data = data.dropna(subset=[skill]).copy()
    plot_data["skill_group"] = plot_data.groupby("wave", observed=True)[skill].transform(
        lambda values: pd.qcut(values.rank(method="first"), 3, labels=["low", "middle", "high"])
    )
    summary = plot_data.groupby(["wave", "skill_group", "comprehension_score"], observed=True)["fixations_per_word"].mean().reset_index()
    figure, axes = plt.subplots(2, 1, figsize=(9, 8), sharex=True, sharey=True)
    for axis, (wave, group) in zip(axes, summary.groupby("wave", observed=True)):
        sns.lineplot(data=group, x="comprehension_score", y="fixations_per_word", hue="skill_group", marker="o", ax=axis)
        axis.set_title(f"Wave {wave}: observed means by skill group")
        axis.set_ylabel("Mean fixations per word")
    axes[-1].set_xlabel("Comprehension score")
    figure.tight_layout()
    return _save(figure, output_dir, "interaction_means_vertical.png")
