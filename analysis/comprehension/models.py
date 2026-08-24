"""Clustered regression models for repeated participant-text observations."""

import json

import numpy as np
import statsmodels.api as sm


PRIMARY_FORMULA = (
    "valid_fixation_events ~ comprehension_score + C(wave) + C(lang) + C(text_id)"
)
REVERSE_FORMULA = (
    "comprehension_success ~ fixations_per_word + C(wave) + C(lang) + C(text_id)"
)


def fit_primary(data, formula=PRIMARY_FORMULA):
    model = sm.GEE.from_formula(
        formula,
        groups="participant_id",
        data=data,
        family=sm.families.NegativeBinomial(alpha=1.0),
        cov_struct=sm.cov_struct.Exchangeable(),
        offset=data["log_text_length"],
    )
    return model.fit()


def fit_reverse(data, formula=REVERSE_FORMULA):
    # Represent the two questions as Bernoulli observations instead of relying
    # on freq_weights, which GEE.from_formula does not support consistently.
    expanded = data.loc[data.index.repeat(2)].copy()
    question_number = expanded.groupby(level=0).cumcount()
    expanded["comprehension_success"] = (
        question_number < expanded["comprehension_score"].to_numpy()
    ).astype(int)
    model = sm.GEE.from_formula(
        formula,
        groups="participant_id",
        data=expanded,
        family=sm.families.Binomial(),
        cov_struct=sm.cov_struct.Exchangeable(),
    )
    return model.fit()


def fit_poisson_diagnostic(data):
    model = sm.GEE.from_formula(
        PRIMARY_FORMULA,
        groups="participant_id",
        data=data,
        family=sm.families.Poisson(),
        cov_struct=sm.cov_struct.Exchangeable(),
        offset=data["log_text_length"],
    )
    return model.fit()


def tidy_result(result, model_name, ratio_name="rate_ratio"):
    confidence = result.conf_int()
    table = result.params.rename("estimate").to_frame()
    table["std_error"] = result.bse
    table["z_value"] = result.tvalues
    table["p_value"] = result.pvalues
    table["ci_low"] = confidence[0]
    table["ci_high"] = confidence[1]
    table[ratio_name] = np.exp(table["estimate"])
    table.insert(0, "model", model_name)
    return table.reset_index(names="term")


def model_metadata(result, data, model_name):
    pearson_ratio = float(np.sum(result.resid_pearson**2) / result.df_resid)
    return {
        "model": model_name,
        "n_rows": int(len(data)),
        "n_participants": int(data["participant_id"].nunique()),
        "n_texts": int(data["text_id"].nunique()),
        "aic": float(result.aic) if np.isfinite(result.aic) else None,
        "pearson_dispersion_ratio": pearson_ratio,
        "converged": bool(getattr(result, "converged", True)),
    }


def save_result(result, data, model_name, output_dir, ratio_name="rate_ratio"):
    output_dir.mkdir(parents=True, exist_ok=True)
    tidy_result(result, model_name, ratio_name=ratio_name).to_csv(
        output_dir / f"{model_name}_coefficients.csv", index=False
    )
    (output_dir / f"{model_name}_summary.txt").write_text(result.summary().as_text())
    metadata = model_metadata(result, data, model_name)
    (output_dir / f"{model_name}_metadata.json").write_text(json.dumps(metadata, indent=2))
    return metadata
