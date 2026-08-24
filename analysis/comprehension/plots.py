"""Reusable plots for comprehension/fixation exploration and diagnostics."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def _save(figure, output_dir, filename):
    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        figure.savefig(output_dir / filename, dpi=160, bbox_inches="tight")
    return figure


def plot_distributions(data, output_dir=None):
    figure, axes = plt.subplots(1, 2, figsize=(12, 4))
    single_wave = data["wave"].nunique() == 1
    hue = None if single_wave else "wave"
    sns.histplot(data=data, x="fixations_per_word", hue=hue, stat="density", common_norm=False, alpha=0.35, ax=axes[0])
    sns.histplot(data=data, x="comprehension_score", discrete=True, hue=hue, stat="density", common_norm=False, multiple="dodge", ax=axes[1])
    axes[0].set(xlabel="Valid fixations per word", ylabel="Density")
    axes[1].set(xlabel="Comprehension score (0-2)", ylabel="Density")
    figure.tight_layout()
    return _save(figure, output_dir, "distributions.png")


def plot_jittered_association(data, output_dir=None):
    figure, axis = plt.subplots(figsize=(8, 5))
    single_wave = data["wave"].nunique() == 1
    hue = None if single_wave else "wave"
    sns.stripplot(data=data, x="comprehension_score", y="fixations_per_word", hue=hue, jitter=0.22, alpha=0.28, dodge=not single_wave, ax=axis)
    sns.pointplot(data=data, x="comprehension_score", y="fixations_per_word", hue=hue, errorbar=("ci", 95), dodge=0.42 if not single_wave else False, markers="D", linestyles="none", ax=axis)
    if not single_wave:
        handles, labels = axis.get_legend_handles_labels()
        axis.legend(handles[:2], labels[:2], title="Wave")
    axis.set(xlabel="Comprehension score (0-2)", ylabel="Valid fixations per word")
    figure.tight_layout()
    return _save(figure, output_dir, "jittered_association.png")


def plot_text_facets(data, output_dir=None):
    hue = None if data["wave"].nunique() == 1 else "wave"
    grid = sns.lmplot(
        data=data,
        x="comprehension_proportion",
        y="fixations_per_word",
        col="text_id",
        col_wrap=4,
        hue=hue,
        scatter_kws={"alpha": 0.22, "s": 14},
        line_kws={"linewidth": 1.5},
        height=3,
        aspect=1.1,
        ci=95,
    )
    grid.set_axis_labels("Comprehension proportion", "Fixations per word")
    grid.fig.suptitle("Comprehension and fixation rate by text", y=1.02)
    return _save(grid.fig, output_dir, "association_by_text.png")


def plot_group_estimates(data, output_dir=None):
    grouped = data.groupby(["wave", "comprehension_score"], observed=True)["fixations_per_word"]
    summary = grouped.agg(mean="mean", median="median", count="size", sd="std").reset_index()
    summary["se"] = summary["sd"] / np.sqrt(summary["count"])
    summary["ci_low"] = summary["mean"] - 1.96 * summary["se"]
    summary["ci_high"] = summary["mean"] + 1.96 * summary["se"]
    figure, axis = plt.subplots(figsize=(8, 5))
    single_wave = summary["wave"].nunique() == 1
    hue = None if single_wave else "wave"
    sns.pointplot(data=summary, x="comprehension_score", y="mean", hue=hue, errorbar=None, dodge=0.35 if not single_wave else False, ax=axis)
    for wave_index, wave in enumerate(sorted(summary["wave"].unique())):
        current = summary[summary["wave"] == wave]
        x = current["comprehension_score"] + (wave_index - 0.5) * 0.18 if not single_wave else current["comprehension_score"]
        axis.errorbar(x, current["mean"], yerr=[current["mean"] - current["ci_low"], current["ci_high"] - current["mean"]], fmt="none", color="black", capsize=3, alpha=0.7)
    axis.set(xlabel="Comprehension score (0-2)", ylabel="Mean fixations per word")
    figure.tight_layout()
    return _save(figure, output_dir, "group_estimates.png")


def plot_language_text_heatmap(data, output_dir=None):
    table = data.pivot_table(index="lang", columns="text_id", values="fixations_per_word", aggfunc="mean")
    figure, axis = plt.subplots(figsize=(11, 6))
    sns.heatmap(table, cmap="mako", annot=False, ax=axis)
    axis.set(xlabel="Text ID", ylabel="Language", title="Mean fixation rate by language and text")
    figure.tight_layout()
    return _save(figure, output_dir, "language_text_heatmap.png")


def plot_participant_association(data, output_dir=None):
    participant = data.groupby("participant_id", as_index=False).agg(
        comprehension=("comprehension_proportion", "mean"),
        fixation_rate=("fixations_per_word", "mean"),
        wave=("wave", "first"),
    )
    figure, axis = plt.subplots(figsize=(8, 5))
    sns.regplot(data=participant, x="comprehension", y="fixation_rate", scatter_kws={"alpha": 0.28}, line_kws={"color": "black"}, ax=axis)
    axis.set(xlabel="Participant mean comprehension", ylabel="Participant mean fixations per word")
    figure.tight_layout()
    return _save(figure, output_dir, "participant_association.png")


def plot_model_diagnostics(result, output_dir=None, filename="primary_model_diagnostics.png"):
    fitted = np.asarray(result.fittedvalues)
    residuals = np.asarray(result.resid_pearson)
    figure, axes = plt.subplots(1, 2, figsize=(12, 4))
    sns.scatterplot(x=fitted, y=residuals, alpha=0.25, s=15, ax=axes[0])
    axes[0].axhline(0, color="black", linestyle="--")
    axes[0].set(xlabel="Fitted values", ylabel="Pearson residuals")
    sns.histplot(residuals, bins=40, ax=axes[1])
    axes[1].set(xlabel="Pearson residual", ylabel="Count")
    figure.tight_layout()
    return _save(figure, output_dir, filename)


def plot_model_effects(results, term, output_dir=None, filename="model_effects.png", xlabel="Exponentiated effect (95% CI)"):
    rows = []
    for name, result in results.items():
        if term not in result.params:
            continue
        low, high = result.conf_int().loc[term]
        rows.append({"model": name, "effect": np.exp(result.params[term]), "low": np.exp(low), "high": np.exp(high)})
    summary = pd.DataFrame(rows)
    figure, axis = plt.subplots(figsize=(8, 4))
    axis.errorbar(summary["effect"], summary["model"], xerr=[summary["effect"] - summary["low"], summary["high"] - summary["effect"]], fmt="o", capsize=4)
    axis.axvline(1, color="black", linestyle="--")
    axis.set(xlabel=xlabel, ylabel="Model")
    figure.tight_layout()
    return _save(figure, output_dir, filename)


def plot_model_coefficients(results, output_dir=None):
    return plot_model_effects(
        results,
        "comprehension_score",
        output_dir,
        filename="model_coefficients.png",
        xlabel="Rate ratio for comprehension score (95% CI)",
    )


def save_descriptive_plots(data, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    figures = [
        plot_jittered_association(data, output_dir),
        plot_distributions(data, output_dir),
        plot_text_facets(data, output_dir),
        plot_group_estimates(data, output_dir),
        plot_language_text_heatmap(data, output_dir),
        plot_participant_association(data, output_dir),
    ]
    for figure in figures:
        plt.close(figure)
